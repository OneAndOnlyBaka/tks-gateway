"""UI texts of the web interface: key -> (English, German).

Keys without prefix are used by the template (``{{ t("key") }}``); keys with
the prefix ``js.`` are handed to the JavaScript (``t("js.key", {param})``).
Texts may contain HTML (they come from this file only); ``{name}`` marks
placeholders filled in by the JavaScript.
"""

UI: dict[str, tuple[str, str]] = {
    # ------------------------------------------------------------ general
    "title": ("TK Gateway Commissioning", "TK-Gateway Inbetriebnahme"),
    "subtitle": ("Commissioning", "Inbetriebnahme"),
    "port": ("Serial port", "Schnittstelle"),
    "ports.refresh": ("Search serial ports again", "Schnittstellen neu suchen"),
    "conn.test": ("Test connection", "Verbindung testen"),
    "lang.switch": ("Language", "Sprache"),
    "tab.config": ("Configuration", "Konfiguration"),
    "tab.phonebook": ("Phonebook", "Telefonbuch"),
    "tab.log": ("Log", "Loggen"),
    "tab.firmware": ("Firmware", "Firmware"),
    "tab.codes": ("Phone codes", "Telefon-Codes"),
    "ready": ("Ready", "Bereit"),
    "btn.load": ("Load from gateway", "Aus Gateway laden"),
    "btn.save": ("Save to gateway", "In Gateway speichern"),
    "btn.import": ("Load from file", "Aus Datei laden"),
    "btn.cancel": ("Cancel", "Abbrechen"),
    "btn.apply": ("Apply", "Übernehmen"),
    "btn.close": ("Close", "Schließen"),
    "btn.back": ("Back", "Zurück"),
    "btn.next": ("Next", "Weiter"),
    "btn.check_load": ("Check and load", "Prüfen und laden"),
    "undoc": ("undocumented", "undokumentiert"),
    "door": ("Door", "Tür"),
    "door_station": ("Door station", "Türstation"),
    "name": ("Name", "Bezeichnung"),
    "number_v1": ("Number V1", "Rufnummer V1"),
    "number_v2": ("Number V2", "Rufnummer V2"),
    "call_button": ("Call button", "Ruftaste"),
    "subscriber": ("Subscriber", "Teilnehmer"),
    "ab": ("AM", "AB"),
    "chk.conn": ("Check the connection to the TK gateway", "Verbindung zum TK-Gateway prüfen"),
    "chk.read": ("Load the current state from the gateway (nothing is overwritten)",
                 "Aktuellen Stand aus dem Gateway laden (nichts wird überschrieben)"),

    # ------------------------------------------------------------ configuration
    "cfg.connection": ("Connection type", "Anschlussart"),
    "cfg.amt": ("Direct line", "Amtsanschluss"),
    "cfg.amt.help": (
        "The gateway is connected with “Amt a/b” directly to the analogue telephone line. A phone is connected "
        "to “TLN a'/b'” and rings on door calls.",
        "Gateway hängt mit „Amt a/b“ direkt am analogen Telefonanschluss. Ein Telefon wird an „TLN a'/b'“ "
        "angeschlossen und klingelt bei Türrufen."),
    "cfg.neben": ("PBX extension", "Nebenstellenanschluss"),
    "cfg.neben.help": (
        "The gateway is connected to an analogue port of a PBX (e.g. FON 1 of a FRITZ!Box). Door calls go via "
        "the PBX to its phones. <strong>No</strong> phone may then be connected to TLN. Factory setting. "
        "→ wizard “Connect to PBX”.",
        "Gateway hängt an einem analogen Port einer Telefonanlage (z. B. FON 1 der FRITZ!Box). Türrufe gehen über "
        "die Anlage an deren Telefone. An TLN darf dann <strong>kein</strong> Telefon hängen. Werkseinstellung. "
        "→ Assistent „Mit Telefonanlage verbinden“."),
    "cfg.times": ("Times &amp; PIN", "Zeiten &amp; PIN"),
    "cfg.talk": ("Door talk time (s)", "Türgesprächszeit (s)"),
    "cfg.talk.help": (
        "Maximum duration of a door conversation; afterwards the gateway ends it automatically. "
        "Factory setting 60 s, max. 120 s.",
        "Maximale Dauer eines Türgesprächs; danach beendet das Gateway das Gespräch automatisch. "
        "Werkseinstellung 60 s, max. 120 s."),
    "cfg.local": ("Local ring time (s)", "Lokale Rufzeit (s)"),
    "cfg.local.help": (
        "How long the phone at “TLN a'/b'” rings. Only effective with a direct line; there also the waiting time "
        "until the <em>delayed</em> master redirect. Factory setting 30 s, max. 120 s.",
        "Wie lange das Telefon an „TLN a'/b'“ klingelt. Nur bei Amtsanschluss wirksam; dort auch die Wartezeit "
        "bis zur <em>verzögerten</em> Masterumleitung. Werkseinstellung 30 s, max. 120 s."),
    "cfg.external": ("External ring time (s)", "Externe Rufzeit (s)"),
    "cfg.external.help": (
        "How long the gateway calls via “Amt a/b” – an external number or, with a PBX, its phones. "
        "With a PBX extension also the waiting time until the <em>delayed</em> master redirect. "
        "Factory setting 30 s, max. 120 s.",
        "Wie lange über „Amt a/b“ gerufen wird – also eine externe Rufnummer bzw. bei einer Telefonanlage deren "
        "Telefone. Im Nebenstellenbetrieb auch die Wartezeit bis zur <em>verzögerten</em> Masterumleitung. "
        "Werkseinstellung 30 s, max. 120 s."),
    "cfg.pin": ("PIN", "PIN"),
    "cfg.pin.help": (
        "Protects programming by phone (<code>R * 0 * PIN #</code>). Factory setting 0000 – change it when "
        "connected to a PBX, because every internal phone can call the gateway.",
        "Schützt die Programmierung per Telefon (<code>R * 0 * PIN #</code>). Werkseinstellung 0000 – an einer "
        "Telefonanlage unbedingt ändern, denn jedes interne Telefon kann das Gateway anrufen."),
    "cfg.variant": ("Variant switching", "Variantenumschaltung"),
    "cfg.v1": ("Variant 1 (e.g. day)", "Variante 1 (z. B. Tag)"),
    "cfg.v2": ("Variant 2 (e.g. night)", "Variante 2 (z. B. Nacht)"),
    "cfg.variant.help": (
        "Every phonebook entry has two numbers. This selects which one is active – e.g. the mobile during the "
        "day, the home phone in the evening. Switchable by phone: <code>R * 3 * 1 #</code> or "
        "<code>R * 3 * 2 #</code>.",
        "Jeder Telefonbucheintrag hat zwei Rufnummern. Hier wird festgelegt, welche gerade gilt – z. B. tagsüber "
        "das Handy, abends das Telefon zu Hause. Per Telefon umschaltbar: <code>R * 3 * 1 #</code> bzw. "
        "<code>R * 3 * 2 #</code>."),
    "cfg.listen": ("Listen in", "Mithören"),
    "cfg.on": ("On", "An"),
    "cfg.off": ("Off", "Aus"),
    "cfg.listen.help": (
        "Explained neither in the manual nor in the original software. Gira lists a <strong>“privacy lock”"
        "</strong> (“Mithörsperre”) in the product description of the gateway – presumably this is its switch "
        "(off = lock active, factory setting). Firmware 1.26 stores the value (also by phone with "
        "<code>*8</code>), <strong>but never evaluates it</strong> – according to our analysis the setting has "
        "no effect.",
        "Weder im Handbuch noch in der Originalsoftware erklärt. Gira nennt in der Produktbeschreibung des "
        "Gateways eine <strong>„Mithörsperre“</strong> – vermutlich ist dies der Schalter dafür (Aus = Sperre "
        "aktiv, Werkseinstellung). Die Firmware 1.26 speichert den Wert (auch per Telefon mit <code>*8</code>), "
        "<strong>wertet ihn aber nirgends aus</strong> – die Einstellung hat nach unserer Analyse keine Wirkung."),
    "cfg.master": ("Master redirect", "Masterumleitung"),
    "cfg.master.number": ("Number", "Rufnummer"),
    "cfg.master.number.help": (
        "A number ranking above the phonebook to which – when enabled – all door calls go. Special characters: "
        "<code>P</code> dial pause ~1 s, <code>F</code>/<code>f</code> flash 100/80 ms, <code>*</code>, "
        "<code>#</code>. FRITZ!Box example: <code>**9</code> = all phones.",
        "Eine dem Telefonbuch übergeordnete Nummer, an die – wenn aktiviert – alle Türrufe gehen. Sonderzeichen: "
        "<code>P</code> Wählpause ~1 s, <code>F</code>/<code>f</code> Flash 100/80 ms, <code>*</code>, "
        "<code>#</code>. Beispiel FRITZ!Box: <code>**9</code> = alle Telefone."),
    "cfg.master.off": ("Off", "Aus"),
    "cfg.master.delayed": ("Delayed", "Verzögert"),
    "cfg.master.immediate": ("Immediate", "Sofort"),
    "cfg.master.ab": ("Answering machine", "Anrufbeantworter"),
    "cfg.master.help": (
        "<strong>Off:</strong> the phonebook numbers apply. <strong>Delayed:</strong> first the phonebook "
        "number; after the ring time (local with a direct line, external with a PBX extension) the master "
        "redirect number. <strong>Immediate:</strong> directly the master redirect number. Important: only call "
        "buttons learned in the phonebook are forwarded. <strong>Answering machine:</strong> see phonebook – "
        "cannot be combined with “delayed”.",
        "<strong>Aus:</strong> es gelten die Nummern des Telefonbuchs. <strong>Verzögert:</strong> erst die "
        "Telefonbuchnummer; nach Ablauf der Rufzeit (lokal bei Amt-, extern bei Nebenstellenanschluss) die "
        "Masterumleitungsnummer. <strong>Sofort:</strong> direkt die Masterumleitungsnummer. Wichtig: Es werden "
        "nur Klingeln weitergeleitet, die im Telefonbuch angelernt sind. <strong>Anrufbeantworter:</strong> "
        "siehe Telefonbuch – nicht mit „verzögert“ kombinierbar."),
    "btn.tk_wizard": ("Connect to PBX …", "Mit Telefonanlage verbinden …"),
    "btn.tk_test": ("Test PBX …", "Telefonanlage testen …"),
    "btn.defaults": ("Factory settings", "Werkseinstellungen"),
    "btn.export_gtk": ("Save as .gtk", "Als .gtk speichern"),
    "btn.export_json": ("Complete (.json)", "Komplett (.json)"),
    "btn.export_bin": ("Raw image (.bin)", "Rohabbild (.bin)"),

    # ------------------------------------------------------------ phonebook
    "pb.ab.help": (
        "Answering machine function for this number: if the door call is not answered, the answering machine "
        "or mailbox can be heard and spoken to at the door station.",
        "Anrufbeantworterfunktion für diese Nummer: Wird der Türruf nicht angenommen, kann man an der "
        "Türstation den Anrufbeantworter bzw. die Mailbox hören und besprechen."),
    "pb.ab2.help": ("Answering machine function for the number of variant 2.",
                    "Anrufbeantworterfunktion für die Nummer der Variante 2."),
    "pb.door.help": (
        "Number of the door station (1–9). With several door stations each needs its own number; it is also "
        "used to open the door by phone (# + number).",
        "Nummer der Türstation (1–9). Bei mehreren Türstationen braucht jede eine eigene Nummer; sie wird auch "
        "zum Türöffnen per Telefon verwendet (# + Nummer)."),
    "pb.button.help": (
        "“captured”: a call button is assigned (button code). “free”: no button yet – there are no door calls "
        "for this entry.",
        "„gefangen“: eine Klingeltaste ist zugeordnet (Tastercode). „frei“: noch keine Taste – Türrufe für "
        "diesen Eintrag gibt es dann nicht."),
    "pb.show_all": ("also show free entries", "auch freie Einträge anzeigen"),
    "btn.learn_wizard": ("Learn call buttons …", "Klingeln anlernen …"),
    "btn.pb_clear": ("Clear phonebook", "Telefonbuch löschen"),
    "btn.export_gtb": ("Save as .gtb", "Als .gtb speichern"),

    # ------------------------------------------------------------ log
    "log.ping": ("Test output", "Testausgabe"),
    "log.ping.title": ("Sends “i”: the gateway queries the bus driver and logs this as “S: 90 …”",
                       "Sendet „i“: das Gateway fragt den Bustreiber ab und protokolliert das als „S: 90 …“"),
    "log.show": ("Show", "Anzeigen"),
    "log.f.all": ("everything", "alles"),
    "log.f.calls": ("door calls only", "nur Türrufe"),
    "log.f.E": ("gateway receives", "Gateway empfängt"),
    "log.f.S": ("gateway sends", "Gateway sendet"),
    "log.f.T": ("gateway calls", "Gateway ruft"),
    "log.raw": ("Raw data", "Rohdaten"),
    "log.scroll": ("Auto-scroll", "Auto-Scroll"),
    "log.save": ("Save", "Speichern"),
    "log.clear": ("Clear", "Löschen"),
    "log.time": ("Time", "Zeit"),
    "log.text": ("Plain text", "Klartext"),
    "log.idle": (
        "No data from the gateway for some seconds. That is normal as long as nothing happens on the bus (or "
        "no bus is connected): the gateway only reports bus telegrams and its own dialling. “Test output” "
        "checks the connection.",
        "Seit einigen Sekunden keine Daten vom Gateway. Das ist normal, solange am Bus nichts passiert (oder "
        "kein Bus angeschlossen ist): Das Gateway meldet nur Bus-Telegramme und eigene Wählvorgänge. "
        "„Testausgabe“ prüft die Verbindung."),
    "log.scope": (
        "The log only shows the <strong>bus</strong> (<code>S:</code>/<code>E:</code>) and the gateway's own "
        "dialling (<code>T:</code>). Calls to the gateway, command mode and programming by phone are not "
        "reported by the firmware – only their bus actions, e.g. <code>#1</code> (open door) as "
        "<code>S: 31 …</code>.",
        "Das Log zeigt nur den <strong>Bus</strong> (<code>S:</code>/<code>E:</code>) und eigene Wählvorgänge "
        "(<code>T:</code>). Anrufe beim Gateway, Kommandomodus und Programmierung per Telefon meldet die "
        "Firmware nicht – nur deren Bus-Aktionen, z. B. <code>#1</code> (Tür öffnen) als <code>S: 31 …</code>."),
    "log.calls": (
        "Door calls (<code>E: 11</code>) contain the bus address of the pressed call button. Unknown buttons "
        "can be assigned to a phonebook entry right here.",
        "Türrufe (<code>E: 11</code>) enthalten die Busadresse der gedrückten Ruftaste. Unbekannte Klingeln "
        "lassen sich hier direkt einem Telefonbucheintrag zuordnen."),

    # ------------------------------------------------------------ firmware
    "fw.version": ("Firmware version", "Firmwarestand"),
    "fw.gateway": ("TK gateway", "TK-Gateway"),
    "fw.pic": ("Bus driver (PIC)", "Bustreiber (PIC)"),
    "fw.not_read": ("Not read yet.", "Noch nicht ausgelesen."),
    "fw.read": ("Read", "Auslesen"),
    "fw.bl_reset": ("Bootloader reset", "Bootlader-Reset"),
    "fw.bl_reset.title": ("Hidden function of the original software: restarts the bootloader",
                          "Versteckte Funktion der Originalsoftware: startet den Bootlader neu"),
    "fw.file": ("Firmware file (.tsk)", "Firmwaredatei (.tsk)"),
    "fw.transfer": ("Transfer", "Übertragen"),
    "fw.file.hint": ("The TK gateway erases its firmware and restarts afterwards (approx. 5 s).",
                     "Das TK-Gateway löscht dabei seine Firmware und startet danach neu (ca. 5 s)."),
    "fw.bt_file": ("Bus driver file (.hex)", "Bustreiberdatei (.hex)"),
    "fw.bt_file.hint": (
        "The bus driver PIC is erased immediately at the start. If the transfer breaks off, the bus only works "
        "again after a successful new upload.",
        "Der Bustreiber-PIC wird beim Start sofort gelöscht. Bricht die Übertragung ab, funktioniert der Bus "
        "erst nach einem erfolgreichen neuen Upload wieder."),
    "fw.abort.hint": (
        "If a transfer breaks off: check the connection, power-cycle the TK gateway and transfer again. The "
        "bootloader reset only works when the gateway is in the bootloader.",
        "Bricht eine Übertragung ab: Verbindung prüfen, Spannungsreset am TK-Gateway durchführen und erneut "
        "übertragen. Der Bootlader-Reset wirkt nur, wenn das Gateway im Bootlader steht."),

    # ------------------------------------------------------------ phone codes
    "codes.intro": (
        "Entered on a tone-dialling phone at the TLN terminals (prefix <code>R</code> = recall/flash key) or, "
        "with a PBX, after calling the gateway (<code>NR</code>).",
        "Eingabe an einem Tonwahl-Telefon an den TLN-Klemmen (Präfix <code>R</code> = Rückfrage-/Flash-Taste) "
        "bzw. bei Anschluss an eine Telefonanlage nach Anwahl des Gateways (<code>NR</code>)."),
    "codes.undoc_note": ("= found in firmware 1.26, not in the manual.",
                         "= in Firmware 1.26 gefunden, nicht im Handbuch."),
    "codes.action": ("Action", "Aktion"),
    "codes.code": ("DTMF code", "DTMF-Code"),
    "codes.note": ("Note", "Hinweis"),

    # ------------------------------------------------------------ entry dialog
    "entry.title": ("Phonebook entry", "Telefonbucheintrag"),
    "entry.name.help": ("Name of the entry or call button, max. 20 characters.",
                        "Name des Eintrags bzw. der Klingel, max. 20 Zeichen."),
    "entry.v1": ("Phone number variant 1", "Telefonnummer Variante 1"),
    "entry.v1.help": (
        "Which of the two numbers applies is set by the variant switching (configuration). Empty number: the "
        "door call goes to the phone at “TLN a'/b'” (only useful with a direct line). Max. 24 characters. "
        "Special characters: <code>P</code> dial pause ~1 s, <code>F</code>/<code>f</code> flash 100/80 ms, "
        "<code>*</code>, <code>#</code>.",
        "Welche der beiden Nummern gilt, bestimmt die Variantenumschaltung (Konfiguration). Leere Nummer: "
        "Türruf geht an das Telefon an „TLN a'/b'“ (nur bei Amtsanschluss sinnvoll). Max. 24 Zeichen. "
        "Sonderzeichen: <code>P</code> Wählpause ~1 s, <code>F</code>/<code>f</code> Flash 100/80 ms, "
        "<code>*</code>, <code>#</code>."),
    "entry.ab1": ("Answering machine (variant 1)", "Anrufbeantworter (Variante 1)"),
    "entry.ab.help": (
        "<strong>Answering machine:</strong> if the door call is not answered, the answering machine or mailbox "
        "can be heard and spoken to at the door station. After picking up you can talk immediately; the ring "
        "times do not apply, instead the door talk time runs from the ring. Cannot be combined with a "
        "“delayed” master redirect.",
        "<strong>Anrufbeantworter:</strong> Wird der Türruf nicht angenommen, kann man an der Türstation den "
        "Anrufbeantworter bzw. die Mailbox hören und besprechen. Nach Abheben kann sofort gesprochen werden; "
        "die Rufzeiten gelten dann nicht, stattdessen läuft die Türgesprächszeit ab dem Klingeln. Nicht mit "
        "„verzögerter“ Masterumleitung kombinierbar."),
    "entry.v2": ("Phone number variant 2", "Telefonnummer Variante 2"),
    "entry.v2.help": ("Second number, e.g. for the evening. Empty: door call to the phone at “TLN a'/b'”.",
                      "Zweite Nummer, z. B. für abends. Leer: Türruf an das Telefon an „TLN a'/b'“."),
    "entry.ab2": ("Answering machine (variant 2)", "Anrufbeantworter (Variante 2)"),
    "entry.ab2.help": ("Answering machine function for the number of variant 2.",
                       "Anrufbeantworterfunktion für die Nummer der Variante 2."),
    "entry.door.help": (
        "Number of the door station (1–9). With several door stations each needs its own number; it is also "
        "used to open the door by phone (<code>#</code> + number).",
        "Nummer der Türstation (1–9). Bei mehreren Türstationen braucht jede eine eigene Nummer; sie wird auch "
        "zum Türöffnen per Telefon verwendet (<code>#</code> + Nummer)."),
    "entry.code": ("Button code", "Tastercode"),
    "entry.code.help": (
        "Bus address of the call button – filled in automatically when learning. The gateway ignores call "
        "buttons that are not stored here.",
        "Busadresse der Klingeltaste – wird beim Anlernen automatisch eingetragen. Klingeln, die hier nicht "
        "hinterlegt sind, ignoriert das Gateway."),

    # ------------------------------------------------------------ call button dialog
    "rt.title": ("Assign call button – entry", "Ruftaste zuordnen – Eintrag"),
    "rt.a": ("A · Via the control unit", "A · Über das Steuergerät"),
    "rt.a.tag": ("like the original software", "wie Originalsoftware"),
    "rt.a.1": ("Press the “Systemprogr.” key on the control unit for <strong>3 s</strong> until the LED next "
               "to it flashes.",
               "Am Steuergerät die Taste „Systemprogr.“ <strong>3 s</strong> drücken, bis die LED daneben blinkt."),
    "rt.a.2": ("Press the call button(s) at the door station for <strong>3 s</strong> each until a short "
               "confirmation tone sounds – several in the order in which they shall be assigned to the entries.",
               "An der Türstation die Ruftaste(n) jeweils <strong>3 s</strong> drücken, bis ein kurzer "
               "Quittierton kommt – mehrere in der Reihenfolge, in der sie den Einträgen zugeordnet werden sollen."),
    "rt.a.3": ("Click “Fetch call button” here for each entry.",
               "Hier für jeden Eintrag „Ruftaste abholen“ klicken."),
    "rt.a.4": ("Finally press “Systemprogr.” briefly on the control unit (end programming mode).",
               "Zum Schluss am Steuergerät „Systemprogr.“ kurz drücken (Programmiermodus beenden)."),
    "rt.a.warn": ("Release the call button after the confirmation tone! Holding it another 3 s deletes "
                  "<strong>all assignments of this door station</strong>.",
                  "Ruftaste nach dem Quittierton loslassen! Wer weitere 3 s hält, löscht <strong>alle Zuordnungen "
                  "dieser Türstation</strong>."),
    "rt.fetch": ("Fetch call button", "Ruftaste abholen"),
    "rt.b": ("B · By capture", "B · Per Mitschnitt"),
    "rt.b.tag": ("no programming mode", "ohne Programmiermodus"),
    "rt.b.text": ("Starts logging and takes over the next door call. Note: it really rings, and every door "
                  "call during this time is detected.",
                  "Startet das Loggen und übernimmt den nächsten Türruf. Achtung: Es klingelt wirklich, und jeder "
                  "Türruf in dieser Zeit wird erkannt."),
    "rt.cap": ("Start capture", "Mitschnitt starten"),
    "rt.multi": ("Several call buttons at once:", "Mehrere Klingeln auf einmal:"),
    "rt.multi.link": ("wizard “Learn call buttons”", "Assistent „Klingeln anlernen“"),
    "rt.c": ("C · By phone", "C · Per Telefon"),
    "rt.c.text": ("Enter on the phone, then ring at the door within 15 s:",
                  "Am Telefon eingeben, dann innerhalb von 15 s an der Tür klingeln:"),

    # ------------------------------------------------------------ assign dialog
    "as.title": ("Assign door call", "Türruf zuordnen"),
    "tab.help": ("Help", "Hilfe"),
    "tab.licenses": ("Licenses", "Lizenzen"),
    "lic.intro": (
        "tks-gateway is licensed under the MIT license. This list is determined at runtime from the installed "
        "packages, so it always matches the running installation.",
        "tks-gateway steht unter der MIT-Lizenz. Diese Liste wird zur Laufzeit aus den installierten Paketen "
        "ermittelt und passt daher immer zur laufenden Installation.",
    ),
    "lic.sbom": ("Download SBOM (CycloneDX JSON)", "SBOM herunterladen (CycloneDX JSON)"),
    "lic.sbom.title": ("Software bill of materials of this installation, generated on request",
                       "Stückliste (SBOM) dieser Installation, wird beim Abruf erzeugt"),
    "lic.component": ("Component", "Komponente"),
    "lic.version": ("Version", "Version"),
    "lic.license": ("License", "Lizenz"),
    "lic.type": ("Type", "Art"),
    "lic.source": ("Project", "Projekt"),
    "lic.disclaimer": ("Gira and product names are trademarks of their owners. See DISCLAIMER.md – no Gira code, "
                       "firmware or documents are included.",
                       "Gira und Produktnamen sind Marken ihrer Inhaber. Siehe DISCLAIMER.md – Code, Firmware oder "
                       "Dokumente von Gira sind nicht enthalten."),
    "js.lic.loading": ("Determining components …", "Komponenten werden ermittelt …"),
    "js.lic.text": ("License text", "Lizenztext"),
    "js.lic.bundled": ("Bundled npm dependencies", "Mitgelieferte npm-Abhängigkeiten"),
    "js.lic.requires": ("Requires", "Benötigt"),
    "js.lic.python": ("Python package", "Python-Paket"),
    "js.lic.javascript": ("JavaScript (bundled)", "JavaScript (mitgeliefert)"),
    "js.lic.own": ("this project", "dieses Projekt"),
    "js.lic.failed": ("Could not determine the components: {err}", "Komponenten konnten nicht ermittelt werden: {err}"),
    "save_note": (
        "<strong>Not saved yet:</strong> call buttons assigned here only change the working copy. The gateway "
        "only uses them after you write the phonebook explicitly (stop logging, then Phonebook → "
        "“Save to gateway”).",
        "<strong>Noch nicht gespeichert:</strong> Hier zugeordnete Ruftasten ändern nur die Arbeitskopie. Das "
        "Gateway übernimmt sie erst, wenn Sie das Telefonbuch ausdrücklich schreiben (Loggen beenden, dann "
        "Telefonbuch → „In Gateway speichern“).",
    ),
    "save_note.btn": ("Save phonebook to gateway", "Telefonbuch in Gateway speichern"),
    "save_note.pb": ("Click “Save to gateway” so the gateway uses them.",
                     "Mit „In Gateway speichern“ übernimmt das Gateway sie."),
    "as.entry": ("Phonebook entry", "Telefonbucheintrag"),

    # ------------------------------------------------------------ PBX test
    "tt.title": ("Test the connection to the PBX", "Verbindung zur Telefonanlage testen"),
    "tt1.title": ("Test 1 · PBX → gateway", "Test 1 · Anlage → Gateway"),
    "tt1.tag": ("possible without bus", "ohne Bus möglich"),
    "tt1.text": ("Checks whether the PBX reaches the gateway and it understands tone dialling: you call the "
                 "gateway and switch the variant by phone – the UI then reads back whether the input arrived.",
                 "Prüft, ob die Telefonanlage das Gateway erreicht und es Tonwahl versteht: Sie rufen das Gateway "
                 "an und schalten per Telefon die Variante um – die Oberfläche liest danach nach, ob die Eingabe "
                 "angekommen ist."),
    "tt1.hint": ("Loads the current state from the gateway first (unsaved changes in the UI are lost) and "
                 "switches the variant back automatically at the end.",
                 "Lädt dazu den aktuellen Stand aus dem Gateway (ungespeicherte Änderungen in der Oberfläche gehen "
                 "verloren) und stellt die Variante am Ende automatisch zurück."),
    "tt1.start": ("Start test 1", "Test 1 starten"),
    "tt1.s1": ("Call the gateway from a phone of the PBX{own}. <strong>Let it ring</strong> – the gateway only "
               "answers after approx. 12–20 s (observed: at the 3rd–4th ring). Then you hear the "
               "<strong>command tone</strong> (two short tones, repeated).",
               "Von einem Telefon der Anlage das Gateway anrufen{own}. <strong>Klingeln lassen</strong> – das "
               "Gateway nimmt erst nach ca. 12–20 s ab (beobachtet: beim 3.–4. Klingeln). Dann hören Sie den "
               "<strong>Kommandoton</strong> (zwei kurze Töne, wiederholt)."),
    "tt1.s2": ("Enter: {code} – a confirmation tone follows. Then hang up.",
               "Eingeben: {code} – es folgt ein Quittierton. Dann auflegen."),
    "tt1.s3": ("Click “Check” here. Wait at least 60 s after hanging up before another call – the gateway holds "
               "the line that long (otherwise: busy).",
               "Hier auf „Prüfen“ klicken. Für einen weiteren Anruf nach dem Auflegen mindestens 60 s warten – so "
               "lange hält das Gateway die Leitung noch (sonst: besetzt)."),
    "tt1.check": ("Check", "Prüfen"),
    "tt2.title": ("Test 2 · Gateway → PBX", "Test 2 · Gateway → Anlage"),
    "tt2.tag": ("needs bus + learned call button", "braucht Bus + angelernte Klingel"),
    "tt2.text": ("Checks whether the gateway dials out and the PBX puts the call through: start capture, ring "
                 "at the door – the UI shows whether and which number the gateway dials.",
                 "Prüft, ob das Gateway hinauswählt und die Anlage den Anruf durchstellt: Mitschnitt starten, an "
                 "der Tür klingeln – die Oberfläche zeigt, ob und welche Nummer das Gateway wählt."),
    "tt2.start": ("Start test 2", "Test 2 starten"),
    "tt2.ask": ("Did the phone or phones ring?", "Hat das Telefon bzw. haben die Telefone geklingelt?"),
    "yes": ("Yes", "Ja"),
    "no": ("No", "Nein"),

    # ------------------------------------------------------------ PBX wizard
    "tk.title": ("Connect to PBX", "Mit Telefonanlage verbinden"),
    "tk.st1": ("Connection", "Anschluss"),
    "tk.st2": ("Who rings?", "Wer klingelt?"),
    "tk.st3": ("Times &amp; PIN", "Zeiten &amp; PIN"),
    "tk.st4": ("Check", "Prüfen"),
    "tk.st5": ("Done", "Fertig"),
    "tk.other": ("other PBX", "andere Telefonanlage"),
    "tk.wire": (
        "<strong>Wiring:</strong> terminals “Amt a/b” of the gateway to an <em>analogue</em> phone port of the "
        "PBX <span class=\"fritz\">(FRITZ!Box: “FON 1” or “FON 2”)</span>. <strong>Nothing</strong> may be "
        "connected to “TLN a'/b'”. Bus and power supply “Ub” stay as they are.",
        "<strong>Verkabeln:</strong> Klemmen „Amt a/b“ des Gateways an einen <em>analogen</em> Telefonport der "
        "Anlage <span class=\"fritz\">(FRITZ!Box: „FON 1“ oder „FON 2“)</span>. An „TLN a'/b'“ darf "
        "<strong>nichts</strong> angeschlossen sein. Bus und Versorgung „Ub“ bleiben wie sie sind."),
    "tk.setup": (
        "<strong>Set up the PBX:</strong> configure the port as an analogue phone with tone dialling (DTMF). "
        "<span class=\"fritz\">FRITZ!Box: Telephony → Telephony Devices → Configure New Device → Telephone → "
        "FON 1/2 (name e.g. “door gateway”). Menu path differs slightly depending on FRITZ!OS.</span> "
        "<span class=\"andere\">Details are in the manual of the PBX.</span>",
        "<strong>Anlage einrichten:</strong> den Port als analoges Telefon mit Tonwahl (MFV) einrichten. "
        "<span class=\"fritz\">FRITZ!Box: Telefonie → Telefoniegeräte → Neues Gerät einrichten → Telefon → "
        "FON 1/2 (Bezeichnung z. B. „Türgateway“). Menüpfad je nach FRITZ!OS leicht anders.</span> "
        "<span class=\"andere\">Details stehen in der Anleitung der Anlage.</span>"),
    "tk.own": ("<strong>Internal number of the gateway</strong> (optional, for the test and programming by "
               "phone):",
               "<strong>Interne Nummer des Gateways</strong> (optional, für den Test und die Programmierung per "
               "Telefon):"),
    "tk.own.placeholder": ("e.g. **1", "z. B. **1"),
    "tk.wired": ("The gateway is connected like this and set up in the PBX",
                 "Gateway ist so angeschlossen und in der Anlage eingerichtet"),
    "tk.who": ("Who shall be called when someone rings at the door?",
               "Wer soll angerufen werden, wenn an der Tür geklingelt wird?"),
    "tk.all": ("<strong>All phones at once</strong> (group call) – the same number for all call buttons. "
               "Entered as master redirect “immediate”.",
               "<strong>Alle Telefone gleichzeitig</strong> (Sammelruf) – für alle Klingeln dieselbe Nummer. Wird "
               "als Masterumleitung „sofort“ eingetragen."),
    "tk.group": ("Group call number", "Sammelruf-Nummer"),
    "tk.group.fritz": ("FRITZ!Box: <code>**9</code> rings all phones. Single devices: <code>**1</code>/"
                       "<code>**2</code> (FON 1/2), DECT handsets from <code>**610</code>.",
                       "FRITZ!Box: <code>**9</code> ruft alle Telefone. Einzelne Geräte: <code>**1</code>/"
                       "<code>**2</code> (FON 1/2), DECT-Mobilteile ab <code>**610</code>."),
    "tk.group.other": ("The group call number is given in the manual of the PBX.",
                       "Die Nummer für den Sammelruf steht in der Anleitung der Telefonanlage."),
    "tk.single": ("<strong>A separate number per call button</strong> – e.g. ground and upper floor "
                  "separately. Entered as number (variant 1) in the phonebook.",
                  "<strong>Je Klingel eine eigene Nummer</strong> – z. B. Erdgeschoss und Obergeschoss getrennt. "
                  "Wird als Rufnummer (Variante 1) im Telefonbuch eingetragen."),
    "tk.bell": ("Call button", "Klingel"),
    "tk.number": ("Number", "Rufnummer"),
    "tk.ring": ("Ring duration at the phones (external ring time, s)",
                "Klingeldauer an den Telefonen (externe Rufzeit, s)"),
    "tk.ring.help": ("How long the phones of the PBX ring before the gateway gives up. 10–120 s, usually 20–30 s.",
                     "So lange klingeln die Telefone der Anlage, bevor das Gateway aufgibt. 10–120 s, üblich "
                     "20–30 s."),
    "tk.talk.help": ("Maximum duration of a door conversation, afterwards the gateway hangs up. Max. 120 s.",
                     "Maximale Dauer eines Türgesprächs, danach wird automatisch aufgelegt. Max. 120 s."),
    "tk.pin.warn": ("The PIN is still 0000. With a PBX every internal phone can call the gateway and reprogram "
                    "it with the PIN – please change it.",
                    "Die PIN ist noch 0000. An einer Telefonanlage kann jedes interne Telefon das Gateway anrufen "
                    "und mit der PIN umprogrammieren – bitte ändern."),
    "tk.changes": ("These changes are written to the gateway:", "Diese Änderungen werden in das Gateway geschrieben:"),
    "tk.test_now": ("Test the connection now …", "Verbindung jetzt testen …"),
    "tk.t1": ("Ring at the door – the selected phones ring.", "An der Tür klingeln – die gewählten Telefone klingeln."),
    "tk.t2": ("Pick up and talk. <strong>Open the door:</strong> press <code>#</code> and <code>0</code> during "
              "the conversation (further doors: <code>#1</code> … <code>#9</code>).",
              "Abheben und sprechen. <strong>Tür öffnen:</strong> während des Gesprächs <code>#</code> und "
              "<code>0</code> drücken (weitere Türen: <code>#1</code> … <code>#9</code>)."),
    "tk.t3": ("Hanging up ends the conversation. If a busy tone keeps sounding at the door, end the conversation "
              "with <code>0</code>.",
              "Auflegen beendet das Gespräch. Hört man an der Tür weiter ein Besetztzeichen, das Gespräch mit "
              "<code>0</code> beenden."),
    "tk.t4": ("<strong>Open the door without a conversation</strong> (e.g. visitor already seen): call the "
              "gateway, after the command tone <code>#</code> + number of the door station (e.g. <code>#1</code>).",
              "<strong>Tür öffnen ohne Gespräch</strong> (z. B. Besucher schon gesehen): Gateway anrufen, nach dem "
              "Kommandoton <code>#</code> + Nummer der Türstation (z. B. <code>#1</code>)."),
    "tk.t5": ("Operate the gateway by phone: call the internal number and let it ring (answer after approx. "
              "12–20 s), after the command tone enter the codes from the “Phone codes” tab.",
              "Gateway per Telefon bedienen: interne Nummer anrufen und klingeln lassen (Annahme nach ca. "
              "12–20 s), nach dem Kommandoton die Codes aus dem Reiter „Telefon-Codes“ eingeben."),

    # ------------------------------------------------------------ learn wizard
    "wz.title": ("Learn call buttons", "Klingeln anlernen"),
    "wz.passive": ("passive", "passiv"),
    "wz.st1": ("Prepare", "Vorbereiten"),
    "wz.st2": ("Ring", "Klingeln"),
    "wz.st3": ("Check", "Prüfen"),
    "wz.st4": ("Done", "Fertig"),
    "wz.intro": ("The wizard listens to the bus and detects every pressed call button. The gateway sends "
                 "<strong>nothing</strong> to the bus – no programming mode, no phone needed.",
                 "Der Assistent liest den Bus mit und erkennt jede gedrückte Klingeltaste. Das Gateway sendet "
                 "dabei <strong>nichts</strong> auf den Bus – kein Programmiermodus, kein Telefon nötig."),
    "wz.backup": ("Download backup (.bin)", "Sicherung herunterladen (.bin)"),
    "wz.req": ("Requirement: the gateway is connected to the bus and powered.",
               "Voraussetzung: Das Gateway ist am Bus angeschlossen und versorgt."),
    "wz.live": ("Capture running – go to the door stations and press the call buttons <strong>one after "
                "another</strong>. Every detected button appears below. The bell rings normally.",
                "Mitschnitt läuft – gehen Sie zu den Türstationen und drücken Sie die Klingeltasten "
                "<strong>nacheinander</strong>. Jede erkannte Taste erscheint unten. Die Klingel ertönt dabei "
                "normal."),
    "wz.detected": ("detected", "erkannt"),
    "wz.entry": ("Entry", "Eintrag"),
    "wz.empty": ("No call button detected yet …", "Noch keine Klingel erkannt …"),
    "wz.tip": ("Tip: if you do not know which row belongs to which call button, press it again – the row is "
               "highlighted.",
               "Tipp: Wissen Sie nicht, welche Zeile zu welcher Klingel gehört, drücken Sie die Klingel noch "
               "einmal – die Zeile wird hervorgehoben."),
    "wz.save_note": (
        "<strong>Nothing is saved yet.</strong> The assignments are only written to the gateway in the next "
        "step with “Save to gateway”. If you cancel the wizard, the gateway keeps its previous assignments.",
        "<strong>Noch ist nichts gespeichert.</strong> Die Zuordnungen werden erst im nächsten Schritt mit "
        "„In Gateway speichern“ in das Gateway geschrieben. Brechen Sie den Assistenten ab, behält das Gateway "
        "seine bisherigen Zuordnungen.",
    ),
    "wz.summary": ("These assignments are written to the phonebook of the gateway:",
                   "Diese Zuordnungen werden in das Telefonbuch des Gateways geschrieben:"),
    "wz.later": ("Numbers and further details can be changed in the phonebook at any time.",
                 "Rufnummern und weitere Angaben lassen sich danach jederzeit im Telefonbuch ändern."),
    "wz.test": ("To test: start the “Log” tab and ring – the door call then shows the assigned entry.",
                "Zum Testen: im Reiter „Loggen“ starten und klingeln – der Türruf zeigt dann den zugeordneten "
                "Eintrag."),

    # ================================================================ JavaScript
    "js.explanation": ("Explanation", "Erklärung"),
    "js.undoc": ("undocumented", "undokumentiert"),
    "js.simulation": ("Simulation", "Simulation"),
    "js.none_option": ("– none –", "– keine –"),
    "js.port_set": ("Serial port: {port}", "Schnittstelle: {port}"),
    "js.none": ("none", "keine"),
    "js.cfg_conflict": ("At least one phonebook entry has the answering machine function enabled – a delayed "
                        "master redirect is not possible with it.",
                        "Mindestens ein Telefonbucheintrag hat die Anrufbeantworterfunktion aktiv – eine "
                        "verzögerte Masterumleitung ist damit nicht möglich."),
    "js.fix_fields": ("Please correct the marked fields", "Bitte die markierten Felder korrigieren"),
    "js.cfg_changed": ("Configuration changed – not yet saved to the gateway",
                       "Konfiguration geändert – noch nicht im Gateway gespeichert"),
    "js.captured": ("captured", "gefangen"),
    "js.free": ("free", "frei"),
    "js.edit": ("Edit", "Bearbeiten"),
    "js.button_dlg": ("Call button …", "Ruftaste …"),
    "js.delete_entry": ("Delete entry", "Eintrag löschen"),
    "js.delete_entry_n": ("Delete entry {n}", "Eintrag {n} löschen"),
    "js.no_entries": ("No entries. Select “also show free entries” to create one.",
                      "Keine Einträge. „auch freie Einträge anzeigen“ wählen, um einen anzulegen."),
    "js.confirm_delete": ("Do you really want to delete the phonebook entry?",
                          "Möchten Sie den Telefonbucheintrag wirklich löschen?"),
    "js.entry_changed": ("Entry changed – not yet saved to the gateway",
                         "Eintrag geändert – noch nicht im Gateway gespeichert"),
    "js.fetching": ("Fetching call information …", "Rufinformation wird abgeholt …"),
    "js.waiting_call": ("Waiting for a door call … ring now", "Warte auf Türruf … jetzt klingeln"),
    "js.button_taken": ("Call button taken over – please save the phonebook to the gateway",
                        "Ruftaste übernommen – bitte das Telefonbuch in das Gateway speichern"),
    "js.detected_code": ("Detected: {code}", "Erkannt: {code}"),
    "js.already_entry": (" (already entry {entry})", " (bereits Eintrag {entry})"),
    "js.next": ("Next", "Weiter"),
    "js.save_gw": ("Save to gateway", "Ins Gateway speichern"),
    "js.close": ("Close", "Schließen"),
    "js.dup_entry": ("Entry {n} is assigned to several call buttons.", "Eintrag {n} ist mehreren Klingeln zugeordnet."),
    "js.replaces": ("Entry {entry} already has a different call button – it will be replaced.",
                    "Eintrag {entry} hat bereits eine andere Ruftaste – sie wird ersetzt."),
    "js.taken": (" (taken)", " (belegt)"),
    "js.free_suffix": (" · free", " · frei"),
    "js.known_entry": ("known: entry {n}", "bekannt: Eintrag {n}"),
    "js.entry": ("Entry", "Eintrag"),
    "js.door_station": ("Door station", "Türstation"),
    "js.name": ("Name", "Bezeichnung"),
    "js.number_v1": ("Number V1", "Rufnummer V1"),
    "js.add_again": ("Add", "Aufnehmen"),
    "js.discard": ("Discard", "Verwerfen"),
    "js.ready_backup": ("Ready. Recommendation: download the backup first.",
                        "Bereit. Empfehlung: zuerst die Sicherung herunterladen."),
    "js.number_chars": ("Number: only digits, *, # and P, F, f", "Rufnummer: nur Ziffern, *, # sowie P, F, f"),
    "js.wz_line": ("{code} → entry {n}", "{code} → Eintrag {n}"),
    "js.door_station_n": (", door station {n}", ", Türstation {n}"),
    "js.number_n": (", number {nr}", ", Rufnummer {nr}"),
    "js.already_assigned": (" (already assigned like this)", " (bereits so zugeordnet)"),
    "js.saving": ("Saving …", "Speichere …"),
    "js.save_failed_pb": ("Error while saving: {err}. The assignments are entered in the phonebook – please use "
                          "“Save to gateway” there again.",
                          "Fehler beim Speichern: {err}. Die Zuordnungen sind im Telefonbuch eingetragen – bitte "
                          "dort erneut „In Gateway speichern“."),
    "js.wz_saved": ("{n} call button(s) assigned and saved in the gateway.",
                    "{n} Klingel(n) zugeordnet und im Gateway gespeichert."),
    "js.no_learned": ("No learned call buttons.", "Keine angelernten Klingeln."),
    "js.n_learned": ("{n} call button(s) are learned.", "{n} Klingel(n) sind angelernt."),
    "js.none_learned_warn": ("No call button learned yet. The gateway ignores door calls of unknown call buttons – "
                             "please run the wizard “Learn call buttons” (Phonebook tab) afterwards.",
                             "Noch keine Klingel angelernt. Das Gateway ignoriert Türrufe von unbekannten Klingeln – "
                             "bitte danach den Assistenten „Klingeln anlernen“ (Reiter Telefonbuch) ausführen."),
    "js.number_for": ("Number for entry {n}", "Rufnummer für Eintrag {n}"),
    "js.lbl.anschlussart": ("Connection type", "Anschlussart"),
    "js.lbl.externe_rufzeit": ("External ring time", "Externe Rufzeit"),
    "js.lbl.tuergespraechszeit": ("Door talk time", "Türgesprächszeit"),
    "js.lbl.pin": ("PIN", "PIN"),
    "js.lbl.masterumleitung": ("Master redirect", "Masterumleitung"),
    "js.lbl.masterumleitungsnummer": ("Master redirect number", "Masterumleitungsnummer"),
    "js.lbl.master_anrufbeantworter": ("Answering machine (master)", "Anrufbeantworter (Master)"),
    "js.lbl.variante": ("Variant", "Variante"),
    "js.entry_number_change": ("Entry {entry}, number V1:", "Eintrag {entry}, Rufnummer V1:"),
    "js.val.amt": ("direct line", "Amtsanschluss"),
    "js.val.nebenstelle": ("PBX extension", "Nebenstelle"),
    "js.val.aus": ("off", "aus"),
    "js.val.verzoegert": ("delayed", "verzögert"),
    "js.val.sofort": ("immediate", "sofort"),
    "js.val.true": ("on", "an"),
    "js.val.false": ("off", "aus"),
    "js.no_changes": ("No changes – the gateway is already set up like this.",
                      "Keine Änderungen – das Gateway ist bereits so eingestellt."),
    "js.warn_unlearned": ("No call button learned yet – door calls are only forwarded afterwards.",
                          "Noch keine Klingel angelernt – Türrufe werden erst danach weitergeleitet."),
    "js.warn_pin": ("The PIN is still 0000.", "Die PIN ist weiterhin 0000."),
    "js.save_failed": ("Error while saving: {err}", "Fehler beim Speichern: {err}"),
    "js.tk_saved": ("Saved. The gateway now works as an extension of your PBX.",
                    "Gespeichert. Das Gateway arbeitet jetzt als Nebenstelle Ihrer Telefonanlage."),
    "js.tk_own": ("Operate the gateway by phone: call <code>{own}</code> and let it ring (answer after approx. "
                  "12–20 s), after the command tone enter the codes from the “Phone codes” tab (PIN!).",
                  "Gateway per Telefon bedienen: <code>{own}</code> anrufen und klingeln lassen (Annahme nach ca. "
                  "12–20 s), nach dem Kommandoton die Codes aus dem Reiter „Telefon-Codes“ eingeben (PIN!)."),
    "js.loading_state": ("Loading current state …", "Lade aktuellen Stand …"),
    "js.tt1_amt": ("The gateway is set to <strong>direct line</strong> and does not accept calls from the PBX "
                   "this way. Please switch to PBX extension first with “Connect to PBX”.",
                   "Das Gateway steht auf <strong>Amtsanschluss</strong> und nimmt so keine Anrufe der "
                   "Telefonanlage an. Bitte zuerst mit „Mit Telefonanlage verbinden“ auf Nebenstelle umstellen."),
    "js.reading_gw": ("Reading gateway …", "Lese Gateway …"),
    "js.tt1_fail": (
        "<p><strong>The input did not arrive</strong> (variant is still {v}). Depending on what you heard:</p><ul>"
        "<li><strong>Busy tone</strong>: after a call the gateway keeps the line in command mode for up to 60 s "
        "(until no key is pressed any more). Wait at least 60 s after hanging up and call again.</li>"
        "<li><strong>No command tone</strong>: did you let it ring long enough? The gateway only answers after "
        "approx. 12–20 s. If the PBX ends the call earlier, increase its ring time/“no answer timeout”. "
        "Otherwise the PBX does not reach the gateway – wiring “Amt a/b” ↔ analogue port, port set up as a "
        "phone in the PBX, correct internal number?</li>"
        "<li><strong>Command tone, but no confirmation tone</strong>: tone dialling does not arrive – set the "
        "port or phone to tone dialling (DTMF), enter the digits a bit slower.</li>"
        "<li><strong>Confirmation tone heard</strong>: hung up? Then click “Check” again.</li></ul>",
        "<p><strong>Die Eingabe ist nicht angekommen</strong> (Variante ist weiterhin {v}). Je nachdem, was Sie "
        "gehört haben:</p><ul>"
        "<li><strong>Besetztzeichen</strong>: Das Gateway hält nach einem Anruf die Leitung noch bis zu 60 s im "
        "Kommandomodus (bis keine Taste mehr gedrückt wird). Nach dem Auflegen mindestens 60 s warten und erneut "
        "anrufen.</li>"
        "<li><strong>Kein Kommandoton</strong>: Lange genug klingeln lassen? Das Gateway nimmt erst nach ca. "
        "12–20 s ab. Bricht die Anlage den Ruf vorher ab, deren Rufzeit/„No-Answer-Timeout“ erhöhen. Sonst "
        "erreicht die Anlage das Gateway nicht – Verkabelung „Amt a/b“ ↔ analoger Port, Port in der Anlage als "
        "Telefon eingerichtet, richtige interne Nummer?</li>"
        "<li><strong>Kommandoton, aber kein Quittierton</strong>: Die Tonwahl kommt nicht an – Port bzw. Telefon "
        "auf Tonwahl (MFV) einstellen, Ziffern etwas langsamer eingeben.</li>"
        "<li><strong>Quittierton gehört</strong>: aufgelegt? Dann noch einmal „Prüfen“.</li></ul>"),
    "js.restoring": ("Switching the variant back …", "Stelle Variante zurück …"),
    "js.tt1_ok": ("<strong>✓ PBX → gateway works.</strong> The PBX reaches the gateway and tone dialling is "
                  "recognised. ",
                  "<strong>✓ Anlage → Gateway funktioniert.</strong> Die Anlage erreicht das Gateway und die "
                  "Tonwahl wird erkannt. "),
    "js.tt1_restore_fail": ("<span class=\"warn\">Switching the variant back failed ({err}) – please by phone "
                            "<code>* 3 * {v} #</code>.</span>",
                            "<span class=\"warn\">Zurückstellen der Variante fehlgeschlagen ({err}) – bitte per "
                            "Telefon <code>* 3 * {v} #</code>.</span>"),
    "js.tt1_restored": ("Variant switched back to {v}.", "Variante wieder auf {v} gestellt."),
    "js.tt2_ring": ("Door call received – please ring at the door now",
                    "Türruf empfangen – bitte jetzt an der Tür klingeln"),
    "js.tt2_known": ("Call button known in the phonebook", "Klingel im Telefonbuch bekannt"),
    "js.tt2_dial": ("Gateway dials", "Gateway wählt"),
    "js.tt2_unlearned": ("No call button learned yet – the gateway ignores door calls of unknown call buttons. "
                         "Please first <button type=\"button\" class=\"link\" data-action=\"wizard-from-tt\">learn "
                         "call buttons</button>.",
                         "Noch keine Klingel angelernt – das Gateway ignoriert Türrufe unbekannter Klingeln. Bitte "
                         "zuerst <button type=\"button\" class=\"link\" data-action=\"wizard-from-tt\">Klingeln "
                         "anlernen</button>."),
    "js.tt2_noring": ("<strong>No door call received.</strong> Is the gateway connected to the bus and powered? "
                      "In the “Log” tab, lines <code>E: 11 …</code> should appear when ringing.",
                      "<strong>Kein Türruf empfangen.</strong> Hängt das Gateway am Bus und ist es versorgt? Im "
                      "Reiter „Loggen“ sollten beim Klingeln Zeilen <code>E: 11 …</code> erscheinen."),
    "js.tt2_aborted": ("Test aborted.", "Test abgebrochen."),
    "js.tt2_rang": ("Door call received ({code})", "Türruf empfangen ({code})"),
    "js.tt2_notlearned": ("<strong>This call button is not learned</strong> – the gateway ignores it and does not "
                          "dial. Please assign it with <button type=\"button\" class=\"link\" "
                          "data-action=\"wizard-from-tt\">Learn call buttons</button> and repeat the test.",
                          "<strong>Diese Klingel ist nicht angelernt</strong> – das Gateway ignoriert sie und wählt "
                          "nicht. Bitte mit <button type=\"button\" class=\"link\" data-action=\"wizard-from-tt\">"
                          "Klingeln anlernen</button> zuordnen und den Test wiederholen."),
    "js.tt2_isknown": ("Call button known: entry {entry}", "Klingel bekannt: Eintrag {entry}"),
    "js.tt2_nodial": ("<strong>The gateway did not dial.</strong> Is a number entered for this call button in the "
                      "active variant, or is the master redirect active? With a PBX extension every door call "
                      "needs a number.",
                      "<strong>Das Gateway hat nicht gewählt.</strong> Ist für diese Klingel in der aktiven Variante "
                      "eine Rufnummer eingetragen bzw. die Masterumleitung aktiv? Bei Nebenstellenanschluss braucht "
                      "jeder Türruf eine Nummer."),
    "js.tt2_local": ("The gateway calls the phone at “TLN” instead of the PBX – the connection type is set to "
                     "<strong>direct line</strong> or the number is empty.",
                     "Das Gateway ruft das Telefon an „TLN“ statt der Anlage – die Anschlussart steht auf "
                     "<strong>Amtsanschluss</strong> oder die Rufnummer ist leer."),
    "js.tt2_dials": ("Gateway dials {nr} ({what})", "Gateway wählt {nr} ({what})"),
    "js.entry_n": ("entry {n}", "Eintrag {n}"),
    "js.master": ("master redirect", "Masterumleitung"),
    "js.tt2_ok": ("<strong>✓ Gateway → PBX works.</strong> Finally pick up at the phone, talk and open the door "
                  "with <code>#0</code>.",
                  "<strong>✓ Gateway → Anlage funktioniert.</strong> Zum Abschluss am Telefon abheben, sprechen und "
                  "mit <code>#0</code> die Tür öffnen."),
    "js.tt2_no": (
        "<p><strong>The gateway dialled, but the PBX did not put the call through.</strong> Please check:</p><ul>"
        "<li>Is the number <code>{nr}</code> correct for your PBX? (FRITZ!Box: <code>**9</code> all, "
        "<code>**1</code>/<code>**2</code> FON, DECT from <code>**610</code>)</li>"
        "<li>Does the PBX need a pause before dialling? Prepend a <code>P</code>, e.g. <code>P**9</code>.</li>"
        "<li>Is the port set up in the PBX as a phone with tone dialling and allowed to make internal calls?</li>"
        "<li>Are the terminals “Amt a/b” (not “TLN”) connected to the port?</li></ul>",
        "<p><strong>Das Gateway hat gewählt, die Anlage hat den Ruf aber nicht durchgestellt.</strong> Prüfen "
        "Sie:</p><ul>"
        "<li>Stimmt die Nummer <code>{nr}</code> für Ihre Anlage? (FRITZ!Box: <code>**9</code> alle, "
        "<code>**1</code>/<code>**2</code> FON, DECT ab <code>**610</code>)</li>"
        "<li>Braucht die Anlage eine Pause vor der Wahl? Ein <code>P</code> voranstellen, z. B. "
        "<code>P**9</code>.</li>"
        "<li>Ist der Port in der Anlage als Telefon mit Tonwahl eingerichtet und darf er intern anrufen?</li>"
        "<li>Sind die Klemmen „Amt a/b“ (nicht „TLN“) mit dem Port verbunden?</li></ul>"),
    "js.unsaved.one": ("1 call button assignment not yet saved in the gateway (entry {list}).",
                       "1 Ruftasten-Zuordnung noch nicht im Gateway gespeichert (Eintrag {list})."),
    "js.unsaved": ("{n} call button assignments not yet saved in the gateway (entries {list}).",
                   "{n} Ruftasten-Zuordnungen noch nicht im Gateway gespeichert (Einträge {list})."),
    "js.unsaved_log": ("Stop logging first.", "Vorher das Loggen beenden."),
    "js.assigned": ("Call button assigned – please save the phonebook to the gateway",
                    "Ruftaste zugeordnet – bitte das Telefonbuch in das Gateway speichern"),
    "js.typ.S": ("sends", "sendet"),
    "js.typ.E": ("receives", "empfängt"),
    "js.typ.T": ("calls", "ruft"),
    "js.assign": ("Assign …", "Zuordnen …"),
    "js.ping_sent": ("Test output requested – expected: “S: 90 …” and “PIC Release …”",
                     "Testausgabe angefordert – erwartet: „S: 90 …“ und „PIC Release …“"),
    "js.src_loaded": ("Showing the data last loaded from the gateway (with your changes).",
                      "Angezeigt werden die zuletzt aus dem Gateway geladenen Daten (mit Ihren Änderungen)."),
    "js.src_default": ("Showing default values – first “Load from gateway” so nothing is overwritten.",
                       "Angezeigt werden Standardwerte – zuerst „Aus Gateway laden“, damit nichts überschrieben wird."),
    "js.no_connection": ("no connection", "keine Verbindung"),
    "js.not_checked": ("not checked", "nicht geprüft"),
    "js.bl_only": ("bootloader only", "nur Bootlader"),
    "js.not_present": ("not present", "nicht vorhanden"),
    "js.fw_ok": ("Firmware and bus driver present.", "Firmware und Bustreiber vorhanden."),
    "js.fw_bl": ("Bootloader only – please transfer a firmware (.tsk).",
                 "Nur Bootlader – bitte Firmware (.tsk) übertragen."),
    "js.fw_nobt": ("No bus driver – please transfer a bus driver (.hex).",
                   "Kein Bustreiber – bitte Bustreiber (.hex) übertragen."),
    "js.bootloader": ("Bootloader", "Bootlader"),
    "js.select_file": ("Please select a file first", "Bitte zuerst eine Datei auswählen"),
    "js.confirm_fw": ("Do you really want to transfer the firmware “{file}”?\n\nThe firmware in the gateway is "
                      "erased immediately. Do not disconnect until the end.",
                      "Möchten Sie die Firmware „{file}“ wirklich übertragen?\n\nDie Firmware im Gateway wird dabei "
                      "sofort gelöscht. Bitte die Verbindung bis zum Ende nicht trennen."),
    "js.confirm_bt": ("Do you really want to transfer the bus driver “{file}”?\n\nThe bus driver in the gateway "
                      "is erased immediately. Do not disconnect until the end.",
                      "Möchten Sie den Bustreiber „{file}“ wirklich übertragen?\n\nDer Bustreiber im Gateway wird "
                      "dabei sofort gelöscht. Bitte die Verbindung bis zum Ende nicht trennen."),
    "js.confirm_defaults": ("Do you really want to reset the configuration to factory settings?",
                            "Möchten Sie wirklich die Konfiguration auf Werkseinstellung zurücksetzen?"),
    "js.defaults_loaded": ("Factory settings loaded – please transfer them with “Save to gateway”",
                           "Werkseinstellungen geladen – bitte mit „In Gateway speichern“ übertragen"),
    "js.confirm_pb_clear": ("Do you really want to clear the phonebook?\nNote: you will have to assign all call "
                            "buttons again!",
                            "Möchten Sie wirklich das Telefonbuch löschen?\nAchtung: Sie müssen alle Ruftasten neu "
                            "zuordnen!"),
    "js.pb_cleared": ("Phonebook cleared – please transfer it with “Save to gateway”",
                      "Telefonbuch gelöscht – bitte mit „In Gateway speichern“ übertragen"),
    "js.confirm_bl": ("Send bootloader reset?\nOnly works when the gateway is in the bootloader.",
                      "Bootlader-Reset senden?\nWirkt nur, wenn das Gateway im Bootlader steht."),
    "js.file_loaded": ("File loaded: {file} – not yet saved to the gateway",
                       "Datei geladen: {file} – noch nicht im Gateway gespeichert"),
    "js.logging": ("Logging", "Loggen läuft"),
    "js.server_lost": ("Connection to the server lost: {err}", "Verbindung zum Server verloren: {err}"),
    "js.stop": ("Stop", "Stop"),
    "js.start": ("Start", "Start"),

    # phone codes table: action, code, note (code column is language independent where possible)
    "js.code.unlock": ("Unlock programming", "Programmierung freischalten"),
    "js.code.unlock.n": ("the codes with * follow (same call)", "danach folgen die Codes mit * (gleiche Verbindung)"),
    "js.code.number": ("Enter phone number", "Telefonnummer eintragen"),
    "js.code.number.c": ("* 1 * index * no. V1 * no. V2 * AM #", "* 1 * Index * Nr. V1 * Nr. V2 * AB #"),
    "js.code.number.n": ("index 01–50, AM 0–3", "Index 01–50, AB 0–3"),
    "js.code.button": ("Assign call button (control unit)", "Ruftaste zuordnen (Steuergerät)"),
    "js.code.button.c": ("* 2 * door station * index #", "* 2 * Türstation * Index #"),
    "js.code.button.n": ("control unit in programming mode, waits 3 s",
                         "Steuergerät im Programmiermodus, wartet 3 s"),
    "js.code.passive": ("Assign call button (passive)", "Ruftaste zuordnen (passiv)"),
    "js.code.passive.c": ("* 7 * door station * index #", "* 7 * Türstation * Index #"),
    "js.code.passive.n": ("ring at the door within 15 s", "innerhalb von 15 s an der Tür klingeln"),
    "js.code.type": ("Connection type", "Anschlussart"),
    "js.code.type.n": ("0 = direct line, 1 = PBX extension", "0 = Amt, 1 = Nebenstelle"),
    "js.code.local": ("Local ring time", "Lokale Rufzeit"),
    "js.code.secs3": ("three digits in seconds, e.g. 030", "dreistellig in Sekunden, z. B. 030"),
    "js.code.external": ("External ring time", "Externe Rufzeit"),
    "js.code.secs": ("three digits in seconds", "dreistellig in Sekunden"),
    "js.code.talk": ("Door talk time", "Türgesprächszeit"),
    "js.code.listen": ("Listen in", "Mithören"),
    "js.code.onoff": ("0 = off, 1 = on", "0 = aus, 1 = an"),
    "js.code.pin": ("Change PIN", "PIN ändern"),
    "js.code.pin.c": ("* 9 * new PIN * new PIN #", "* 9 * neue PIN * neue PIN #"),
    "js.code.pin.n": ("four digits", "vierstellig"),
    "js.code.master_nr": ("Master redirect number", "Masterumleitungsnummer"),
    "js.code.master_nr.c": ("R * 1 * number #", "R * 1 * Nummer #"),
    "js.code.master_nr.n": ("without PIN; an empty number deletes it", "ohne PIN; leere Nummer löscht"),
    "js.code.master_ab": ("Master redirect number with AM", "Masterumleitungsnummer mit AB"),
    "js.code.master_ab.c": ("R * 1 * number * 1 #", "R * 1 * Nummer * 1 #"),
    "js.code.master_ab.n": ("additionally sets the answering machine flag",
                            "setzt zusätzlich die Anrufbeantworter-Kennung"),
    "js.code.master": ("Master redirect", "Masterumleitung"),
    "js.code.master.n": ("0 = off, 1 = delayed, 2 = immediate", "0 = aus, 1 = verzögert, 2 = sofort"),
    "js.code.variant": ("Switch variant", "Variante umschalten"),
    "js.code.variant.n": ("1 = day, 2 = night", "1 = Tag, 2 = Nacht"),
    "js.code.actuator": ("Execute switching actuator", "Schaltaktor ausführen"),
    "js.code.actuator.c": ("R # number", "R # Nummer"),
    "js.code.actuator.n": ("assignment: programming mode at control unit and actuator",
                           "Zuordnung: Programmiermodus an Steuergerät und Aktor"),
    "js.code.door": ("Open door (during/after door conversation)", "Tür öffnen (im/nach Türgespräch)"),
    "js.code.door.n": ("opens the door that rang; after 2 min (or 30 s after the conversation) the main door",
                       "öffnet die Tür, von der geklingelt wurde; nach 2 min (bzw. 30 s nach dem Gespräch) die "
                       "Haupttür"),
    "js.code.door2": ("Open door without conversation", "Tür öffnen ohne Gespräch"),
    "js.code.door2.c": ("R # door station", "R # Türstation"),
    "js.code.door2.n": ("direct line: pick up, R key. PBX: call the gateway, then # + number of the door station "
                        "(1–9)",
                        "Amtsanschluss: Hörer ab, R-Taste. Telefonanlage: Gateway anrufen, dann # + Nummer der "
                        "Türstation (1–9)"),
    "js.code.reset": ("Factory reset", "Werksreset"),
    "js.code.reset.n": ("deletes configuration AND phonebook completely; back up first",
                        "löscht Konfiguration UND Telefonbuch komplett; vorher sichern"),
}
