"""Web UI (Flask) – replaces the windows of the original commissioning software.

Start: ``tks-gateway --port /dev/ttyUSB0 web`` or ``tks-gateway --sim web``.

Device access runs as a background job; the page polls ``/api/status``.
As in the original only one access to the serial port is possible at a time –
logging occupies it as well.

Language: English by default, German selectable. The UI sends the cookie
``lang`` (``en``/``de``); messages created on the server follow it, also
inside background jobs.
"""

from __future__ import annotations

import io
import json
import re
import tempfile
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

from flask import Flask, jsonify, render_template, request, send_file
from markupsafe import Markup

from . import files
from .i18n import LANGS, _, get_lang, js_catalog, set_lang, ui
from .image import GatewayImage, PhonebookEntry
from .logdecode import decode, telegram, tuerruf_adresse
from .protocol import Gateway, GatewayError, TransferTimeout


@dataclass
class Job:
    name: str = ""
    kind: str = ""  # stable identifier (independent of the language), e.g. "version"
    busy: bool = False
    done: int = 0
    total: int = 0
    message: str = ""
    error: str = ""
    finished_at: float = 0.0


@dataclass
class LogLine:
    zeit: str  # timestamp
    roh: str  # raw line from the gateway ("" for messages of this program)
    text: str  # English message for roh == ""; plain text is created on request
    typ: str = ""  # S = sends, E = receives, T = calls, "" = message
    code: str = ""  # telegram code (hex)
    tuerruf: str = ""  # button code "XX-XX-…" of a received door call (E 11)


def _in_thread(target: Callable[[], None]) -> threading.Thread:
    """Start a thread that uses the language of the current request."""
    lang = get_lang()

    def run() -> None:
        set_lang(lang)
        target()

    t = threading.Thread(target=run, daemon=True)
    t.start()
    return t


