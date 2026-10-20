"""Serial protocol of the Gira TK gateway 1290 00 (programming interface).

Reconstructed from ``frm_Kommunikation`` of the original commissioning software
and verified against firmware 1.26:

* 19200 baud, 8N1, no handshake.
* A command is one letter + ``CR`` (``"u\\r"`` etc.). The firmware collects
  characters up to the CR, converts upper to lower case and evaluates the
  first character. The bootloader understands ``s`` and ``r`` without CR.
* Data transfers in both directions use XMODEM (128-byte blocks, 8-bit sum
  checksum, padding with 0x1A).
* Text replies (version, call button, bus log) end with ``CR LF``.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Callable, Iterator, Protocol

from .i18n import _

BAUDRATE = 19200

SOH = 0x01
EOT = 0x04
ACK = 0x06
NAK = 0x15
CAN = 0x18
SUB = 0x1A
BLOCK_SIZE = 128

CMD_END = b"\r"
CMD_FIRMWARE = b"s"  # transfer firmware (.tsk)
CMD_BUSTREIBER = b"p"  # transfer bus driver firmware (.hex, PIC) – erases the PIC immediately!
CMD_READ_IMAGE = b"U"  # read configuration + phonebook
CMD_WRITE_IMAGE = b"D"  # write configuration + phonebook
CMD_VERSION = b"i"  # read firmware version
CMD_BOOTLOADER_RESET = b"r"  # bootloader only, without CR
CMD_RUFTASTE = b"z"  # + door station (1 digit) + phonebook index (2 digits)
CMD_LOG_ON = b"t"
CMD_LOG_OFF = b"n"

Progress = Callable[[int, int], None]


class Port(Protocol):
    """Minimal interface fulfilled by ``serial.Serial``."""

    timeout: float | None

    def read(self, size: int = 1) -> bytes: ...
    def write(self, data: bytes) -> int | None: ...
    def reset_input_buffer(self) -> None: ...
    def close(self) -> None: ...


class GatewayError(Exception):
    pass


class TransferTimeout(GatewayError):
    pass


class TransferAborted(GatewayError):
    pass


class TransferError(GatewayError):
    pass


_LOG_START = re.compile(r"(?:^|\s)[SET]: ")


def strip_log(text: str) -> str:
    """Remove bus log output (``S: …``, ``E: …``, ``T: …``) from an answer line."""
    m = _LOG_START.search(text)
    return (text[:m.start()] if m else text).strip()


def checksum(block: bytes) -> int:
    """XMODEM sum checksum (original function ``csum``)."""
    return sum(block) & 0xFF


def build_block(number: int, payload: bytes) -> bytes:
    """Build an XMODEM block (original function ``BlockSenden``)."""
    data = payload.ljust(BLOCK_SIZE, bytes([SUB]))
    n = number & 0xFF
    return bytes([SOH, n, 0xFF - n]) + data + bytes([checksum(data)])


@dataclass
class VersionInfo:
    text: str

    @property
    def bootloader_only(self) -> bool:
        return "Bootlader" in self.text

    @property
    def has_bustreiber(self) -> bool:
        return "PIC" in self.text

    @property
    def koppler(self) -> str | None:
        """Gateway firmware version, e.g. ``"01.26"``."""
        m = re.search(r"Version\s+(\S+)", self.text)
        return m.group(1) if m else None

    @property
    def pic(self) -> str | None:
        """Bus driver (PIC) version, e.g. ``"0101"``."""
        m = re.search(r"PIC Release\s+(\S+)", self.text)
        return m.group(1) if m else None

    def as_dict(self) -> dict:
        return {
            "text": self.text,
            "koppler": self.koppler,
            "pic": self.pic,
            "bootloader_only": self.bootloader_only,
            "has_bustreiber": self.has_bustreiber,
        }


def open_serial(port: str, baudrate: int = BAUDRATE) -> Port:
    import serial  # pyserial

    return serial.Serial(
        port,
        baudrate=baudrate,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=0.1,
    )


class Gateway:
    def __init__(
        self,
        port: Port,
        *,
        timeout: float = 60.0,
        line_timeout: float = 10.0,
        retries: int = 10,
        log: Callable[[str], None] | None = None,
    ) -> None:
        self.port = port
        self.timeout = timeout
        self.line_timeout = line_timeout
        self.retries = retries
        self._log = log or (lambda msg: None)
        if self.port.timeout is None or self.port.timeout > 0.5:
            self.port.timeout = 0.1

    @classmethod
    def open(cls, device: str, **kw) -> "Gateway":
        return cls(open_serial(device), **kw)

    def close(self) -> None:
        self.port.close()

    def __enter__(self) -> "Gateway":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # ------------------------------------------------------------------ basics

    def _read_byte(self, deadline: float) -> int | None:
        while time.monotonic() < deadline:
            b = self.port.read(1)
            if b:
                return b[0]
        return None

    def _read_exact(self, n: int, deadline: float) -> bytes:
        buf = b""
        while len(buf) < n and time.monotonic() < deadline:
            buf += self.port.read(n - len(buf))
        return buf

    def _read_line(self, timeout: float, *, partial_ok: bool = False) -> str:
        deadline = time.monotonic() + timeout
        buf = b""
        while not buf.endswith(b"\r\n"):
            b = self.port.read(1)
            if b:
                buf += b
            elif time.monotonic() >= deadline:
                if partial_ok and buf:
                    return buf.decode("latin-1")
                raise TransferTimeout(_("no response (received so far: {buf!r})", buf=buf))
        return buf[:-2].decode("latin-1")

    def quiet(self, settle: float = 0.3, limit: float = 2.0) -> bool:
        """Switch the bus log off and discard pending output.

        The log flag lives in the gateway's RAM: if the host restarts while
        logging (container reset, unplugged PC), the gateway keeps sending log
        lines that then get mixed into the next answers – e.g. ``i`` looks as if
        no bus driver were installed. ``n`` is harmless otherwise. Returns True
        if the gateway was still sending something.
        """
        self.send_command(CMD_LOG_OFF)
        noisy = False
        deadline = time.monotonic() + limit
        quiet_since = time.monotonic()
        while time.monotonic() < deadline and time.monotonic() - quiet_since < settle:
            if self.port.read(64):
                noisy = True
                quiet_since = time.monotonic()
        self.port.reset_input_buffer()
        if noisy:
            self._log("gateway was still sending (stale log mode) – switched off")
        return noisy

    def send_command(self, cmd: bytes, *, terminate: bool = True) -> None:
        self.port.reset_input_buffer()
        self.port.write(cmd + (CMD_END if terminate else b""))
        self._log(f"command {cmd.decode('latin-1')!r} sent")

    def _abort(self) -> None:
        self.port.write(bytes([CAN]) * 3)

    # ---------------------------------------------------------------- XMODEM

    def _xmodem_send(self, data: bytes, progress: Progress | None) -> None:
        if not data:
            raise ValueError(_("no data to transfer"))
        deadline = time.monotonic() + self.timeout
        while True:
            b = self._read_byte(deadline)
            if b is None:
                raise TransferTimeout(_("Gateway does not request data (no NAK received)"))
            if b == NAK:
                break
            if b == CAN:
                raise TransferAborted(_("Transfer aborted by the gateway"))

        blocks = [data[i:i + BLOCK_SIZE] for i in range(0, len(data), BLOCK_SIZE)]
        for idx, payload in enumerate(blocks):
            packet = build_block(idx + 1, payload)
            for _attempt in range(self.retries):
                self.port.write(packet)
                b = self._read_byte(time.monotonic() + self.timeout)
                if b == ACK:
                    break
                if b == CAN:
                    raise TransferAborted(_("Transfer aborted by the gateway"))
                if b is None:
                    raise TransferTimeout(_("no acknowledgement for block {n}", n=idx + 1))
                self._log(f"block {idx + 1} repeated (reply 0x{b:02X})")
            else:
                self._abort()
                raise TransferError(_("block {n} not acknowledged after {tries} attempts", n=idx + 1, tries=self.retries))
            if progress:
                progress(min((idx + 1) * BLOCK_SIZE, len(data)), len(data))

        for _attempt in range(self.retries):
            self.port.write(bytes([EOT]))
            b = self._read_byte(time.monotonic() + self.timeout)
            if b == ACK:
                return
            if b == CAN:
                raise TransferAborted(_("Transfer aborted by the gateway"))
            if b is None:
                raise TransferTimeout(_("no acknowledgement for end of transfer"))
        raise TransferError(_("end of transfer not acknowledged"))

    def _xmodem_receive(
        self, expected_size: int | None, progress: Progress | None, start_attempts: int = 10
    ) -> bytes:
        # start reception: NAK once per second (original: EmpfangenInitSenden)
        first = None
        for _attempt in range(start_attempts):
            self.port.write(bytes([NAK]))
            first = self._read_byte(time.monotonic() + 1.0)
            if first is not None:
                break
        if first is None:
            raise TransferTimeout(_("Gateway does not send any data"))

        data = bytearray()
        expected = 1
        errors = 0
        b: int | None = first
        while True:
            if b is None:
                raise TransferTimeout(_("Timeout while receiving block {n}", n=expected))
            if b == EOT:
                self.port.write(bytes([ACK]))
                break
            if b == CAN:
                raise TransferAborted(_("Transfer aborted by the gateway"))
            if b == SOH:
                rest = self._read_exact(BLOCK_SIZE + 3, time.monotonic() + self.line_timeout)
                ok = (
                    len(rest) == BLOCK_SIZE + 3
                    and rest[0] == 0xFF - rest[1]
                    and checksum(rest[2:-1]) == rest[-1]
                )
                if ok and rest[0] == expected & 0xFF:
                    data += rest[2:-1]
                    expected += 1
                    errors = 0
                    self.port.write(bytes([ACK]))
                    if progress and expected_size:
                        progress(min(len(data), expected_size), expected_size)
                elif ok and rest[0] == (expected - 1) & 0xFF:
                    self.port.write(bytes([ACK]))  # repetition of the previous block
                else:
                    errors += 1
                    self._log(f"bad block {expected} (error {errors})")
                    if errors >= 3:
                        self._abort()
                        raise TransferError(_("Transfer aborted due to transmission errors"))
                    self.port.reset_input_buffer()
                    self.port.write(bytes([NAK]))
            b = self._read_byte(time.monotonic() + self.timeout)

        if expected_size is not None and len(data) < expected_size:
            raise TransferError(_("only {n} of {size} bytes received", n=len(data), size=expected_size))
        return bytes(data[:expected_size] if expected_size else data)

    # ------------------------------------------------------- device functions

    def read_version(self, timeout: float = 3.0) -> VersionInfo:
        """Read the firmware version.

        The firmware immediately sends ``"Gira TK Koppler Version 01.26 "``
        (without line end), then queries the bus driver PIC via bus telegram
        0x90 and only appends ``"PIC Release NNNN\\r\\n"`` on its reply. Without
        a bus driver no CRLF ever arrives; the partial text is the answer then.
        """
        self.send_command(CMD_VERSION)
        deadline = time.monotonic() + timeout
        parts: list[str] = []
        buf = b""
        while time.monotonic() < deadline:
            b = self.port.read(1)
            if not b:
                continue
            buf += b
            if buf.endswith(b"\r\n"):
                raw = buf[:-2].decode("latin-1")
                buf = b""
                text = strip_log(raw)
                if text:
                    parts.append(text)
                # without log output the answer is one line; with log output glued
                # to it ("… 01.26 S: 90 …") "PIC Release" follows on its own line
                if text and (text == raw.strip() or "PIC" in text):
                    break
        else:
            if buf:
                parts.append(strip_log(buf.decode("latin-1")))
        text = " ".join(p for p in parts if p)
        if not text:
            raise TransferTimeout(_("no response (received so far: {buf!r})", buf=buf))
        return VersionInfo(text)

    def read_image(self, progress: Progress | None = None) -> bytes:
        from .image import IMAGE_SIZE

        self.send_command(CMD_READ_IMAGE)
        return self._xmodem_receive(IMAGE_SIZE, progress)

    def write_image(self, data: bytes, progress: Progress | None = None) -> None:
        from .image import IMAGE_SIZE

        if len(data) != IMAGE_SIZE:
            raise ValueError(_("Image must be {size} bytes, not {n}", size=IMAGE_SIZE, n=len(data)))
        self.send_command(CMD_WRITE_IMAGE)
        self._xmodem_send(data, progress)

    def upload_firmware(
        self, data: bytes, progress: Progress | None = None, *, bootloader_only: bool | None = None
    ) -> None:
        """Transfer firmware (.tsk). If only the bootloader runs, ``s`` is sent without CR."""
        if bootloader_only is None:
            try:
                bootloader_only = self.read_version().bootloader_only
            except TransferTimeout:
                bootloader_only = False
        self.send_command(CMD_FIRMWARE, terminate=not bootloader_only)
        self._xmodem_send(data, progress)

    def upload_bustreiber(self, data: bytes, progress: Progress | None = None) -> None:
        """Transfer bus driver firmware (.hex); the file is sent unchanged."""
        self.send_command(CMD_BUSTREIBER)
        self._xmodem_send(data, progress)

    def reset_bootloader(self) -> None:
        """Restart the bootloader (original: key ``r`` on the "Read" button)."""
        self.send_command(CMD_BOOTLOADER_RESET, terminate=False)

    def fetch_ruftaste(self, index: int, tuerstation: int, timeout: float = 8.0) -> bytes:
        """Assign a call button to phonebook entry ``index`` and fetch its button code.

        Equivalent to the DTMF code ``*2*station*index#``. The gateway sends bus
        telegram ``05 <index-1>`` (observed: ``z105`` → ``S: 05 04 …``) and then
        accepts any door call (code 0x11) within 2–3 s – a normal ring as well.
        The door station number is only stored locally. On success:
        ``"XX XX XX XX XX \\r\\n"`` (17 characters, bus address); the original
        software extends the 5 bytes with ``00-00-00`` to 8 bytes. Without a
        reply the gateway reports nothing on the serial line – hence the short
        timeout.
        """
        if not 1 <= tuerstation <= 9:
            raise ValueError(_("Please assign a valid door station number (1-9)"))
        if not 1 <= index <= 50:
            raise ValueError(_("Phonebook index must be between 1 and 50"))
        self.send_command(CMD_RUFTASTE + f"{tuerstation}{index:02d}".encode())
        deadline = time.monotonic() + timeout
        try:
            while True:  # skip log lines ("S: 05 …") if logging is on
                line = self._read_line(max(deadline - time.monotonic(), 0.01))
                if strip_log(line):
                    break
        except TransferTimeout:
            raise TransferTimeout(_(
                "No call information received. Is the control unit in programming mode, was the call button "
                "at the door station pressed and is the bus connected?"
            )) from None
        if len(line) != 15:
            raise TransferError(_("Call information invalid: {line!r}", line=line))
        try:
            code = bytes(int(line[i * 3:i * 3 + 2], 16) for i in range(5))
        except ValueError:
            raise TransferError(_("Call information invalid: {line!r}", line=line)) from None
        return code + bytes(3)

    def log_on(self) -> None:
        self.send_command(CMD_LOG_ON)

    def log_off(self) -> None:
        self.send_command(CMD_LOG_OFF)

    def iter_log(self, stop: Callable[[], bool] = lambda: False) -> Iterator[str]:
        """Yield bus log lines until ``stop()`` is true."""
        buf = b""
        while not stop():
            chunk = self.port.read(64)
            if not chunk:
                continue
            buf += chunk
            while b"\r\n" in buf:
                line, buf = buf.split(b"\r\n", 1)
                if line:
                    yield line.decode("latin-1")
