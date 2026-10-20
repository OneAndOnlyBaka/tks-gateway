"""File formats: JSON (lossless), raw image (.bin) and the formats of the
original software (.gtk configuration, .gtb phonebook).

.gtk is the plain-text report of the original software ("Gira
TK-Gatewaykonfiguration"), .gtb the content of the phonebook grid (columns
separated by tabs). Both are read tolerantly; compatibility was derived from the
program code but not checked against original files. Their labels stay German
on purpose – they must match the original software.
"""

from __future__ import annotations

import base64
import json
import re
from pathlib import Path

from .i18n import _
from .image import (
    IMAGE_SIZE,
    Anschlussart,
    Config,
    GatewayImage,
    Masterumleitung,
    PhonebookEntry,
)

# --------------------------------------------------------------------- JSON


def config_to_dict(c: Config) -> dict:
    return {
        "anschlussart": c.anschlussart.name.lower(),
        "lokale_rufzeit": c.lokale_rufzeit,
        "externe_rufzeit": c.externe_rufzeit,
        "tuergespraechszeit": c.tuergespraechszeit,
        "variante": c.variante,
        "mithoeren": c.mithoeren,
        "pin": c.pin,
        "masterumleitung": c.masterumleitung.name.lower(),
        "master_anrufbeantworter": c.master_anrufbeantworter,
        "masterumleitungsnummer": c.masterumleitungsnummer,
    }


def config_from_dict(d: dict) -> Config:
    c = Config()
    for key, value in d.items():
        if key == "anschlussart":
            value = Anschlussart[value.upper()]
        elif key == "masterumleitung":
            value = Masterumleitung[value.upper()]
        elif not hasattr(c, key):
            raise ValueError(_("unknown configuration parameter {key!r}", key=key))
        setattr(c, key, value)
    return c


def entry_to_dict(e: PhonebookEntry) -> dict:
    return {
        "bezeichnung": e.bezeichnung,
        "nummer_v1": e.nummer_v1,
        "nummer_v2": e.nummer_v2,
        "ab_v1": e.ab_v1,
        "ab_v2": e.ab_v2,
        "tuerstation": e.tuerstation,
        "tastercode": e.tastercode_str,
    }


def entry_from_dict(d: dict) -> PhonebookEntry:
    d = dict(d)
    code = d.pop("tastercode", None)
    e = PhonebookEntry(**d)
    if code:
        e.tastercode = PhonebookEntry.parse_tastercode(code)
    return e


def save_json(img: GatewayImage, path: Path) -> None:
    doc = {
        "format": "tks-gateway/1",
        "konfiguration": config_to_dict(img.config),
        "telefonbuch": [entry_to_dict(e) for e in img.phonebook],
        "rohabbild": base64.b64encode(img.raw).decode(),
    }
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_json(path: Path) -> GatewayImage:
    doc = json.loads(path.read_text(encoding="utf-8"))
    raw = base64.b64decode(doc["rohabbild"]) if "rohabbild" in doc else bytes(IMAGE_SIZE)
    img = GatewayImage.from_bytes(raw)
    if "konfiguration" in doc:
        img.config = config_from_dict(doc["konfiguration"])
    if "telefonbuch" in doc:
        entries = [entry_from_dict(e) for e in doc["telefonbuch"]]
        img.phonebook = (entries + [PhonebookEntry() for _ in range(50)])[:50]
    return img


# ---------------------------------------------------------------- Rohabbild


def save_bin(img: GatewayImage, path: Path) -> None:
    # backup: without validation so it never fails because of device data
    path.write_bytes(img.to_bytes(check=False))


def load_bin(path: Path) -> GatewayImage:
    return GatewayImage.from_bytes(path.read_bytes())


# ---------------------------------------------------------------------- .gtk


def _x(flag: bool) -> str:
    return "X" if flag else ""


def config_report(c: Config) -> str:
    """Klartextbericht wie "Konfiguration drucken"/"In Datei speichern" (.gtk)."""
    rows: list[tuple[str, str] | str | None] = [
        "Gira TK-Gatewaykonfiguration",
        None,
        ("Parameter", "Wert"),
        "Anschlussart",
        ("Amtsanschluss:", _x(c.anschlussart == Anschlussart.AMT)),
        ("Nebenstellenanschluss:", _x(c.anschlussart == Anschlussart.NEBENSTELLE)),
        None,
        ("PIN:", c.pin),
        ("Türgesprächszeit (in Sek.):", c.tuergespraechszeit),
        ("Lokale Rufzeit (in Sek.):", c.lokale_rufzeit),
        ("Externe Rufzeit (in Sek.):", c.externe_rufzeit),
        "Variantenumschaltung",
        ("Variante 1:", _x(c.variante == 1)),
        ("Variante 2:", _x(c.variante == 2)),
        None,
        "Mithören",
        ("An:", _x(c.mithoeren)),
        ("Aus:", _x(not c.mithoeren)),
        None,
        "Masterumleitungsnummer",
        ("Rufnummer:", c.masterumleitungsnummer),
        ("Anrufbeantworter:", _x(c.master_anrufbeantworter)),
        ("Aus: ", _x(c.masterumleitung == Masterumleitung.AUS)),
        ("Verzögert:", _x(c.masterumleitung == Masterumleitung.VERZOEGERT)),
        ("Sofort:", _x(c.masterumleitung == Masterumleitung.SOFORT)),
    ]
    out = []
    for row in rows:
        if row is None:
            out.append("")
        elif isinstance(row, str):
            out.append(row)
        else:
            out.append(f"{row[0]:<32}{row[1]}")
    return "\r\n".join(out) + "\r\n"