class Service:
    def __init__(self, device: str | None = None, sim: bool = False) -> None:
        self.device = device
        self.sim_port = None
        if sim:
            from .simulator import SimulatedPort

            self.sim_port = SimulatedPort()
        self.image = GatewayImage.factory_defaults()
        self.loaded = False  # image was read from the gateway
        # call buttons as stored in the gateway (last read/write), per entry
        self.gateway_buttons = self._buttons(self.image)
        self.version: dict | None = None  # VersionInfo.as_dict()
        self.job = Job()
        self.log_lines: list[LogLine] = []
        self.log_active = False
        self._log_stop = threading.Event()
        self._log_gw: Gateway | None = None
        self._lock = threading.Lock()

    # ------------------------------------------------------------- access

    def connect(self) -> Gateway:
        if self.sim_port is not None:
            gw = Gateway(self.sim_port)
        elif not self.device:
            raise GatewayError(_("No serial port selected (settings)"))
        else:
            try:
                gw = Gateway.open(self.device)
            except Exception as exc:  # serial.SerialException etc.
                raise GatewayError(_("Serial port {dev} not available or busy: {err}",
                                     dev=self.device, err=exc)) from None
        # the gateway may still be logging from before a restart of this program
        if gw.quiet():
            self._add_log("", "The gateway was still logging (e.g. after a restart) – logging switched off")
        return gw

    @staticmethod
    def _buttons(image: GatewayImage) -> list[tuple[bytes, int]]:
        return [(e.tastercode, e.tuerstation) for e in image.phonebook]

    def set_gateway_state(self, image: GatewayImage) -> None:
        """Remember what the gateway contains now (after reading or writing)."""
        self.gateway_buttons = self._buttons(image)

    def unsaved_buttons(self) -> list[int]:
        """Entries (1-based) whose call button assignment is not yet in the gateway."""
        return [i for i, (now, gw) in enumerate(zip(self._buttons(self.image), self.gateway_buttons), 1)
                if now != gw and (any(now[0]) or any(gw[0]))]  # door station alone does not matter

    def busy(self) -> bool:
        return self.job.busy or self.log_active

    def start_job(self, name: str, work: Callable[[Gateway, Callable[[int, int], None]], str], kind: str = "") -> None:
        with self._lock:
            if self.busy():
                raise GatewayError(_(
                    "The serial port is busy. Other parts of the program are using it. Stop logging if necessary."
                ))
            self.job = Job(name=name, kind=kind, busy=True, message=_("{name} …", name=name))

        def progress(done: int, total: int) -> None:
            self.job.done, self.job.total = done, total

        def run() -> None:
            try:
                with self.connect() as gw:
                    self.job.message = work(gw, progress)
            except (GatewayError, ValueError) as exc:
                self.job.error = str(exc)
                self.job.message = _("{name} failed", name=name)
            except Exception as exc:  # unexpected, show it anyway
                self.job.error = f"{type(exc).__name__}: {exc}"
                self.job.message = _("{name} failed", name=name)
            finally:
                self.job.busy = False
                self.job.finished_at = time.time()

        _in_thread(run)

    # --------------------------------------------------------------- logging

    def start_log(self) -> None:
        with self._lock:
            if self.busy():
                raise GatewayError(_("Logging not possible, the serial port is busy"))
            gw = self.connect()
            self._log_gw = gw
            self.log_active = True
            self._log_stop.clear()

        def run() -> None:
            try:
                gw.log_on()
                self._add_log("", "Logging started")
                if self.sim_port is not None:
                    threading.Thread(target=self._sim_traffic, daemon=True).start()
                for line in gw.iter_log(self._log_stop.is_set):
                    self._add_log(line)
            except Exception as exc:
                self._add_log("", f"Error: {exc}")
            finally:
                try:
                    gw.log_off()
                finally:
                    gw.close()
                self.log_active = False
                self._add_log("", "Logging stopped")

        _in_thread(run)

    def stop_log(self) -> None:
        self._log_stop.set()

    def ping_log(self) -> None:
        """Test output: send "i" while logging. The firmware then queries the
        bus driver via telegram 0x90 and logs it as "S: 90 …"."""
        if not self.log_active or self._log_gw is None:
            raise GatewayError(_("Logging is not running"))
        self._log_gw.port.write(b"i\r")

    def _add_log(self, raw: str, message: str = "") -> None:
        # The version text has no line end; a following log line is then glued
        # to it ("…Version 01.26 S: 90 …") – split into two entries.
        m = re.search(r" ([SE]): ", raw)
        if raw and m and not raw.startswith(("S: ", "E: ", "T: ")):
            self._add_log(raw[:m.start()])
            self._add_log(raw[m.start() + 1:])
            return
        t = telegram(raw)
        adr = tuerruf_adresse(raw)
        self.log_lines.append(LogLine(
            zeit=time.strftime("%d.%m.%Y %H:%M:%S"),
            roh=raw,
            text=message,
            typ=raw[:1] if raw[:1] in ("S", "E", "T") else "",
            code=t[1] if t else "",
            tuerruf="-".join(f"{b:02X}" for b in adr) if adr else "",
        ))
        del self.log_lines[:-5000]

    @staticmethod
    def log_text(line: LogLine) -> str:
        """Plain text in the language of the current request."""
        if line.roh:
            return decode(line.roh)
        if line.text.startswith("Error: "):
            return _("Error: {err}", err=line.text[7:])
        return _(line.text)

    def _sim_traffic(self) -> None:
        # three different call buttons, normal conversation telegrams in between
        demo = ["E: 11 1A 2B 3C 4D 5E 00 00 00 ", "T: DIAL  01 00 00 - 0221123456",
                "S: 21 1A 2B 3C 4D 00 00 00 00 ", "E: 11 CC ED 19 83 00 00 00 00 ",
                "S: 20 1A 2B 3C 4D 00 00 00 00 ", "E: 11 0F 22 31 07 00 00 00 00 ",
                "E: 20 1A 2B 3C 4D 01 00 00 00 "]
        i = 0
        while not self._log_stop.wait(2.0):
            self.sim_port.emit_log(demo[i % len(demo)])
            i += 1


