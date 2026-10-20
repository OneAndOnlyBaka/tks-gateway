import time

import pytest

from tks_gateway import files
from tks_gateway.image import (
    IMAGE_SIZE,
    Anschlussart,
    Config,
    GatewayImage,
    Masterumleitung,
    PhonebookEntry,
    cut0,
)
from tks_gateway.logdecode import decode
from tks_gateway.protocol import Gateway, TransferError, build_block, checksum
from tks_gateway.simulator import SimulatedPort


def sample_image() -> GatewayImage:
    img = GatewayImage.factory_defaults()
    img.config = Config(
        anschlussart=Anschlussart.AMT,
        lokale_rufzeit="045",
        externe_rufzeit="120",
        tuergespraechszeit="090",
        variante=2,
        mithoeren=True,
        pin="4711",
        masterumleitung=Masterumleitung.SOFORT,
        master_anrufbeantworter=True,
        masterumleitungsnummer="01701234567",
    )
    img.phonebook[0] = PhonebookEntry(
        bezeichnung="Müller EG", nummer_v1="0221555", nummer_v2="0171999", ab_v2=True,
        tuerstation=3, tastercode=bytes([0x1A, 0x2B, 0x3C, 0x4D, 0x5E, 0, 0, 0]),
    )
    img.phonebook[49] = PhonebookEntry(bezeichnung="Letzter", nummer_v1="12")
    return img


# ------------------------------------------------------------ Speicherabbild


def test_layout_offsets():
    raw = sample_image().to_bytes()
    assert len(raw) == IMAGE_SIZE
    assert raw[0x01] == 0  # Amtsanschluss
    assert raw[0x02:0x06] == b"045\x00"
    assert raw[0x10:0x15] == b"4711\x00"
    assert raw[0x15] == 2
    assert raw[0x40:0x41] == b"A"
    assert raw[0x41:0x4C] == b"01701234567"
    e = raw[0x100:0x140]
    assert e[:8] == bytes([0x1A, 0x2B, 0x3C, 0x4D, 0x5E, 0, 0, 0])
    assert e[8] == ord("3") and e[10] == ord(" ") and e[36] == ord("A")
    assert e[11:18] == b"0221555"
    assert raw[0x1000:0x1009] == "Müller EG".encode("latin-1")


def test_roundtrip_and_unknown_bytes_preserved():
    raw = bytearray(sample_image().to_bytes())
    raw[0x00] = 0x5A
    raw[0x20:0x24] = b"\xde\xad\xbe\xef"  # unbekannter Konfigurationsbereich
    img = GatewayImage.from_bytes(bytes(raw))
    assert img.config == sample_image().config
    assert img.phonebook[0] == sample_image().phonebook[0]
    assert img.phonebook[0].gefangen and not img.phonebook[1].gefangen
    img.config.pin = "1234"
    out = img.with_config()
    assert out[0x00] == 0x5A and out[0x20:0x24] == b"\xde\xad\xbe\xef"
    assert out[0x10:0x14] == b"1234"
    assert out[0x100:] == bytes(raw[0x100:])


def test_device_patterns_roundtrip_byte_exact():
    """Patterns from a real device (firmware 1.26): special characters in numbers,
    door station '0' (0x30) and AB flag ' ' in empty entries."""
    raw = bytearray(IMAGE_SIZE)
    raw[0x02:0x0E] = b"030\x00030\x00060\x00"
    raw[0x10:0x14] = b"0000"
    raw[0x40:0x48] = b" 1234567"
    for i in range(50):
        e = 0x100 + 64 * i
        raw[e + 8] = ord("0")
        raw[e + 10] = raw[e + 36] = ord(" ")
    raw[0x100:0x104] = bytes([0xCC, 0xED, 0x19, 0x83])
    raw[0x108] = ord("1")
    raw[0x10B:0x10E] = raw[0x125:0x128] = b"**9"
    raw[0x1000:0x1005] = b"taste"
    img = GatewayImage.from_bytes(bytes(raw))
    img.validate()  # "**9" is allowed
    assert img.phonebook[0].nummer_v1 == "**9" and img.phonebook[0].tuerstation == 1
    assert img.to_bytes() == img.with_config() == img.with_phonebook() == bytes(raw)


