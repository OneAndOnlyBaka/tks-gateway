"""Translations: English is the source language, German the translation.

* ``_(text, **kw)`` translates messages created in Python code (validation,
  errors, job status, log decoding). The active language lives in a
  ``ContextVar`` so it is correct per HTTP request and inside background jobs.
* ``ui(key)`` returns UI texts for the web template and the JavaScript
  catalog (see ``ui_texts.py``).
"""

from __future__ import annotations

import contextvars
import os

LANGS = ("en", "de")
DEFAULT_LANG = os.environ.get("TKS_GATEWAY_LANG", "en") if os.environ.get("TKS_GATEWAY_LANG") in LANGS else "en"

_lang: contextvars.ContextVar[str] = contextvars.ContextVar("lang", default=DEFAULT_LANG)


def set_lang(lang: str | None) -> None:
    _lang.set(lang if lang in LANGS else DEFAULT_LANG)


def get_lang() -> str:
    return _lang.get()


def _(msg: str, /, **kw) -> str:
    """Translate an English message into the active language and format it.

    ``msg`` is positional-only so placeholders may use any name (e.g. ``{text}``).
    """
    if get_lang() == "de":
        msg = MESSAGES_DE.get(msg, msg)
    return msg.format(**kw) if kw else msg


def ui(key: str, lang: str | None = None) -> str:
    from .ui_texts import UI

    en, de = UI[key]
    return de if (lang or get_lang()) == "de" else en


def js_catalog(lang: str | None = None) -> dict[str, str]:
    from .ui_texts import UI

    return {k: ui(k, lang) for k in UI if k.startswith("js.")}


# --------------------------------------------------------------- messages
# English source text -> German translation (placeholders in {braces}).

