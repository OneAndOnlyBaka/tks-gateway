"""Memory image of the Gira TK gateway 1290 00.

The gateway sends (command ``u``) or expects (command ``d``) a 6144-byte image
(48 XMODEM blocks of 128 bytes). Layout, reverse-engineered from the original
commissioning software V1.01 (TK_Gateway.exe) and firmware 1.26:

====================  =====================================================
Offset                Content
====================  =====================================================
0x0000 - 0x00FF       configuration (see :class:`Config`)
0x0100 - 0x0D7F       phonebook, 50 entries of 64 bytes
0x0D80 - 0x0FFF       unused (written as 0x00)
0x1000 - 0x13E7       entry names, 50 x 20 bytes
0x13E8 - 0x17FF       unused (written as 0x00)
====================  =====================================================

All text fields are ASCII padded with 0x00. When reading, a field ends at the
first 0x00 or 0xFF (numbers/times also at ``'A'``), exactly like the original
functions ``Cut0``/``Cut0A``.

Unknown bytes are preserved when writing back, as the original software does.
Field names (``anschlussart``, ``tuerstation`` …) are kept in German because
they are used in JSON files and the web API.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum

from .i18n import _

IMAGE_SIZE = 0x1800
CONFIG_SIZE = 0x100
PB_OFFSET = 0x100
PB_ENTRY_SIZE = 64
PB_ENTRIES = 50
NAME_OFFSET = 0x1000
NAME_SIZE = 20
NUMBER_SIZE = 25  # field size in the image
NUMBER_MAX = 24  # max. length per software manual (remaining byte = terminator)
TASTERCODE_SIZE = 8


class Anschlussart(IntEnum):
    """Connection type."""

    AMT = 0  # direct analogue line ("Amtsanschluss")
    NEBENSTELLE = 1  # extension of a PBX ("Nebenstellenanschluss")


class Masterumleitung(IntEnum):
    """Master redirect mode."""

    AUS = 0  # off
    VERZOEGERT = 1  # delayed: after the ring time to the master redirect number
    SOFORT = 2  # immediately to the master redirect number


def cut0(raw: bytes) -> str:
    """Original ``Cut0``: text up to 0x00, 0xFF or ``'A'``."""
    out = []
    for b in raw:
        if b in (0x00, 0xFF, ord("A")):
            break
        out.append(chr(b))
    return "".join(out)


def cut0a(raw: bytes) -> str:
    """Original ``Cut0A``: text up to 0x00 or 0xFF."""
    out = []
    for b in raw:
        if b in (0x00, 0xFF):
            break
        out.append(chr(b))
    return "".join(out)


def put0(text: str, length: int) -> bytes:
    """Original ``Put0``: pad text with 0x00 to ``length`` bytes."""
    raw = text.encode("latin-1")
    if len(raw) > length:
        raise ValueError(_("{text!r} is longer than {n} characters", text=text, n=length))
    return raw + b"\x00" * (length - len(raw))


def _digits(text: str, what: str) -> str:
    if text and not text.isdigit():
        raise ValueError(_("{what}: digits only ({text!r})", what=what, text=text))
    return text


DIAL_CHARS = "0123456789*#PFf"


def _dialstring(text: str, what: str) -> str:
    """Dial string: digits, ``*``, ``#`` and – per manual – the special characters
    ``P`` (dial pause ~1 s), ``F`` (flash 100 ms + pause), ``f`` (flash 80 ms + pause).
    Example: ``**9`` = ring all phones of a FRITZ!Box."""
    if any(c not in DIAL_CHARS for c in text):
        raise ValueError(_("{what}: only digits, *, # and P, F, f allowed ({text!r})", what=what, text=text))
    if len(text) > NUMBER_MAX:
        raise ValueError(_("{what}: max. {n} characters", what=what, n=NUMBER_MAX))
    return text


@dataclass
class Config:
    anschlussart: Anschlussart = Anschlussart.NEBENSTELLE
    lokale_rufzeit: str = "030"  # local ring time (TLN terminals), seconds, max. 120
    externe_rufzeit: str = "030"  # external ring time (AMT terminals), seconds, max. 120
    tuergespraechszeit: str = "060"  # door talk time, seconds, max. 120
    variante: int = 1  # active phonebook variant 1 (day) / 2 (night)
    mithoeren: bool = False  # "listen in" – stored but not evaluated by firmware 1.26
    pin: str = "0000"
    masterumleitung: Masterumleitung = Masterumleitung.AUS
    master_anrufbeantworter: bool = False
    masterumleitungsnummer: str = ""

    def validate(self) -> None:
        names = {"lokale_rufzeit": _("local ring time"), "externe_rufzeit": _("external ring time"),
                 "tuergespraechszeit": _("door talk time")}
        for name, label in names.items():
            value = _digits(getattr(self, name), label)
            if not value:
                raise ValueError(_("{what}: value missing", what=label))
            if len(value) > 4:
                raise ValueError(_("{what}: max. 4 digits", what=label))
            if int(value) > 120:  # per manual for all three times
                raise ValueError(_("{what}: maximum value is 120 seconds", what=label))
        if len(self.pin) != 4 or not self.pin.isdigit():
            raise ValueError(_("Enter a 4-digit PIN"))
        _dialstring(self.masterumleitungsnummer, _("Master redirect number"))
        if self.variante not in (1, 2):
            raise ValueError(_("Variant must be 1 or 2"))

    @classmethod
    def factory_defaults(cls) -> "Config":
        """Values of ``KonfigurationWerkseinstellungen`` in the original software."""
        return cls()

    @classmethod
    def from_bytes(cls, raw: bytes) -> "Config":
        return cls(
            anschlussart=Anschlussart.AMT if raw[0x01] == 0 else Anschlussart.NEBENSTELLE,
            lokale_rufzeit=cut0(raw[0x02:0x06]),
            externe_rufzeit=cut0(raw[0x06:0x0A]),
            tuergespraechszeit=cut0(raw[0x0A:0x0E]),
            variante=1 if raw[0x0E] == 0 else 2,
            mithoeren=raw[0x0F] != 0,
            pin=cut0(raw[0x10:0x15]),
            masterumleitung=Masterumleitung(raw[0x15]) if raw[0x15] <= 2 else Masterumleitung.AUS,
            master_anrufbeantworter=cut0a(raw[0x40:0x41]) == "A",
            masterumleitungsnummer=cut0(raw[0x41:0x41 + NUMBER_SIZE]),
        )

    def to_bytes(self, original: bytes, check: bool = True) -> bytes:
        """Build the configuration area; unknown bytes are taken from ``original``."""
        if check:
            self.validate()
        out = bytearray(original[:CONFIG_SIZE].ljust(CONFIG_SIZE, b"\x00"))
        out[0x01] = 0 if self.anschlussart == Anschlussart.AMT else 1
        out[0x02:0x06] = put0(self.lokale_rufzeit, 4)
        out[0x06:0x0A] = put0(self.externe_rufzeit, 4)
        out[0x0A:0x0E] = put0(self.tuergespraechszeit, 4)
        out[0x0E] = 0 if self.variante == 1 else 1
        out[0x0F] = 1 if self.mithoeren else 0
        out[0x10:0x15] = put0(self.pin, 5)
        out[0x15] = int(self.masterumleitung)
        out[0x40] = ord("A") if self.master_anrufbeantworter else ord(" ")
        out[0x41:0x41 + NUMBER_SIZE] = put0(self.masterumleitungsnummer, NUMBER_SIZE)
        return bytes(out)


@dataclass
class PhonebookEntry:
    bezeichnung: str = ""  # name
    nummer_v1: str = ""  # number for variant 1
    nummer_v2: str = ""  # number for variant 2
    ab_v1: bool = False  # answering machine function for variant 1
    ab_v2: bool = False
    tuerstation: int = 0  # door station, 0 = none, else 1..9
    tastercode: bytes = bytes(TASTERCODE_SIZE)  # bus address of the learned call button

    @property
    def gefangen(self) -> bool:
        """``True`` if a call button is assigned (original: "gefangen" = captured)."""
        return any(self.tastercode)

    @property
    def tastercode_str(self) -> str:
        return "-".join(f"{b:02X}" for b in self.tastercode)

    @staticmethod
    def parse_tastercode(text: str) -> bytes:
        parts = [p for p in text.replace(" ", "").split("-") if p]
        if len(parts) != TASTERCODE_SIZE:
            raise ValueError(_("Button code {text!r}: 8 hex bytes expected", text=text))
        return bytes(int(p, 16) for p in parts)

    @property
    def ab_code(self) -> int:
        """Column "Anrufbeantworter" of the original software (0, 1, 2 or 3)."""
        return (1 if self.ab_v1 else 0) | (2 if self.ab_v2 else 0)

    def validate(self) -> None:
        for num in (self.nummer_v1, self.nummer_v2):
            _dialstring(num, _("Phone number"))
        if not 0 <= self.tuerstation <= 9:
            raise ValueError(_("Please select a door station between 1 and 9"))
        if len(self.bezeichnung.encode("latin-1")) > NAME_SIZE:
            raise ValueError(_("Name: max. {n} characters", n=NAME_SIZE))
        if len(self.tastercode) != TASTERCODE_SIZE:
            raise ValueError(_("Button code must be 8 bytes long"))

    @classmethod
    def from_bytes(cls, raw: bytes, name_raw: bytes) -> "PhonebookEntry":
        ts = raw[8]
        return cls(
            bezeichnung=cut0a(name_raw),
            tastercode=bytes(raw[0:8]),
            tuerstation=int(chr(ts)) if chr(ts).isdigit() else 0,
            ab_v1=raw[10] == ord("A"),
            nummer_v1=cut0(raw[11:36]),
            ab_v2=raw[36] == ord("A"),
            nummer_v2=cut0(raw[37:62]),
        )

    def to_bytes(self, check: bool = True) -> bytes:
        if check:
            self.validate()
        out = bytearray(self.tastercode)
        out.append(ord(str(self.tuerstation)))  # ASCII, also '0' for none (as on the device)
        out.append(0)
        out.append(ord("A") if self.ab_v1 else ord(" "))
        out += put0(self.nummer_v1, NUMBER_SIZE)
        out.append(ord("A") if self.ab_v2 else ord(" "))
        out += put0(self.nummer_v2, NUMBER_SIZE)
        out += b"\x00" * (PB_ENTRY_SIZE - len(out))
        return bytes(out)


@dataclass
class GatewayImage:
    """Complete 6144-byte image with decoded configuration and phonebook."""

    raw: bytes = bytes(IMAGE_SIZE)
    config: Config = field(default_factory=Config)
    phonebook: list[PhonebookEntry] = field(
        default_factory=lambda: [PhonebookEntry() for _i in range(PB_ENTRIES)]
    )

    @classmethod
    def from_bytes(cls, raw: bytes) -> "GatewayImage":
        if len(raw) < IMAGE_SIZE:
            raise ValueError(_("Image too short: {n} instead of {size} bytes", n=len(raw), size=IMAGE_SIZE))
        raw = bytes(raw[:IMAGE_SIZE])
        entries = []
        for i in range(PB_ENTRIES):
            e = raw[PB_OFFSET + i * PB_ENTRY_SIZE:PB_OFFSET + (i + 1) * PB_ENTRY_SIZE]
            n = raw[NAME_OFFSET + i * NAME_SIZE:NAME_OFFSET + (i + 1) * NAME_SIZE]
            entries.append(PhonebookEntry.from_bytes(e, n))
        return cls(raw=raw, config=Config.from_bytes(raw), phonebook=entries)

    @classmethod
    def factory_defaults(cls) -> "GatewayImage":
        return cls()

    def validate(self) -> None:
        self.config.validate()
        for i, e in enumerate(self.phonebook, 1):
            try:
                e.validate()
            except ValueError as exc:
                raise ValueError(_("Phonebook entry {i}: {err}", i=i, err=exc)) from None
        if self.config.masterumleitung == Masterumleitung.VERZOEGERT and any(
            e.ab_v1 or e.ab_v2 for e in self.phonebook
        ):
            raise ValueError(_(
                "At least one phonebook entry has the answering machine function enabled. "
                "A delayed master redirect is not possible with it."
            ))

    def with_config(self, check: bool = True) -> bytes:
        """Image with the new configuration, rest unchanged (original: KonfigurationUpload)."""
        return self.config.to_bytes(self.raw, check) + self.raw[CONFIG_SIZE:]

    def with_phonebook(self, check: bool = True) -> bytes:
        """Image with the new phonebook, configuration unchanged (original: TelefonbuchUpload)."""
        if len(self.phonebook) != PB_ENTRIES:
            raise ValueError(_("Phonebook must have {n} entries", n=PB_ENTRIES))
        out = bytearray(self.raw[:PB_OFFSET])
        for e in self.phonebook:
            out += e.to_bytes(check)
        out += b"\x00" * (NAME_OFFSET - len(out))
        for e in self.phonebook:
            out += put0(e.bezeichnung, NAME_SIZE)
        out += b"\x00" * (IMAGE_SIZE - len(out))
        return bytes(out)

    def to_bytes(self, check: bool = True) -> bytes:
        """Image with the new configuration *and* the new phonebook.

        ``check=False`` only for backups: values are not validated then (data
        read from a device may deviate from the rules).
        """
        if check:
            self.validate()
        cfg = self.config.to_bytes(self.raw, check)
        return GatewayImage(raw=cfg + self.raw[CONFIG_SIZE:], phonebook=self.phonebook).with_phonebook(check)