def test_dialstring_rules():
    e = PhonebookEntry(nummer_v1="0P0221F555f*#")  # Sonderzeichen laut Handbuch
    e.validate()
    with pytest.raises(ValueError, match="max. 24"):
        PhonebookEntry(nummer_v1="1" * 25).validate()
    with pytest.raises(ValueError, match="120"):
        Config(tuergespraechszeit="121").validate()


def test_backup_export_never_fails(tmp_path):
    img = GatewayImage.factory_defaults()
    img.phonebook[0].nummer_v1 = "12x"  # invalid, e.g. from a foreign source
    files.save_bin(img, tmp_path / "s.bin")
    assert (tmp_path / "s.bin").stat().st_size == IMAGE_SIZE


def test_cut_semantics():
    assert cut0(b"0221\xff\xff") == "0221"
    assert cut0(b"0221A\x00") == "0221"


def test_validation():
    img = sample_image()
    img.config.lokale_rufzeit = "121"
    with pytest.raises(ValueError, match="120"):
        img.validate()
    img = sample_image()
    img.config.masterumleitung = Masterumleitung.VERZOEGERT
    with pytest.raises(ValueError, match="delayed master redirect"):
        img.validate()


# -------------------------------------------------------------------- XMODEM


def test_block_format():
    blk = build_block(1, b"abc")
    assert blk[:3] == b"\x01\x01\xfe" and len(blk) == 132
    assert blk[6] == 0x1A and blk[-1] == checksum(blk[3:-1])


def test_read_write_image_via_simulator():
    port = SimulatedPort(sample_image().to_bytes())
    gw = Gateway(port, timeout=2)
    raw = gw.read_image()
    assert GatewayImage.from_bytes(raw).config.pin == "4711"
    img = GatewayImage.from_bytes(raw)
    img.config.pin = "9999"
    gw.write_image(img.with_config())
    assert bytes(port.image[0x10:0x14]) == b"9999"
    assert port.commands == ["u", "d"]


def test_corrupt_block_is_repeated():
    port = SimulatedPort(sample_image().to_bytes(), corrupt_blocks={2, 30})
    raw = Gateway(port, timeout=2).read_image()
    assert raw == sample_image().to_bytes()


def test_corrupt_block_three_times_aborts():
    port = SimulatedPort(corrupt_blocks={5})
    gw = Gateway(port, timeout=2)
    orig = port._send_block

    def always_corrupt():
        port.corrupt_blocks.add(5)
        orig()

    port._send_block = always_corrupt
    with pytest.raises(TransferError):
        gw.read_image()


def test_firmware_and_version():
    port = SimulatedPort()
    gw = Gateway(port, timeout=2)
    assert gw.read_version().has_bustreiber
    data = bytes(range(256)) * 3 + b"xyz"
    gw.upload_firmware(data)
    assert port.firmware.rstrip(b"\x1a") == data
    gw.upload_bustreiber(b":020000040000FA\r\n")
    assert port.bustreiber.startswith(b":020000040000FA")


def test_bootloader_only_sends_s_without_cr():
    port = SimulatedPort(version="Bootlader V1.0")
    gw = Gateway(port, timeout=2)
    gw.upload_firmware(b"\x02" * 10)
    assert port.firmware.startswith(b"\x02" * 10)
    gw.reset_bootloader()
    assert port.commands == ["i", "s", "r"]


def test_commands_are_letter_plus_cr():
    port = SimulatedPort()
    sent = []
    orig = port.write
    port.write = lambda data: (sent.append(bytes(data)), orig(data))[1]
    Gateway(port, timeout=2).read_version()
    assert sent[0] == b"i\r"


def test_ruftaste():
    port = SimulatedPort()
    code = Gateway(port, timeout=2).fetch_ruftaste(5, 3)
    assert code == bytes([0x1A, 0x2B, 0x3C, 0x4D, 0x5E, 0, 0, 0])
    assert port.commands[-1] == "z305"


