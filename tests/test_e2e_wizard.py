"""Browser-Test des Assistenten "Klingeln anlernen" gegen den Simulator.

Only runs if Playwright (pip) and a Chromium are installed.
"""
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

sync_playwright = pytest.importorskip("playwright.sync_api").sync_playwright
CHROMIUM = shutil.which("chromium-browser") or shutil.which("chromium")
pytestmark = pytest.mark.skipif(not CHROMIUM, reason="Chromium not installed")
ROOT = Path(__file__).resolve().parents[1]
B = "http://127.0.0.1:5089"


def api(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(B + path, method=method, data=data, headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req))


def wait_job():
    for _ in range(100):
        if not api("GET", "/api/status")["job"]["busy"]:
            return
        time.sleep(0.1)


@pytest.fixture
def server():
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    srv = subprocess.Popen([sys.executable, "-m", "tks_gateway", "--sim", "web", "--http-port", "5089"],
                           cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            api("GET", "/api/status")
            break
        except Exception:
            time.sleep(0.1)
    yield
    srv.terminate()
    srv.wait()


def test_wizard_passiv_anlernen(server):
    # simulated device: entry 1 already knows call button 1A-2B-3C-4D-5E
    api("POST", "/api/gateway/read"); wait_job()
    api("PUT", "/api/phonebook/1", {"bezeichnung": "Müller EG", "nummer_v1": "0221555", "nummer_v2": "",
                                     "ab_v1": False, "ab_v2": False, "tuerstation": 1,
                                     "tastercode": "1A-2B-3C-4D-5E-00-00-00"})
    api("POST", "/api/gateway/write", {"part": "telefonbuch"}); wait_job()

    errors = []
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=CHROMIUM, args=["--no-sandbox"])
        pg = br.new_page(viewport={"width": 1280, "height": 900})
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.on("console", lambda m: m.type == "error" and errors.append(m.text))

        def row(code):
            return pg.locator(f'#wz-found tr[data-code^="{code}"]')

        pg.goto(B + "/#telefonbuch")
        pg.click("text=Learn call buttons …")
        pg.click("#wz-prepare")
        pg.wait_for_selector("#wz-c-read.ok", timeout=15000)
        pg.click("#wz-next")

        # the simulator rings at three door stations in turn
        pg.wait_for_function("document.querySelectorAll('#wz-found tbody tr').length >= 3", timeout=30000)
        assert "known: entry 1" in row("1A-2B").inner_text()
        row("CC-ED").locator("[data-f=name]").fill("Haustür")
        row("CC-ED").locator("[data-f=ts]").select_option("2")
        row("0F-22").locator("[data-f=ignore]").click()

        # further door calls must not discard the input
        before = row("1A-2B").locator(".count").inner_text()
        pg.wait_for_function(
            "b => document.querySelector('#wz-found tr[data-code^=\"1A-2B\"] .count').textContent !== b",
            arg=before, timeout=20000)
        assert row("CC-ED").locator("[data-f=name]").input_value() == "Haustür"

        pg.click("#wz-next")
        pg.wait_for_selector("#wz-summary li")
        summary = pg.inner_text("#wz-summary")
        assert "already assigned like this" in summary and "0F-22" not in summary

        pg.click("#wz-next")
        pg.wait_for_selector(".steps li.current[data-step='4']", timeout=20000)
        assert pg.inner_text("#wz-result").startswith("2 call button")
        pg.click("#wz-next")
        br.close()

    assert not api("GET", "/api/status")["log_active"]
    api("POST", "/api/gateway/read"); wait_job()
    got = {e["index"]: (e["bezeichnung"], e["tuerstation"], e["tastercode"])
           for e in api("GET", "/api/image")["telefonbuch"] if e["gefangen"]}
    assert got == {1: ("Müller EG", 1, "1A-2B-3C-4D-5E-00-00-00"),
                   2: ("Haustür", 2, "CC-ED-19-83-00-00-00-00")}
    assert not errors, errors