def _entry_json(i: int, e: PhonebookEntry) -> dict:
    d = files.entry_to_dict(e)
    d.update(index=i, gefangen=e.gefangen)
    return d


def create_app(device: str | None = None, sim: bool = False) -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024
    svc = Service(device, sim)
    app.extensions["tks_gateway"] = svc

    @app.before_request
    def _lang():
        set_lang(request.cookies.get("lang"))

    @app.errorhandler(GatewayError)
    @app.errorhandler(ValueError)
    def _err(exc):
        return jsonify(error=str(exc)), 400

    @app.get("/")
    def index():
        return render_template(
            "index.html",
            t=lambda key: Markup(ui(key)),
            lang=get_lang(),
            langs=LANGS,
            js_i18n=js_catalog(),
        )

    @app.get("/api/licenses")
    def licenses_list():
        from .licenses import components

        return jsonify(components=[c.as_dict() for c in components()])

    @app.get("/api/sbom")
    def sbom_download():
        from .licenses import sbom

        doc = sbom()
        name = f"tks-gateway-{doc['metadata']['component'].get('version', '')}.cdx.json"
        return send_file(io.BytesIO(json.dumps(doc, indent=2).encode("utf-8")),
                         mimetype="application/vnd.cyclonedx+json", as_attachment=True, download_name=name)

    @app.get("/api/status")
    def status():
        return jsonify(
            job=asdict(svc.job),
            log_active=svc.log_active,
            device=svc.device,
            sim=svc.sim_port is not None,
            version=svc.version,
            loaded=svc.loaded,
            unsaved_buttons=svc.unsaved_buttons(),
        )

    @app.get("/api/ports")
    def ports():
        try:
            from serial.tools import list_ports

            found = [{"device": p.device, "description": p.description} for p in list_ports.comports()]
        except Exception:
            found = []
        return jsonify(ports=found, device=svc.device)

    @app.post("/api/settings")
    def settings():
        if svc.busy():
            raise GatewayError(_("The serial port is busy"))
        svc.device = (request.json or {}).get("device") or None
        return jsonify(device=svc.device)

    # ------------------------------------------------- working copy (form)

    @app.get("/api/image")
    def get_image():
        return jsonify(
            konfiguration=files.config_to_dict(svc.image.config),
            telefonbuch=[_entry_json(i, e) for i, e in enumerate(svc.image.phonebook, 1)],
            loaded=svc.loaded,
        )

    @app.put("/api/config")
    def put_config():
        cfg = files.config_from_dict(request.json or {})
        cfg.validate()
        svc.image.config = cfg
        return get_image()

    @app.post("/api/config/werkseinstellungen")
    def defaults():
        svc.image.config = GatewayImage.factory_defaults().config
        return get_image()

    @app.put("/api/phonebook/<int:index>")
    def put_entry(index: int):
        if not 1 <= index <= 50:
            raise ValueError(_("Index must be between 1 and 50"))
        e = files.entry_from_dict(request.json or {})
        e.validate()
        svc.image.phonebook[index - 1] = e
        return get_image()

    @app.delete("/api/phonebook/<int:index>")
    def delete_entry(index: int):
        svc.image.phonebook[index - 1] = PhonebookEntry()
        return get_image()

    @app.delete("/api/phonebook")
    def clear_phonebook():
        svc.image.phonebook = [PhonebookEntry() for _i in range(50)]
        return get_image()

    # --------------------------------------------------------- device jobs

    @app.post("/api/gateway/version")
    def job_version():
        def work(gw, progress):
            try:
                v = gw.read_version()
            except TransferTimeout:
                svc.version = None
                raise GatewayError(_(
                    "No response. Please check the connection and pinout (swap TX/RX if needed) "
                    "and power the TK gateway."
                )) from None
            svc.version = v.as_dict()
            if v.bootloader_only:
                return _("The TK gateway only has a bootloader. Please install a firmware!")
            if not v.has_bustreiber:
                return _("The TK gateway has no bus driver. Please install a bus driver firmware!")
            return _("Firmware version read successfully: {v}", v=v.text)

        svc.start_job(_("Read firmware version"), work, kind="version")
        return jsonify(ok=True), 202

    @app.post("/api/gateway/read")
    def job_read():
        def work(gw, progress):
            svc.image = GatewayImage.from_bytes(gw.read_image(progress))
            svc.set_gateway_state(svc.image)
            svc.loaded = True
            return _("Configuration and phonebook read successfully")

        svc.start_job(_("Load from gateway"), work, kind="read")
        return jsonify(ok=True), 202

    @app.post("/api/gateway/write")
    def job_write():
        part = (request.json or {}).get("part", "alles")
        if part not in ("konfiguration", "telefonbuch", "alles"):
            raise ValueError(_("part must be konfiguration, telefonbuch or alles"))
        svc.image.validate()
        cfg, pb = svc.image.config, list(svc.image.phonebook)

        def work(gw, progress):
            # as in the original: fetch the current image, replace only the part
            current = GatewayImage.from_bytes(gw.read_image(progress))
            if part in ("konfiguration", "alles"):
                current.config = cfg
            if part in ("telefonbuch", "alles"):
                current.phonebook = pb
            current.validate()
            data = {"konfiguration": current.with_config,
                    "telefonbuch": current.with_phonebook}.get(part, current.to_bytes)()
            gw.write_image(data, progress)
            written = GatewayImage.from_bytes(data)
            svc.set_gateway_state(written)
            # keep unsaved edits of the part that was not written
            if part == "konfiguration":
                written.phonebook = svc.image.phonebook
            elif part == "telefonbuch":
                written.config = svc.image.config
            svc.image = written
            svc.loaded = True
            return {"konfiguration": _("Configuration transferred successfully"),
                    "telefonbuch": _("Phonebook transferred successfully")}.get(
                part, _("Configuration and phonebook transferred successfully"))

        svc.start_job(_("Save to gateway"), work, kind="write")
        return jsonify(ok=True), 202

    @app.post("/api/gateway/ruftaste/<int:index>")
    def job_ruftaste(index: int):
        e = svc.image.phonebook[index - 1]
        if not 1 <= e.tuerstation <= 9:
            raise ValueError(_("Please assign a valid door station number (1-9) to the selected phonebook entry"))

        def work(gw, progress):
            # the firmware stores button code + door station itself in EEPROM (0x0CC3)
            e.tastercode = gw.fetch_ruftaste(index, e.tuerstation)
            svc.gateway_buttons[index - 1] = (e.tastercode, e.tuerstation)
            return _("Call learned successfully ({code}) and saved in the gateway", code=e.tastercode_str)

        svc.start_job(_("Assign call button"), work)
        return jsonify(ok=True), 202

    @app.post("/api/gateway/bootloader-reset")
    def job_bootloader_reset():
        def work(gw, progress):
            gw.reset_bootloader()
            time.sleep(1.0)
            try:
                v = gw.read_version()
            except TransferTimeout:
                raise GatewayError(_(
                    "No response after the reset. The reset only works when the gateway is in the "
                    "bootloader – otherwise power-cycle it."
                )) from None
            svc.version = v.as_dict()
            return _("Bootloader reset: {v}", v=v.text)

        svc.start_job(_("Bootloader reset"), work)
        return jsonify(ok=True), 202

    @app.post("/api/gateway/firmware")
    def job_firmware():
        upload = request.files.get("datei")
        if not upload:
            raise ValueError(_("No file selected"))
        data = upload.read()
        bustreiber = request.form.get("art") == "bustreiber"

        def work(gw, progress):
            if bustreiber:
                gw.upload_bustreiber(data, progress)
                return _("Bus driver transferred successfully")
            gw.upload_firmware(data, progress)
            time.sleep(5)  # gateway restarts
            return _("Firmware transferred successfully. The TK gateway has restarted.")

        svc.start_job(_("Transfer bus driver") if bustreiber else _("Transfer firmware"), work)
        return jsonify(ok=True), 202

    # ---------------------------------------------------------------- log

    @app.post("/api/log/start")
    def log_start():
        svc.start_log()
        return jsonify(ok=True)

    @app.post("/api/log/stop")
    def log_stop():
        svc.stop_log()
        return jsonify(ok=True)

    @app.post("/api/log/ping")
    def log_ping():
        svc.ping_log()
        return jsonify(ok=True)

    @app.get("/api/log")
    def log_get():
        since = request.args.get("since", 0, type=int)
        lines = [{**asdict(l), "text": svc.log_text(l)} for l in svc.log_lines[since:]]
        return jsonify(lines=lines, next=len(svc.log_lines))

    @app.delete("/api/log")
    def log_clear():
        svc.log_lines.clear()
        return jsonify(ok=True)

    # Simulator only: emulate operation by phone (e.g. "*3*2#" = variant 2) so the
    # connection test can be played through without a real PBX.
    if svc.sim_port is not None:
        @app.post("/api/sim/dtmf")
        def sim_dtmf():
            code = (request.json or {}).get("code", "").replace(" ", "")
            m = re.fullmatch(r"\*3\*([12])#", code)
            if not m:
                raise ValueError(_("Simulator only knows * 3 * 1|2 #"))
            svc.sim_port.image[0x0E] = 0 if m.group(1) == "1" else 1
            return jsonify(ok=True)

    @app.get("/api/log/download")
    def log_download():
        text = "\n".join(f"{l.zeit}  {l.roh}  {svc.log_text(l)}".rstrip() for l in svc.log_lines) + "\n"
        return send_file(io.BytesIO(text.encode("utf-8")), mimetype="text/plain",
                         as_attachment=True, download_name="tk-gateway.log")

    # ------------------------------------------------------- import/export

    @app.get("/api/export/<fmt>")
    def export(fmt: str):
        if fmt not in ("json", "bin", "gtk", "gtb"):
            raise ValueError(_("Format must be json, bin, gtk or gtb"))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / f"tk-gateway.{fmt}"
            {"json": lambda: files.save_json(svc.image, path),
             "bin": lambda: files.save_bin(svc.image, path),
             "gtk": lambda: files.save_gtk(svc.image.config, path),
             "gtb": lambda: files.save_gtb(svc.image.phonebook, path)}[fmt]()
            data = path.read_bytes()
        return send_file(io.BytesIO(data), as_attachment=True, download_name=path.name,
                         mimetype="application/octet-stream")

    @app.post("/api/import")
    def import_():
        upload = request.files.get("datei")
        if not upload or not upload.filename:
            raise ValueError(_("No file selected"))
        suffix = Path(upload.filename).suffix.lower()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / f"upload{suffix}"
            upload.save(path)
            if suffix == ".json":
                svc.image = files.load_json(path)
            elif suffix == ".bin":
                svc.image = files.load_bin(path)
            elif suffix == ".gtk":
                svc.image.config = files.load_gtk(path)
            elif suffix == ".gtb":
                svc.image.phonebook = files.load_gtb(path)
            else:
                raise ValueError(_("Unknown file format (expected .json, .bin, .gtk or .gtb)"))
        return get_image()

    return app


def main(device: str | None = None, sim: bool = False, host: str = "127.0.0.1", port: int = 5000) -> None:
    app = create_app(device, sim)
    print(f"TK gateway commissioning: http://{host}:{port}/ (serial port: {device or 'none'})", flush=True)
    try:
        # one process, several threads: job and log state live in memory
        from waitress import serve
    except ImportError:
        app.run(host=host, port=port, threaded=True)
    else:
        serve(app, host=host, port=port, threads=8)