def test_log_lines():
    port = SimulatedPort()
    gw = Gateway(port, timeout=2)
    gw.log_on()
    # formats as output by the firmware (0x0BB1, 0x0C65, 0x14F4)
    port.emit_log("E: 11 1A 2B 3C 4D 5E 00 00 00 ")
    port.emit_log("S: 42 1A 2B 3C FF 00 00 00 00 ")
    port.emit_log("T: DIAL  03 01 01 - 0221123456")
    lines = []
    for line in gw.iter_log(lambda: len(lines) >= 3):
        lines.append(line)
    assert decode(lines[0]) == "Gateway receives: door call from 1A 2B 3C sub-address 4D"
    assert decode(lines[1]) == "Gateway sends: switching function ON at 1A 2B 3C"
    assert decode(lines[2]) == ("Gateway calls: from phonebook index 3 with variant 2 active "
                                "an external subscriber with number: 0221123456 "
                                "with answering machine function active")


def test_validation_messages_with_placeholders():
    # placeholders named like the parameter of _() ({text}) must work
    with pytest.raises(ValueError, match="only digits, \\*, # and P, F, f allowed \\('1x'\\)"):
        PhonebookEntry(nummer_v1="1x").validate()
    with pytest.raises(ValueError, match="8 hex bytes"):
        PhonebookEntry.parse_tastercode("12-34")


def test_german_messages():
    from tks_gateway.i18n import set_lang

    set_lang("de")
    try:
        assert decode("E: 11 1A 2B 3C 4D 5E 00 00 00 ") == "Gateway empfängt: Türruf von 1A 2B 3C Subadresse 4D"
        with pytest.raises(ValueError, match="maximal 24"):
            PhonebookEntry(nummer_v1="1" * 25).validate()
    finally:
        set_lang("en")


def test_version_without_bustreiber_has_no_crlf():
    port = SimulatedPort(version="Gira TK Koppler Version 01.26 ")
    v = Gateway(port, timeout=2).read_version(timeout=0.5)
    assert v.text == "Gira TK Koppler Version 01.26" and not v.has_bustreiber


# --------------------------------------------------------------- Dateien


def test_files_roundtrip(tmp_path):
    img = sample_image()
    files.save_json(img, tmp_path / "a.json")
    back = files.load_json(tmp_path / "a.json")
    assert back.config == img.config and back.phonebook == img.phonebook

    files.save_gtk(img.config, tmp_path / "a.gtk")
    assert files.load_gtk(tmp_path / "a.gtk") == img.config

    files.save_gtb(img.phonebook, tmp_path / "a.gtb")
    assert files.load_gtb(tmp_path / "a.gtb") == img.phonebook


# ------------------------------------------------------------------- Web


def wait_job(client):
    for _ in range(500):  # up to 10 s (version timeout 3 s + quiet + pauses)
        st = client.get("/api/status").get_json()
        if not st["job"]["busy"]:
            return st["job"]
        time.sleep(0.02)
    raise AssertionError("job hangs")


def test_web_api():
    from tks_gateway.web import create_app

    app = create_app(sim=True)
    c = app.test_client()
    assert c.get("/").status_code == 200

    assert c.post("/api/gateway/read").status_code == 202
    assert wait_job(c)["error"] == ""

    cfg = c.get("/api/image").get_json()["konfiguration"]
    cfg["pin"] = "1357"
    assert c.put("/api/config", json=cfg).status_code == 200
    assert c.put("/api/config", json={**cfg, "pin": "12"}).status_code == 400

    entry = {"bezeichnung": "Test", "nummer_v1": "0123", "nummer_v2": "", "ab_v1": False,
             "ab_v2": False, "tuerstation": 2, "tastercode": "00-00-00-00-00-00-00-00"}
    assert c.put("/api/phonebook/5", json=entry).status_code == 200
    c.post("/api/gateway/ruftaste/5")
    assert wait_job(c)["error"] == ""

    c.post("/api/gateway/write", json={"part": "alles"})
    assert wait_job(c)["error"] == ""
    sim = app.extensions["tks_gateway"].sim_port
    stored = GatewayImage.from_bytes(bytes(sim.image))
    assert stored.config.pin == "1357"
    assert stored.phonebook[4].bezeichnung == "Test" and stored.phonebook[4].gefangen

    assert c.get("/api/export/gtb").status_code == 200