def test_tk_wizard_sammelruf(server):
    # initial state: direct line, one learned call button
    api("POST", "/api/gateway/read"); wait_job()
    cfg = api("GET", "/api/image")["konfiguration"]
    api("PUT", "/api/config", {**cfg, "anschlussart": "amt"})
    api("PUT", "/api/phonebook/1", {"bezeichnung": "Haustür", "nummer_v1": "", "nummer_v2": "", "ab_v1": False,
                                     "ab_v2": False, "tuerstation": 1, "tastercode": "CC-ED-19-83-00-00-00-00"})
    api("POST", "/api/gateway/write", {"part": "alles"}); wait_job()

    errors = []
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=CHROMIUM, args=["--no-sandbox"])
        pg = br.new_page(viewport={"width": 1280, "height": 900})
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(B + "/#konfiguration")
        pg.click("text=Connect to PBX …")
        pg.fill("#tk-own", "**1")
        pg.click("#tk-prepare")
        pg.wait_for_selector("#tk-c-read.ok", timeout=15000)
        assert pg.is_disabled("#tk-next")          # only after confirming the wiring
        pg.check("#tk-wired")
        pg.click("#tk-next")
        assert pg.input_value("#tk-group") == "**9"  # FRITZ!Box-Sammelruf vorbelegt
        pg.click("#tk-next")
        pg.fill("#tk-ring", "25")
        assert pg.is_visible("#tk-pin-warn")         # PIN 0000 -> Warnung
        pg.fill("#tk-pin", "4711")
        pg.click("#tk-next")
        summary = pg.inner_text("#tk-summary")
        assert "PBX extension" in summary and "direct line" in summary
        assert "**9" in summary and "immediate" in summary and "4711" in summary
        pg.click("#tk-next")
        pg.wait_for_selector(".steps li.current[data-step='5']", timeout=20000)
        assert "Saved" in pg.inner_text("#tk-result")
        assert "**1" in pg.inner_text("#tk-test-own")
        br.close()

    api("POST", "/api/gateway/read"); wait_job()
    c = api("GET", "/api/image")["konfiguration"]
    assert (c["anschlussart"], c["masterumleitung"], c["masterumleitungsnummer"], c["externe_rufzeit"], c["pin"]) == \
        ("nebenstelle", "sofort", "**9", "025", "4711")
    assert not errors, errors


def test_verbindungstest_telefonanlage(server):
    # device: PBX extension (factory setting), entry 1 knows call button 1A-2B-…, variant 1
    api("POST", "/api/gateway/read"); wait_job()
    api("PUT", "/api/phonebook/1", {"bezeichnung": "Haustür", "nummer_v1": "**9", "nummer_v2": "", "ab_v1": False,
                                     "ab_v2": False, "tuerstation": 1, "tastercode": "1A-2B-3C-4D-5E-00-00-00"})
    api("POST", "/api/gateway/write", {"part": "telefonbuch"}); wait_job()

    errors = []
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=CHROMIUM, args=["--no-sandbox"])
        pg = br.new_page(viewport={"width": 1280, "height": 900})
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(B + "/#konfiguration")
        pg.click("text=Test PBX …")

        # test 1 – without a call: failure with diagnosis
        pg.click("#tt1-start")
        pg.wait_for_selector("#tt1-run:not([hidden])", timeout=15000)
        pg.click("#tt1-check")
        pg.wait_for_selector("#tt1-result.bad", timeout=15000)
        assert "did not arrive" in pg.inner_text("#tt1-result")

        # test 1 – with (simulated) call and DTMF input: success + restore
        assert pg.inner_text("#tt1-code") == "* 3 * 2 #"
        api("POST", "/api/sim/dtmf", {"code": "*3*2#"})
        pg.click("#tt1-check")
        pg.wait_for_selector("#tt1-result.ok", timeout=15000)
        assert "Variant switched back to 1" in pg.inner_text("#tt1-result")

        # test 2 – simulator rings (E: 11 1A…) and dials (T: DIAL … - 0221123456)
        pg.click("#tt2-start")
        pg.wait_for_selector("#tt2-ask:not([hidden])", timeout=20000)
        dial = pg.inner_text("#tt2-c-dial")
        assert "0221123456" in dial and "entry 1" in dial
        assert "Haustür" in pg.inner_text("#tt2-c-known")
        pg.click("#tt2-yes")
        pg.wait_for_selector("#tt2-result.ok")
        pg.click("#tt-close")
        br.close()

    st = api("GET", "/api/status")
    assert not st["log_active"]
    api("POST", "/api/gateway/read"); wait_job()
    assert api("GET", "/api/image")["konfiguration"]["variante"] == 1
    assert not errors, errors