def parse_config_report(text: str) -> Config:
    c = Config()
    section = ""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped in ("Anschlussart", "Variantenumschaltung", "Mithören", "Masterumleitungsnummer"):
            section = stripped
            continue
        m = re.match(r"\s*(.+?:)\s*(.*)$", line)
        if not m:
            continue
        label, value = m.group(1), m.group(2).strip()
        checked = value.upper() == "X"
        if label == "Amtsanschluss:" and checked:
            c.anschlussart = Anschlussart.AMT
        elif label == "Nebenstellenanschluss:" and checked:
            c.anschlussart = Anschlussart.NEBENSTELLE
        elif label == "PIN:":
            c.pin = value
        elif label.startswith("Türgesprächszeit"):
            c.tuergespraechszeit = value
        elif label.startswith("Lokale Rufzeit"):
            c.lokale_rufzeit = value
        elif label.startswith("Externe Rufzeit"):
            c.externe_rufzeit = value
        elif label == "Variante 1:" and checked:
            c.variante = 1
        elif label == "Variante 2:" and checked:
            c.variante = 2
        elif section == "Mithören" and label == "An:":
            c.mithoeren = checked
        elif label == "Rufnummer:":
            c.masterumleitungsnummer = value
        elif label == "Anrufbeantworter:":
            c.master_anrufbeantworter = checked
        elif section == "Masterumleitungsnummer" and label == "Aus:" and checked:
            c.masterumleitung = Masterumleitung.AUS
        elif label == "Verzögert:" and checked:
            c.masterumleitung = Masterumleitung.VERZOEGERT
        elif label == "Sofort:" and checked:
            c.masterumleitung = Masterumleitung.SOFORT
    return c


def save_gtk(c: Config, path: Path) -> None:
    path.write_bytes(config_report(c).encode("cp1252"))


def load_gtk(path: Path) -> Config:
    return parse_config_report(path.read_bytes().decode("cp1252"))


# ---------------------------------------------------------------------- .gtb

GTB_HEADER = [
    "Index",
    "Teilnehmer",
    "Telefonnummer Variante 1",
    "Telefonnummer Variante 2",
    "Anrufbeantworter",
    "Türstation",
    "Tastercode",
    "Adresse",
]


def phonebook_rows(entries: list[PhonebookEntry]) -> list[list[str]]:
    return [
        [
            str(i),
            e.bezeichnung,
            e.nummer_v1,
            e.nummer_v2,
            str(e.ab_code),
            str(e.tuerstation),
            "gefangen" if e.gefangen else "frei",
            e.tastercode_str,
        ]
        for i, e in enumerate(entries, 1)
    ]


def save_gtb(entries: list[PhonebookEntry], path: Path) -> None:
    rows = [GTB_HEADER] + phonebook_rows(entries)
    path.write_bytes(("\r".join("\t".join(r) for r in rows) + "\r\n").encode("cp1252"))


def load_gtb(path: Path) -> list[PhonebookEntry]:
    text = path.read_bytes().decode("cp1252")
    entries = [PhonebookEntry() for _ in range(50)]
    for line in re.split(r"\r\n|\r|\n", text):
        cells = line.split("\t")
        if len(cells) < 6 or not cells[0].strip().isdigit():
            continue
        idx = int(cells[0]) - 1
        if not 0 <= idx < 50:
            continue
        ab = int(cells[4]) if cells[4].strip().isdigit() else 0
        e = PhonebookEntry(
            bezeichnung=cells[1],
            nummer_v1=cells[2].strip(),
            nummer_v2=cells[3].strip(),
            ab_v1=bool(ab & 1),
            ab_v2=bool(ab & 2),
            tuerstation=int(cells[5]) if cells[5].strip().isdigit() else 0,
        )
        if len(cells) > 7 and cells[7].strip():
            e.tastercode = PhonebookEntry.parse_tastercode(cells[7])
        entries[idx] = e
    return entries


def is_used(e: PhonebookEntry) -> bool:
    return bool(e.nummer_v1 or e.nummer_v2 or e.bezeichnung or e.gefangen or e.tuerstation)


def phonebook_report(entries: list[PhonebookEntry], only_used: bool = False) -> str:
    lines = ["Telefonbuchübersicht GIRA TK-Gateway", ""]
    lines.append(f"{'Index':<6}{'Bezeichnung':<22}{'Telefonnummer Variante 1':<27}"
                 f"{'Telefonnummer Variante 2':<27}{'A/B':<5}{'Tür':<5}Tastercode")
    rows = [r for r, e in zip(phonebook_rows(entries), entries) if is_used(e) or not only_used]
    for row in rows:
        lines.append(f"{row[0]:<6}{row[1]:<22}{row[2]:<27}{row[3]:<27}{row[4]:<5}{row[5]:<5}{row[7]}")
    if not rows:
        lines.append("(keine Einträge)")
    return "\n".join(lines) + "\n"