def test_web_unsaved_call_buttons():
    from tks_gateway.web import create_app

    app = create_app(sim=True)
    c = app.test_client()
    c.post("/api/gateway/read")
    assert wait_job(c)["error"] == ""
    unsaved = lambda: c.get("/api/status").get_json()["unsaved_buttons"]
    assert unsaved() == []

    entry = {"bezeichnung": "", "nummer_v1": "", "nummer_v2": "", "ab_v1": False, "ab_v2": False,
             "tuerstation": 1, "tastercode": "00-00-00-00-00-00-00-00"}
    c.put("/api/phonebook/3", json=entry)
    assert unsaved() == []  # door station without a button is irrelevant
    entry["tastercode"] = "11-22-33-44-55-00-00-00"
    assert c.put("/api/phonebook/3", json=entry).status_code == 200
    assert unsaved() == [3]

    # saving only the configuration keeps the assignment pending (and in the working copy)
    c.post("/api/gateway/write", json={"part": "konfiguration"})
    assert wait_job(c)["error"] == ""
    assert unsaved() == [3]
    assert c.get("/api/image").get_json()["telefonbuch"][2]["tastercode"].startswith("11-22")

    c.post("/api/gateway/write", json={"part": "telefonbuch"})
    assert wait_job(c)["error"] == ""
    assert unsaved() == []

    # the page shows the notice in the log tab
    html = c.get("/").get_data(as_text=True)
    assert html.count("data-unsaved") == 2 and "Not saved yet" in html


def test_web_help_tab():
    from tks_gateway.web import create_app

    c = create_app(sim=True).test_client()
    en = c.get("/").get_data(as_text=True)
    assert 'data-tab="help"' in en and "Quick start" in en and "Learn call buttons" in en
    assert en.count('class="mermaid"') == 3 and 'id="h-connect"' in en and 'class="wiring"' in en
    c.set_cookie("lang", "de")
    de = c.get("/").get_data(as_text=True)
    assert "Schnellstart" in de and de.count('class="mermaid"') == 3 and "RJ10" in de
    # the help is about operating the tool – system background lives in docs/USER_GUIDE.md
    assert "Asterisk" not in en and "Asterisk" not in de
    js = c.get("/static/vendor/mermaid.min.js")
    assert js.status_code == 200 and len(js.data) > 1_000_000


def test_stale_log_mode_after_restart():
    """Gateway still logging after the host restarted: answers must not be garbled."""
    from tks_gateway.protocol import strip_log
    from tks_gateway.simulator import SimulatedPort

    port = SimulatedPort()
    Gateway(port).log_on()  # previous session, never switched off
    assert port.logging

    # read_version copes with log output glued to the version text
    v = Gateway(port).read_version()
    assert v.has_bustreiber and v.koppler == "01.26" and v.pic == "0101" and "S:" not in v.text

    # z: the "S: 05 …" log line is not taken as the call information
    code = Gateway(port).fetch_ruftaste(5, 1)
    assert any(code)

    # quiet() switches the log off and reports it
    gw = Gateway(port)
    assert gw.quiet() is False or not port.logging
    assert not port.logging
    assert strip_log("Gira TK Koppler Version 01.26 S: 90 00") == "Gira TK Koppler Version 01.26"
    assert strip_log("E: 11 01 02 03 04 05 00 00 00") == ""


def test_web_recovers_from_stale_log_mode():
    from tks_gateway.web import create_app

    app = create_app(sim=True)
    svc = app.extensions["tks_gateway"]
    svc.sim_port.logging = True  # as if the container restarted while logging
    c = app.test_client()
    c.post("/api/gateway/version")
    assert wait_job(c)["error"] == ""
    st = c.get("/api/status").get_json()
    assert st["version"]["has_bustreiber"] and st["version"]["pic"] == "0101"
    assert not svc.sim_port.logging


