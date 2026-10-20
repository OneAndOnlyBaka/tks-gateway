"""Plain-text decoding of the gateway's bus log lines (original: Timer10ms, state 1).

Line format per firmware 1.26 (output at 0x0BB1, 0x0C65, 0x14F4):

* ``S: `` / ``E: `` + 9 telegram bytes as ``"XX "``, then CR LF
  (pos. 4-5 telegram code, pos. 7-14 bus address, pos. 16-17 data byte; 1-based)
* ``T: DIAL  `` / ``T: LOCAL `` + index + variant + AB flag (each ``"XX "``)
  + ``"- "`` + number, then CR LF
"""

from __future__ import annotations

from .i18n import _

SENT = {  # code -> text (followed by the address)
    "12": "internal call to ",
    "21": "door conversation start with ",
    "22": "internal conversation start with ",
    "20": "end of conversation with ",
    "31": "open door at ",
}
RECEIVED = {
    "20": "end of conversation from ",
    "11": "door call from ",
    "12": "internal call from ",
    "21": "door call answered by ",
    "22": "internal call answered by ",
}
RECEIVED_WITHOUT_ADDRESS = {
    "01": "system programming ON",
    "00": "system programming OFF",
    "03": "actuator programming ON",
    "02": "actuator programming OFF",
}


def _mid(s: str, start: int, length: int) -> str:
    return s[start - 1:start - 1 + length]


def decode(line: str) -> str:
    kind = line[:1]
    code = _mid(line, 4, 2)
    addr = _mid(line, 7, 8)
    data = _mid(line, 16, 2)

    if kind == "S":
        prefix = _("Gateway sends: ")
        if code in SENT:
            return prefix + _(SENT[code]) + addr
        if code == "42":
            return prefix + _("switching function ON at " if data == "FF" else "switching function OFF at ") + addr
        if code == "90":  # firmware 0x0E31: reply arrives as "PIC Release …"
            return prefix + _("bus driver version request (PIC)")
        if code == "05":  # firmware 0x0F39: data byte = phonebook index - 1
            try:
                return prefix + _("request call button for entry {n}", n=int(_mid(line, 7, 2), 16) + 1)
            except ValueError:
                return prefix + _("request call button")
        if code == "81":
            return prefix + _("test device mode ON")
        if code == "82":
            return prefix + _("test device mode OFF")
        on = _mid(line, 7, 2) == "FF"
        if code == "A0":
            return prefix + _("audio input TLN ON" if on else "audio input TLN OFF")
        if code == "A1":
            return prefix + _("bus transmitter ON" if on else "bus transmitter OFF")
        if code == "A2":
            return prefix + _("system reset")
        if code == "A3":
            return prefix + _("incoming call is known in the phonebook ") + addr
        return prefix + line

    if kind == "E":
        prefix = _("Gateway receives: ")
        if code in RECEIVED:
            text = prefix + _(RECEIVED[code]) + addr
            if data.strip():
                text += _(" sub-address ") + data
            return text
        if code in RECEIVED_WITHOUT_ADDRESS:
            return prefix + _(RECEIVED_WITHOUT_ADDRESS[code])
        return prefix + line

    if kind == "T":
        text = _("Gateway calls: ")
        index = _mid(line, 10, 2)
        if index == "00":
            text += _("via the master redirect ")
        else:
            try:
                text += _("from phonebook index {n} ", n=int(index, 16))
            except ValueError:
                pass
            variante = _mid(line, 13, 2)
            if variante == "00":
                text += _("with variant 1 active ")
            elif variante == "01":
                text += _("with variant 2 active ")
        if "LOCAL" in line:
            text += _("the local subscriber")
        elif "DIAL" in line:
            text += _("an external subscriber")
            if " - " in line:
                text += _(" with number: {nr}", nr=line.split(" - ", 1)[1].strip())
        ab = _mid(line, 16, 2)
        if ab == "00":
            text += _(" with answering machine function inactive")
        elif ab == "01":
            text += _(" with answering machine function active")
        return text

    return line


def telegram(line: str) -> tuple[str, str, list[str]] | None:
    """``"E: 11 1A 2B …"`` → ``("E", "11", ["1A", "2B", …])``; otherwise ``None``."""
    if line[:3] not in ("S: ", "E: "):
        return None
    parts = line[3:].split()
    if not parts:
        return None
    return line[0], parts[0], parts[1:]


def tuerruf_adresse(line: str) -> bytes | None:
    """Bus address of a received door call (``E: 11``) as 8-byte button code.

    When learning, the firmware stores exactly the 5 bytes after the code
    (0x0CAD); the original software appends ``00 00 00``.
    """
    t = telegram(line)
    if not t or t[0] != "E" or t[1] != "11" or len(t[2]) < 5:
        return None
    try:
        return bytes(int(x, 16) for x in t[2][:5]) + bytes(3)
    except ValueError:
        return None


def format_line(line: str) -> str:
    text = decode(line)
    return line if text == line else f"{line}  ->  {text}"
