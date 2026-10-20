"""Simulated TK gateway (device side of the protocol) for tests and demos.

``SimulatedPort`` fulfils the same interface as ``serial.Serial``; everything
the host writes is processed by the simulated device immediately.
"""

from __future__ import annotations

import threading
from collections import deque

from .image import IMAGE_SIZE, GatewayImage
from .protocol import ACK, BLOCK_SIZE, CAN, EOT, NAK, SOH, build_block, checksum


class SimulatedPort:
    def __init__(
        self,
        image: bytes | None = None,
        *,
        version: str = "Gira TK Koppler Version 01.26 PIC Release 0101",
        ruftaste: str = "1A 2B 3C 4D 5E ",
        corrupt_blocks: set[int] | None = None,
    ) -> None:
        self.timeout: float | None = 0.1
        self.image = bytearray(image if image is not None else GatewayImage.factory_defaults().to_bytes())
        self.version = version
        self.ruftaste = ruftaste
        self.firmware = b""
        self.bustreiber = b""
        self.commands: list[str] = []
        self.corrupt_blocks = set(corrupt_blocks or ())  # corrupt once when sending
        self._out: deque[int] = deque()
        self._cond = threading.Condition()
        self._mode = "idle"
        self._line = ""
        self._rx = bytearray()
        self._target = ""
        self._tx_blocks: list[bytes] = []
        self._tx_idx = 0
        self.logging = False

    # -------------------------------------------------- Port-Schnittstelle

    def read(self, size: int = 1) -> bytes:
        with self._cond:
            if not self._out:
                self._cond.wait(self.timeout)
            n = min(size, len(self._out))
            return bytes(self._out.popleft() for _ in range(n))

    def write(self, data: bytes) -> int:
        with self._cond:
            for b in data:
                self._feed(b)
            self._cond.notify_all()
        return len(data)

    def reset_input_buffer(self) -> None:
        with self._cond:
            self._out.clear()

    def close(self) -> None:
        pass

    def emit_log(self, line: str) -> None:
        with self._cond:
            if self.logging:
                self._out.extend((line + "\r\n").encode("latin-1"))
                self._cond.notify_all()

    # ------------------------------------------------------- device side

    def _send(self, data: bytes) -> None:
        self._out.extend(data)

    def _feed(self, b: int) -> None:
        mode = self._mode
        if mode == "idle":
            if "Bootlader" in self.version and b in (ord("s"), ord("r")):
                self.commands.append(chr(b))  # Bootloader: ein Zeichen ohne CR
                if b == ord("s"):
                    self._start_receive("firmware")
                return
            # Firmware: Zeilenpuffer bis CR, A-Z -> a-z, Zeichen < '0' verwerfen
            if ord("A") <= b <= ord("Z"):
                b |= 0x20
            if b == 0x0D:
                line, self._line = self._line, ""
                if line:
                    self._command(line)
            elif b >= ord("0"):
                self._line += chr(b)
        elif mode == "rx_wait_block":
            if b == SOH:
                self._rx = bytearray([b])
                self._mode = "rx_block"
            elif b == EOT:
                self._send(bytes([ACK]))
                self._finish_receive()
            elif b == CAN:
                self._mode = "idle"
        elif mode == "rx_block":
            self._rx.append(b)
            if len(self._rx) == BLOCK_SIZE + 4:
                p = self._rx
                ok = p[2] == 0xFF - p[1] and checksum(p[3:-1]) == p[-1]
                expected = (len(self._data) // BLOCK_SIZE + 1) & 0xFF
                if ok and p[1] == expected:
                    self._data += p[3:-1]
                    self._send(bytes([ACK]))
                elif ok and p[1] == (expected - 1) & 0xFF:
                    self._send(bytes([ACK]))
                else:
                    self._send(bytes([NAK]))
                self._mode = "rx_wait_block"
        elif mode == "tx_wait_start":
            if b == NAK:
                self._mode = "tx"
                self._send_block()
        elif mode == "tx":
            if b == ACK:
                self._tx_idx += 1
                self._send_block()
            elif b == NAK:
                self._send_block()
            elif b == CAN:
                self._mode = "idle"
        elif mode == "tx_eot":
            if b == ACK:
                self._mode = "idle"
            elif b == NAK:
                self._send(bytes([EOT]))

    def _command(self, line: str) -> None:
        self._mode = "idle"
        self.commands.append(line)
        c = line[0]
        if c == "i":
            # as firmware 1.26: version text without CRLF, then bus query 0x90 to the
            # PIC (visible as "S: 90 …" when logging), whose reply "PIC Release …" + CRLF
            if "PIC" in self.version:
                koppler, pic = self.version.split("PIC", 1)
                out = koppler
                if self.logging:
                    out += "S: 90 00 00 00 00 00 00 00 00 \r\n"
                out += "PIC" + pic + "\r\n"
            else:
                out = self.version
            self._send(out.encode("latin-1"))
        elif c == "u":
            self._tx_blocks = [
                bytes(self.image[i:i + BLOCK_SIZE]) for i in range(0, IMAGE_SIZE, BLOCK_SIZE)
            ]
            self._tx_idx = 0
            self._mode = "tx_wait_start"
        elif c == "d":
            self._start_receive("image")
        elif c == "s":
            self._start_receive("firmware")
        elif c == "p":
            self._start_receive("bustreiber")
        elif c == "z":
            # z<door station><index>, index 1..50 (firmware: CJNE/SUBB #33h)
            if len(line) >= 3 and line[1].isdigit() and line[2:].isdigit() and 1 <= int(line[2:]) <= 50:
                if self.logging:  # bus telegram 05 <index-1>, as observed on the device
                    self._send(f"S: 05 {int(line[2:]) - 1:02X} 00 00 00 00 00 00 00 \r\n".encode())
                self._send((self.ruftaste + "\r\n").encode())
        elif c == "t":
            self.logging = True
        elif c == "n":
            self.logging = False

    def _start_receive(self, target: str) -> None:
        self._target = target
        self._data = bytearray()
        self._mode = "rx_wait_block"
        self._send(bytes([NAK]))

    def _finish_receive(self) -> None:
        self._mode = "idle"
        data = bytes(self._data)
        if self._target == "image":
            self.image[:] = data[:IMAGE_SIZE]
        elif self._target == "firmware":
            self.firmware = data
        elif self._target == "bustreiber":
            self.bustreiber = data

    def _send_block(self) -> None:
        if self._tx_idx >= len(self._tx_blocks):
            self._mode = "tx_eot"
            self._send(bytes([EOT]))
            return
        n = self._tx_idx + 1
        packet = bytearray(build_block(n, self._tx_blocks[self._tx_idx]))
        if n in self.corrupt_blocks:
            self.corrupt_blocks.discard(n)
            packet[-1] ^= 0xFF
        self._send(bytes(packet))