def test_licenses_and_sbom_are_generated_from_installed_packages():
    import importlib.metadata as md

    from tks_gateway.licenses import components, sbom
    from tks_gateway.web import create_app

    comps = {c.name.lower(): c for c in components()}
    assert "tks-gateway" in comps and comps["tks-gateway"].license == "MIT" and comps["tks-gateway"].texts
    for dep in ("flask", "pyserial", "werkzeug", "jinja2", "markupsafe"):
        assert dep in comps and comps[dep].version == md.version(dep)
    m = comps["mermaid"]
    assert m.kind == "javascript" and m.license == "MIT" and m.texts and len(m.sha256) == 64

    doc = sbom()
    assert doc["bomFormat"] == "CycloneDX" and doc["specVersion"] == "1.5"
    root = doc["metadata"]["component"]
    assert root["name"] == "tks-gateway" and root["author"] == "OneAndOnlyBaka"
    assert root["externalReferences"] == [{"type": "vcs", "url": "https://github.com/OneAndOnlyBaka/tks-gateway"}]
    refs = {c["bom-ref"] for c in doc["components"]} | {doc["metadata"]["component"]["bom-ref"]}
    assert all(d["ref"] in refs and set(d["dependsOn"]) <= refs for d in doc["dependencies"])
    assert f"pkg:pypi/flask@{md.version('flask')}" in refs

    c = create_app(sim=True).test_client()
    data = c.get("/api/licenses").get_json()["components"]
    assert data[0]["name"] == "tks-gateway"
    r = c.get("/api/sbom")
    assert r.status_code == 200 and r.json["bomFormat"] == "CycloneDX"
    assert "attachment" in r.headers["Content-Disposition"]
    assert 'data-tab="licenses"' in c.get("/").get_data(as_text=True)


def test_cli_sbom(tmp_path, capsys):
    import json

    from tks_gateway.cli import main

    out = tmp_path / "sbom.json"
    main(["sbom", "-o", str(out)])
    assert json.loads(out.read_text())["bomFormat"] == "CycloneDX"
    main(["licenses"])
    assert "pyserial" in capsys.readouterr().out


def test_web_language_cookie():
    from tks_gateway.web import create_app

    c = create_app(sim=True).test_client()
    assert b"Load from gateway" in c.get("/").data  # English by default
    c.set_cookie("lang", "de")
    page = c.get("/").data.decode()
    assert 'lang="de"' in page and "Aus Gateway laden" in page and '"js.saving": "Speichere' in page
    err = c.put("/api/config", json={"pin": "12"}).get_json()["error"]
    assert "4-stellige PIN" in err


def test_web_version_and_log_capture():
    from tks_gateway.web import create_app

    app = create_app(sim=True)
    c = app.test_client()
    c.post("/api/gateway/version")
    assert wait_job(c)["error"] == ""
    v = c.get("/api/status").get_json()["version"]
    assert v["koppler"] == "01.26" and v["pic"] == "0101" and v["has_bustreiber"]

    svc = app.extensions["tks_gateway"]
    svc._add_log("E: 11 1A 2B 3C 4D 5E 00 00 00 ", "x")
    svc._add_log("S: 21 1A 2B 3C 4D 00 00 00 00 ", "y")
    lines = c.get("/api/log").get_json()["lines"]
    assert lines[0]["typ"] == "E" and lines[0]["code"] == "11"
    assert lines[0]["tuerruf"] == "1A-2B-3C-4D-5E-00-00-00"
    assert lines[1]["typ"] == "S" and lines[1]["tuerruf"] == ""

    c.post("/api/gateway/bootloader-reset")
    job = wait_job(c)
    assert "bootloader" in job["error"]  # firmware running -> no response, understandable message


def test_web_log_ping_and_line_split():
    from tks_gateway.web import create_app

    app = create_app(sim=True)
    c = app.test_client()
    assert c.post("/api/log/ping").status_code == 400  # log not running yet
    c.post("/api/log/start")
    for _ in range(50):
        if c.get("/api/status").get_json()["log_active"]:
            break
        time.sleep(0.05)
    c.post("/api/log/ping")
    lines = []
    for _ in range(60):
        lines = c.get("/api/log").get_json()["lines"]
        if any(l["roh"].startswith("PIC Release") for l in lines):
            break
        time.sleep(0.05)
    c.post("/api/log/stop")
    roh = [l["roh"] for l in lines]
    # "…Version 01.26 S: 90 …" is split into version text + telegram
    assert "Gira TK Koppler Version 01.26" in roh
    tel = next(l for l in lines if l["roh"].startswith("S: 90"))
    assert tel["typ"] == "S" and tel["code"] == "90"
    assert any(r.startswith("PIC Release 0101") for r in roh)