MESSAGES_DE: dict[str, str] = {
    # image.py – validation
    "{text!r} is longer than {n} characters": "{text!r} ist länger als {n} Zeichen",
    "{what}: digits only ({text!r})": "{what}: bitte nur Ziffern eingeben ({text!r})",
    "{what}: only digits, *, # and P, F, f allowed ({text!r})": "{what}: nur Ziffern, *, # sowie P, F, f erlaubt ({text!r})",
    "{what}: max. {n} characters": "{what}: maximal {n} Zeichen",
    "{what}: value missing": "{what}: Wert fehlt",
    "{what}: max. 4 digits": "{what}: maximal 4 Stellen",
    "{what}: maximum value is 120 seconds": "{what}: maximaler Wert sind 120 Sekunden",
    "Enter a 4-digit PIN": "Geben Sie eine 4-stellige PIN ein",
    "Variant must be 1 or 2": "Variante muss 1 oder 2 sein",
    "Please select a door station between 1 and 9": "Bitte wählen Sie eine Türstation zwischen 1 und 9 aus",
    "Name: max. {n} characters": "Bezeichnung: maximal {n} Zeichen",
    "Button code must be 8 bytes long": "Tastercode muss 8 Byte lang sein",
    "Button code {text!r}: 8 hex bytes expected": "Tastercode {text!r}: 8 Hex-Bytes erwartet",
    "Phonebook entry {i}: {err}": "Telefonbucheintrag {i}: {err}",
    "At least one phonebook entry has the answering machine function enabled. "
    "A delayed master redirect is not possible with it.":
        "Sie haben mindestens in einem Telefonbucheintrag die Anrufbeantworterfunktion aktiviert. "
        "Eine verzögerte Masterrufumleitung ist damit nicht möglich.",
    "Phonebook must have {n} entries": "Telefonbuch muss {n} Einträge haben",
    "Image too short: {n} instead of {size} bytes": "Abbild zu kurz: {n} statt {size} Byte",
    "Phone number": "Telefonnummer",
    "Master redirect number": "Masterumleitungsnummer",
    "local ring time": "Lokale Rufzeit",
    "external ring time": "Externe Rufzeit",
    "door talk time": "Türgesprächszeit",
    # protocol.py
    "no response (received so far: {buf!r})": "keine Antwort (bisher empfangen: {buf!r})",
    "no data to transfer": "keine Daten zum Übertragen",
    "Gateway does not request data (no NAK received)": "Gateway fordert keine Daten an (kein NAK empfangen)",
    "Transfer aborted by the gateway": "Übertragung vom Gateway abgebrochen",
    "no acknowledgement for block {n}": "keine Quittung für Block {n}",
    "block {n} not acknowledged after {tries} attempts": "Block {n} nach {tries} Versuchen nicht quittiert",
    "no acknowledgement for end of transfer": "keine Quittung für Übertragungsende",
    "end of transfer not acknowledged": "Übertragungsende nicht quittiert",
    "Gateway does not send any data": "Gateway sendet keine Daten",
    "Timeout while receiving block {n}": "Timeout beim Empfang von Block {n}",
    "Transfer aborted due to transmission errors": "Übertragung wegen Übertragungsfehlern abgebrochen",
    "only {n} of {size} bytes received": "nur {n} von {size} Byte empfangen",
    "Image must be {size} bytes, not {n}": "Abbild muss {size} Byte groß sein, nicht {n}",
    "Please assign a valid door station number (1-9)": "Bitte vergeben Sie eine gültige Türstationsnummer (1-9)",
    "Phonebook index must be between 1 and 50": "Telefonbuchindex muss zwischen 1 und 50 liegen",
    "No call information received. Is the control unit in programming mode, was the call button "
    "at the door station pressed and is the bus connected?":
        "Keine Rufinformation erhalten. Ist das Steuergerät im Programmiermodus und wurde die Ruftaste "
        "an der Türstation gedrückt? Ist der Bus angeschlossen?",
    "Call information invalid: {line!r}": "Rufinformationen fehlerhaft: {line!r}",
    # web.py
    "No serial port selected (settings)": "Keine Schnittstelle gewählt (Einstellungen)",
    "Serial port {dev} not available or busy: {err}": "COM-Port {dev} nicht vorhanden oder belegt: {err}",
    "The serial port is busy. Other parts of the program are using it. Stop logging if necessary.":
        "Die Schnittstelle ist belegt. Andere Programmteile greifen gerade auf die Schnittstelle zu. "
        "Beenden Sie ggf. die Logfunktion.",
    "The serial port is busy": "Die Schnittstelle ist belegt",
    "Logging not possible, the serial port is busy": "Loggen nicht möglich, da die Schnittstelle belegt ist",
    "Logging is not running": "Das Loggen läuft nicht",
    "Logging started": "Loggen gestartet",
    "write a CycloneDX SBOM of this installation (JSON)":
        "CycloneDX-SBOM dieser Installation schreiben (JSON)",
    "file (default: standard output)": "Datei (Standard: Standardausgabe)",
    "list the third-party components and their licenses": "Fremdkomponenten und ihre Lizenzen auflisten",
    "SBOM written to {path}": "SBOM nach {path} geschrieben",
    "The installed package contains no license file – see the project page.":
        "Das installierte Paket enthält keine Lizenzdatei – siehe Projektseite.",
    "The minified bundle also contains its npm dependencies (listed with their declared version ranges); "
    "their licenses are documented by the respective projects.":
        "Das minifizierte Paket enthält auch seine npm-Abhängigkeiten (mit den deklarierten Versionsbereichen "
        "aufgeführt); deren Lizenzen dokumentieren die jeweiligen Projekte.",
    "The gateway was still logging (e.g. after a restart) – logging switched off":
        "Das Gateway hat noch geloggt (z. B. nach einem Neustart) – Loggen ausgeschaltet",
    "Logging stopped": "Loggen gestoppt",
    "Error: {err}": "Fehler: {err}",
    "{name} …": "{name} …",
    "{name} failed": "{name} fehlgeschlagen",
    "Read firmware version": "Firmwareversion auslesen",
    "Load from gateway": "Aus Gateway laden",
    "Save to gateway": "In Gateway speichern",
    "Assign call button": "Ruftaste zuordnen",
    "Bootloader reset": "Bootlader-Reset",
    "Transfer bus driver": "Bustreiber übertragen",
    "Transfer firmware": "Firmware übertragen",
    "No response. Please check the connection and pinout (swap TX/RX if needed) and power the TK gateway.":
        "Keine Antwort. Bitte Verbindung und Pinbelegung prüfen (TX/RX ggf. tauschen) und das TK-Gateway versorgen.",
    "The TK gateway only has a bootloader. Please install a firmware!":
        "Das TK-Gateway besitzt nur einen Bootlader. Bitte installieren Sie eine Firmware!",
    "The TK gateway has no bus driver. Please install a bus driver firmware!":
        "Das TK-Gateway besitzt keinen Bustreiber. Bitte installieren Sie eine Bustreiber-Firmware!",
    "Firmware version read successfully: {v}": "Firmwareversion erfolgreich ausgelesen: {v}",
    "Configuration and phonebook read successfully": "Konfiguration und Telefonbuch erfolgreich ausgelesen",
    "Configuration transferred successfully": "Konfiguration erfolgreich übertragen",
    "Phonebook transferred successfully": "Telefonbuch erfolgreich übertragen",
    "Configuration and phonebook transferred successfully": "Konfiguration und Telefonbuch erfolgreich übertragen",
    "part must be konfiguration, telefonbuch or alles": "part muss konfiguration, telefonbuch oder alles sein",
    "Please assign a valid door station number (1-9) to the selected phonebook entry":
        "Bitte vergeben Sie im Telefonbuch für den markierten Eintrag eine gültige Türstationsnummer (1-9)",
    "Call learned successfully ({code}) and saved in the gateway":
        "Ruf erfolgreich eingelernt ({code}) und im Gateway gespeichert",
    "No response after the reset. The reset only works when the gateway is in the bootloader – otherwise power-cycle it.":
        "Keine Antwort nach dem Reset. Der Reset wirkt nur, wenn das Gateway im Bootlader steht – sonst Spannungsreset durchführen.",
    "Bootloader reset: {v}": "Bootlader zurückgesetzt: {v}",
    "No file selected": "Keine Datei ausgewählt",
    "Bus driver transferred successfully": "Bustreiber erfolgreich übertragen",
    "Firmware transferred successfully. The TK gateway has restarted.":
        "Firmware erfolgreich übertragen. Das TK-Gateway wurde neu gestartet.",
    "Index must be between 1 and 50": "Index muss zwischen 1 und 50 liegen",
    "Format must be json, bin, gtk or gtb": "Format muss json, bin, gtk oder gtb sein",
    "Unknown file format (expected .json, .bin, .gtk or .gtb)":
        "Unbekanntes Dateiformat (erwartet .json, .bin, .gtk oder .gtb)",
    "Simulator only knows * 3 * 1|2 #": "Simulator kennt nur * 3 * 1|2 #",
    "unknown configuration parameter {key!r}": "unbekannter Konfigurationsparameter {key!r}",
    # cli.py
    "Please specify the serial port with --port (e.g. --port /dev/ttyUSB0 or COM1)":
        "Bitte die Schnittstelle mit --port angeben (z. B. --port /dev/ttyUSB0 oder COM1)",
    "Unknown file format: {path} (expected .json, .bin, .gtk or .gtb)":
        "Unbekanntes Dateiformat: {path} (erwartet .json, .bin, .gtk oder .gtb)",
    "Note: the TK gateway only has a bootloader. Please install a firmware.":
        "Hinweis: Das TK-Gateway besitzt nur einen Bootlader. Bitte Firmware installieren.",
    "Note: the TK gateway has no bus driver. Please install a bus driver firmware.":
        "Hinweis: Das TK-Gateway besitzt keinen Bustreiber. Bitte Bustreiber-Firmware installieren.",
    "Saved: {path}": "Gespeichert: {path}",
    "Transfer successful. The TK gateway stores the data.": "Übertragung erfolgreich. Das TK-Gateway speichert die Daten.",
    "Configuration transferred successfully.": "Konfiguration erfolgreich übertragen.",
    "Configuration reset to factory settings.": "Konfiguration auf Werkseinstellungen zurückgesetzt.",
    "Call learned successfully: {code}": "Ruf erfolgreich eingelernt: {code}",
    "Phonebook transferred successfully.": "Telefonbuch erfolgreich übertragen.",
    "No response. The reset only works when the gateway is in the bootloader; with running firmware please "
    "power-cycle it.":
        "Keine Antwort. Der Reset wirkt nur, wenn das Gateway im Bootloader steht; bei laufender Firmware bitte "
        "Spannungsreset durchführen.",
    "Bus driver transferred successfully.": "Bustreiber erfolgreich übertragen.",
    "Firmware transferred successfully. The TK gateway restarts, please wait approx. 5 seconds.":
        "Firmware erfolgreich übertragen. Das TK-Gateway startet neu, bitte ca. 5 Sekunden warten.",
    "Logging started (Ctrl+C to stop)": "Loggen gestartet (Strg+C zum Beenden)",
    "Commissioning of the Gira TK gateway 1290 00 (re-implementation of software V1.01)":
        "Inbetriebnahme des Gira TK-Gateway 1290 00 (Nachbau der Software V1.01)",
    "serial port, e.g. /dev/ttyUSB0 or COM1 (default: $TKS_GATEWAY_PORT)":
        "serielle Schnittstelle, z. B. /dev/ttyUSB0 oder COM1 (Standard: $TKS_GATEWAY_PORT)",
    "simulated gateway instead of a real serial port": "simuliertes Gateway statt echter Schnittstelle",
    "language of messages (default: en or $TKS_GATEWAY_LANG)": "Sprache der Meldungen (Standard: en oder $TKS_GATEWAY_LANG)",
    "list available serial ports": "verfügbare Schnittstellen auflisten",
    "start the web UI": "Web-Oberfläche starten",
    "address (default: local only)": "Adresse (Standard: nur lokal)",
    "read the firmware version": "Firmwarestand auslesen",
    "load configuration and phonebook from the gateway": "Konfiguration und Telefonbuch aus dem Gateway laden",
    "file (.json, .bin, .gtk, .gtb); otherwise display": "Datei (.json, .bin, .gtk, .gtb); sonst Anzeige",
    "display a file": "Datei anzeigen",
    "save a file to the gateway": "Datei in das Gateway speichern",
    ".json/.bin (complete), .gtk (configuration) or .gtb (phonebook)":
        ".json/.bin (komplett), .gtk (Konfiguration) oder .gtb (Telefonbuch)",
    "transfer only this part": "nur diesen Bereich übertragen",
    "change single configuration parameters": "einzelne Konfigurationsparameter ändern",
    "answering machine function of the master redirect": "Anrufbeantworterfunktion der Masterumleitung",
    "reset the configuration to factory settings": "Konfiguration auf Werkseinstellung setzen",
    "edit a phonebook entry": "Telefonbucheintrag bearbeiten",
    "phone number variant 1": "Telefonnummer Variante 1",
    "phone number variant 2": "Telefonnummer Variante 2",
    "assign the call button pressed last at the door station": "zuletzt gedrückte Ruftaste der Türstation zuordnen",
    "assign a call button to a phonebook entry, print the button code":
        "Ruftaste einem Telefonbucheintrag zuordnen, Tastercode ausgeben",
    "restart the bootloader (hidden function of the original)": "Bootloader neu starten (versteckte Funktion des Originals)",
    "transfer firmware (.tsk) or bus driver (.hex)": "Firmware (.tsk) oder Bustreiber (.hex) übertragen",
    "file is bus driver firmware (PIC, .hex)": "Datei ist Bustreiber-Firmware (PIC, .hex)",
    "capture the bus communication": "Buskommunikation mitschneiden",
    "additionally write to a file": "zusätzlich in Datei schreiben",
    # logdecode.py
    "Gateway sends: ": "Gateway sendet: ",
    "Gateway receives: ": "Gateway empfängt: ",
    "Gateway calls: ": "Gateway ruft: ",
    "internal call to ": "Internruf an ",
    "door conversation start with ": "Türgesprächsbeginn mit ",
    "internal conversation start with ": "Interngesprächsbeginn mit ",
    "end of conversation with ": "Gesprächsende mit ",
    "open door at ": "Tür öffnen an ",
    "switching function ON at ": "Schaltfunktion EIN an ",
    "switching function OFF at ": "Schaltfunktion AUS an ",
    "bus driver version request (PIC)": "Abfrage Bustreiber-Version (PIC)",
    "request call button for entry {n}": "Ruftaste anfragen für Eintrag {n}",
    "request call button": "Ruftaste anfragen",
    "test device mode ON": "Prüfgerätemodus EIN",
    "test device mode OFF": "Prüfgerätemodus AUS",
    "audio input TLN ON": "Audioeingang TLN EIN",
    "audio input TLN OFF": "Audioeingang TLN AUS",
    "bus transmitter ON": "Sendestufe an Bus EIN",
    "bus transmitter OFF": "Sendestufe an Bus AUS",
    "system reset": "Reset des Systems",
    "incoming call is known in the phonebook ": "Eingehender Ruf ist im Tel.Buch bekannt ",
    "end of conversation from ": "Gesprächsende von ",
    "door call from ": "Türruf von ",
    "internal call from ": "Internruf von ",
    "door call answered by ": "Türrufannahme von ",
    "internal call answered by ": "Internrufannahme von ",
    "system programming ON": "Systemprogrammierung EIN",
    "system programming OFF": "Systemprogrammierung AUS",
    "actuator programming ON": "Aktorprogrammierung EIN",
    "actuator programming OFF": "Aktorprogrammierung AUS",
    " sub-address ": " Subadresse ",
    "via the master redirect ": "mit der Masterrufumleitung ",
    "from phonebook index {n} ": "aus Telefonbuch mit Index {n} ",
    "with variant 1 active ": "und aktivierter Variante 1 ",
    "with variant 2 active ": "und aktivierter Variante 2 ",
    "the local subscriber": "den lokalen Teilnehmer",
    "an external subscriber": "einen externen Teilnehmer",
    " with number: {nr}": " mit der Rufnummer: {nr}",
    " with answering machine function inactive": " mit inaktiver Anrufbeantworterfunktion",
    " with answering machine function active": " mit aktiver Anrufbeantworterfunktion",
}
