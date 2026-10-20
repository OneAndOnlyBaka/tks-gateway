"""Command line: ``tks-gateway <command>`` (``tks-gateway --help`` for an overview).

English by default; ``--lang de`` or ``TKS_GATEWAY_LANG=de`` switches messages and
help to German. The former German command and option names remain available
as aliases (e.g. ``eintrag`` = ``entry``, ``--loeschen`` = ``--delete``).
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

from . import files
from .i18n import LANGS, _, set_lang
from .image import Anschlussart, GatewayImage, Masterumleitung, PhonebookEntry
from .logdecode import format_line
from .protocol import Gateway, GatewayError

ON = ("on", "an")
ONOFF = ["on", "off", "an", "aus"]


def _progress(done: int, total: int) -> None:
    width = 40
    filled = width * done // total
    print(f"\r[{'#' * filled}{'.' * (width - filled)}] {done}/{total} bytes", end="", file=sys.stderr)
    if done >= total:
        print(file=sys.stderr)


def _connect(args) -> Gateway:
    if args.sim:
        from .simulator import SimulatedPort

        gw = Gateway(SimulatedPort(), log=_verbose(args))
    elif not args.port:
        sys.exit(_("Please specify the serial port with --port (e.g. --port /dev/ttyUSB0 or COM1)"))
    else:
        gw = Gateway.open(args.port, log=_verbose(args))
    gw.quiet()  # a stale log mode (gateway kept logging after a restart) would garble answers
    return gw


def _verbose(args):
    return (lambda m: print(f"  {m}", file=sys.stderr)) if args.verbose else None


def load_any(path: Path) -> GatewayImage:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return files.load_json(path)
    if suffix == ".bin":
        return files.load_bin(path)
    if suffix == ".gtk":
        img = GatewayImage.factory_defaults()
        img.config = files.load_gtk(path)
        return img
    if suffix == ".gtb":
        img = GatewayImage.factory_defaults()
        img.phonebook = files.load_gtb(path)
        return img
    raise SystemExit(_("Unknown file format: {path} (expected .json, .bin, .gtk or .gtb)", path=path))


def save_any(img: GatewayImage, path: Path) -> None:
    suffix = path.suffix.lower()
    if suffix == ".json":
        files.save_json(img, path)
    elif suffix == ".bin":
        files.save_bin(img, path)
    elif suffix == ".gtk":
        files.save_gtk(img.config, path)
    elif suffix == ".gtb":
        files.save_gtb(img.phonebook, path)
    else:
        raise SystemExit(_("Unknown file format: {path} (expected .json, .bin, .gtk or .gtb)", path=path))


def show(img: GatewayImage) -> None:
    # the report uses the labels of the original software (.gtk format)
    print(files.config_report(img.config).replace("\r\n", "\n"))
    print(files.phonebook_report(img.phonebook, only_used=True))


# ------------------------------------------------------------------ commands


def cmd_version(args) -> None:
    with _connect(args) as gw:
        v = gw.read_version()
    print(v.text)
    if v.bootloader_only:
        print(_("Note: the TK gateway only has a bootloader. Please install a firmware."))
    elif not v.has_bustreiber:
        print(_("Note: the TK gateway has no bus driver. Please install a bus driver firmware."))


def cmd_read(args) -> None:
    with _connect(args) as gw:
        raw = gw.read_image(_progress)
    img = GatewayImage.from_bytes(raw)
    if args.output:
        save_any(img, args.output)
        print(_("Saved: {path}", path=args.output))
    else:
        show(img)


def cmd_show(args) -> None:
    show(load_any(args.file))


def cmd_write(args) -> None:
    img = load_any(args.file)
    img.validate()
    suffix = args.file.suffix.lower()
    if suffix in (".gtk", ".gtb") or args.only:
        # original behaviour: read the current image, replace only one part
        with _connect(args) as gw:
            current = GatewayImage.from_bytes(gw.read_image(_progress))
            part = args.only or ("konfiguration" if suffix == ".gtk" else "telefonbuch")
            if part in ("konfiguration", "config"):
                current.config = img.config
                data = current.with_config()
            else:
                current.phonebook = img.phonebook
                data = current.with_phonebook()
            gw.write_image(data, _progress)
    else:
        with _connect(args) as gw:
            gw.write_image(img.to_bytes(), _progress)
    print(_("Transfer successful. The TK gateway stores the data."))


def cmd_set(args) -> None:
    """Change single parameters: read the current image, change it, write it back."""
    with _connect(args) as gw:
        img = GatewayImage.from_bytes(gw.read_image(_progress))
        c = img.config
        if args.connection:
            c.anschlussart = Anschlussart.AMT if args.connection in ("amt", "direct") else Anschlussart.NEBENSTELLE
        for name in ("lokale_rufzeit", "externe_rufzeit", "tuergespraechszeit"):
            value = getattr(args, name)
            if value is not None:
                setattr(c, name, f"{value:03d}")
        if args.pin is not None:
            c.pin = args.pin
        if args.variant is not None:
            c.variante = args.variant
        if args.listen_in is not None:
            c.mithoeren = args.listen_in in ON
        if args.master_redirect:
            c.masterumleitung = {
                "off": Masterumleitung.AUS, "aus": Masterumleitung.AUS,
                "delayed": Masterumleitung.VERZOEGERT, "verzoegert": Masterumleitung.VERZOEGERT,
                "immediate": Masterumleitung.SOFORT, "sofort": Masterumleitung.SOFORT,
            }[args.master_redirect]
        if args.master_number is not None:
            c.masterumleitungsnummer = args.master_number
        if args.master_ab is not None:
            c.master_anrufbeantworter = args.master_ab in ON
        img.validate()
        gw.write_image(img.with_config(), _progress)
    print(_("Configuration transferred successfully."))


def cmd_defaults(args) -> None:
    with _connect(args) as gw:
        img = GatewayImage.from_bytes(gw.read_image(_progress))
        img.config = GatewayImage.factory_defaults().config
        gw.write_image(img.with_config(), _progress)
    print(_("Configuration reset to factory settings."))


def cmd_entry(args) -> None:
    """Set or delete a phonebook entry."""
    if not 1 <= args.index <= 50:
        sys.exit(_("Index must be between 1 and 50"))
    with _connect(args) as gw:
        img = GatewayImage.from_bytes(gw.read_image(_progress))
        e = img.phonebook[args.index - 1]
        if args.delete:
            e = PhonebookEntry()
        else:
            if args.name is not None:
                e.bezeichnung = args.name
            if args.v1 is not None:
                e.nummer_v1 = args.v1
            if args.v2 is not None:
                e.nummer_v2 = args.v2
            if args.ab_v1 is not None:
                e.ab_v1 = args.ab_v1 in ON
            if args.ab_v2 is not None:
                e.ab_v2 = args.ab_v2 in ON
            if args.door_station is not None:
                e.tuerstation = args.door_station
            if args.button_code is not None:
                e.tastercode = PhonebookEntry.parse_tastercode(args.button_code)
            if args.learn:
                if not e.tuerstation:
                    sys.exit(_("Please assign a valid door station number (1-9)"))
                e.tastercode = gw.fetch_ruftaste(args.index, e.tuerstation)
                print(_("Call learned successfully: {code}", code=e.tastercode_str))
        img.phonebook[args.index - 1] = e
        img.validate()
        gw.write_image(img.with_phonebook(), _progress)
    print(_("Phonebook transferred successfully."))


def cmd_call_button(args) -> None:
    with _connect(args) as gw:
        code = gw.fetch_ruftaste(args.index, args.door_station)
    print("-".join(f"{b:02X}" for b in code))


def cmd_bootloader_reset(args) -> None:
    """Hidden function of the original software (key "r" on the "Read" button)."""
    from .protocol import TransferTimeout

    with _connect(args) as gw:
        gw.reset_bootloader()
        time.sleep(1.0)
        try:
            print(gw.read_version().text)
        except TransferTimeout:
            sys.exit(_("No response. The reset only works when the gateway is in the bootloader; "
                       "with running firmware please power-cycle it."))


def cmd_firmware(args) -> None:
    data = args.file.read_bytes()
    with _connect(args) as gw:
        gw.log_off()
        if args.bus_driver:
            gw.upload_bustreiber(data, _progress)
            print(_("Bus driver transferred successfully."))
        else:
            gw.upload_firmware(data, _progress)
            print(_("Firmware transferred successfully. The TK gateway restarts, please wait approx. 5 seconds."))


def cmd_log(args) -> None:
    out = args.output.open("a", encoding="utf-8") if args.output else None
    with _connect(args) as gw:
        gw.log_on()
        print(_("Logging started (Ctrl+C to stop)"), file=sys.stderr)
        try:
            for line in gw.iter_log():
                text = f"{time.strftime('%d.%m.%Y %H:%M:%S')}  {format_line(line)}"
                print(text, flush=True)
                if out:
                    out.write(text + "\n")
                    out.flush()
        except KeyboardInterrupt:
            pass
        finally:
            gw.log_off()
            print(_("Logging stopped"), file=sys.stderr)
            if out:
                out.close()


def cmd_sbom(args) -> None:
    import json

    from .licenses import sbom

    text = json.dumps(sbom(), indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
        print(_("SBOM written to {path}", path=args.output))
    else:
        sys.stdout.write(text)


def cmd_licenses(args) -> None:
    from .licenses import components

    for c in components():
        print(f"{c.name:<16} {c.version:<10} {c.license:<16} {c.url}")


def cmd_web(args) -> None:
    from .web import main

    main(device=args.port, sim=args.sim, host=args.host, port=args.http_port)


def cmd_ports(args) -> None:
    from serial.tools import list_ports

    for p in list_ports.comports():
        print(f"{p.device}\t{p.description}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="tks-gateway",
        description=_("Commissioning of the Gira TK gateway 1290 00 (re-implementation of software V1.01)"),
    )
    p.add_argument("--port", "-p", default=os.environ.get("TKS_GATEWAY_PORT") or None,
                   help=_("serial port, e.g. /dev/ttyUSB0 or COM1 (default: $TKS_GATEWAY_PORT)"))
    p.add_argument("--sim", action="store_true", help=_("simulated gateway instead of a real serial port"))
    p.add_argument("--lang", choices=LANGS, help=_("language of messages (default: en or $TKS_GATEWAY_LANG)"))
    p.add_argument("--verbose", "-v", action="store_true")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("ports", help=_("list available serial ports")).set_defaults(func=cmd_ports)
    s = sub.add_parser("web", help=_("start the web UI"))
    s.add_argument("--host", default="127.0.0.1", help=_("address (default: local only)"))
    s.add_argument("--http-port", type=int, default=5000)
    s.set_defaults(func=cmd_web)
    sub.add_parser("version", help=_("read the firmware version")).set_defaults(func=cmd_version)

    s = sub.add_parser("read", help=_("load configuration and phonebook from the gateway"))
    s.add_argument("-o", "--output", type=Path, help=_("file (.json, .bin, .gtk, .gtb); otherwise display"))
    s.set_defaults(func=cmd_read)

    s = sub.add_parser("show", help=_("display a file"))
    s.add_argument("file", type=Path)
    s.set_defaults(func=cmd_show)

    s = sub.add_parser("write", help=_("save a file to the gateway"))
    s.add_argument("file", type=Path, help=_(".json/.bin (complete), .gtk (configuration) or .gtb (phonebook)"))
    s.add_argument("--only", choices=["config", "phonebook", "konfiguration", "telefonbuch"],
                   help=_("transfer only this part"))
    s.set_defaults(func=cmd_write)

    s = sub.add_parser("set", help=_("change single configuration parameters"))
    s.add_argument("--connection", "--anschlussart", choices=["direct", "extension", "amt", "nebenstelle"])
    s.add_argument("--local-ring-time", "--lokale-rufzeit", dest="lokale_rufzeit", type=int, metavar="SEC")
    s.add_argument("--external-ring-time", "--externe-rufzeit", dest="externe_rufzeit", type=int, metavar="SEC")
    s.add_argument("--door-talk-time", "--tuergespraechszeit", dest="tuergespraechszeit", type=int, metavar="SEC")
    s.add_argument("--pin")
    s.add_argument("--variant", "--variante", type=int, choices=[1, 2])
    s.add_argument("--listen-in", "--mithoeren", choices=ONOFF)
    s.add_argument("--master-redirect", "--masterumleitung",
                   choices=["off", "delayed", "immediate", "aus", "verzoegert", "sofort"])
    s.add_argument("--master-number", "--masternummer", metavar="NUMBER")
    s.add_argument("--master-ab", choices=ONOFF, help=_("answering machine function of the master redirect"))
    s.set_defaults(func=cmd_set)

    sub.add_parser("defaults", aliases=["werkseinstellungen"],
                   help=_("reset the configuration to factory settings")).set_defaults(func=cmd_defaults)

    s = sub.add_parser("entry", aliases=["eintrag"], help=_("edit a phonebook entry"))
    s.add_argument("index", type=int, help="1-50")
    s.add_argument("--name")
    s.add_argument("--v1", help=_("phone number variant 1"))
    s.add_argument("--v2", help=_("phone number variant 2"))
    s.add_argument("--ab-v1", choices=ONOFF)
    s.add_argument("--ab-v2", choices=ONOFF)
    s.add_argument("--door-station", "--tuerstation", type=int, choices=range(0, 10), metavar="0-9")
    s.add_argument("--button-code", "--tastercode", metavar="XX-XX-XX-XX-XX-XX-XX-XX")
    s.add_argument("--learn", "--einlernen", action="store_true",
                   help=_("assign the call button pressed last at the door station"))
    s.add_argument("--delete", "--loeschen", action="store_true")
    s.set_defaults(func=cmd_entry)

    s = sub.add_parser("call-button", aliases=["ruftaste"],
                       help=_("assign a call button to a phonebook entry, print the button code"))
    s.add_argument("door_station", type=int, choices=range(1, 10), metavar="DOOR_STATION")
    s.add_argument("index", type=int, choices=range(1, 51), metavar="INDEX")
    s.set_defaults(func=cmd_call_button)

    sub.add_parser("bootloader-reset", help=_("restart the bootloader (hidden function of the original)")) \
        .set_defaults(func=cmd_bootloader_reset)

    s = sub.add_parser("firmware", help=_("transfer firmware (.tsk) or bus driver (.hex)"))
    s.add_argument("file", type=Path)
    s.add_argument("--bus-driver", "--bustreiber", action="store_true",
                   help=_("file is bus driver firmware (PIC, .hex)"))
    s.set_defaults(func=cmd_firmware)

    s = sub.add_parser("sbom", help=_("write a CycloneDX SBOM of this installation (JSON)"))
    s.add_argument("--output", "-o", type=Path, help=_("file (default: standard output)"))
    s.set_defaults(func=cmd_sbom)
    sub.add_parser("licenses", help=_("list the third-party components and their licenses")) \
        .set_defaults(func=cmd_licenses)
    s = sub.add_parser("log", help=_("capture the bus communication"))
    s.add_argument("-o", "--output", type=Path, help=_("additionally write to a file"))
    s.set_defaults(func=cmd_log)
    return p


def main(argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    # the language must be known before the help texts are built
    for i, a in enumerate(argv):
        if a == "--lang" and i + 1 < len(argv):
            set_lang(argv[i + 1])
        elif a.startswith("--lang="):
            set_lang(a.split("=", 1)[1])
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except (GatewayError, ValueError) as exc:
        sys.exit(_("Error: {err}", err=exc))


if __name__ == "__main__":
    main()
