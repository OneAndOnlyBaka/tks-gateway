# Gira TK-Gateway 1290 00 – Protokoll des Programmiersets

> German translation. The primary, maintained version is [PROTOCOL.md](PROTOCOL.md) (English).

Rekonstruiert aus der Original-Inbetriebnahmesoftware V1.01 (`TK_Gateway.exe`,
VB6 Native Code, 28.11.2005) durch Disassemblierung. Die Bezeichnungen in
Klammern sind die Prozedurnamen aus dem Original.

## Schnittstelle

* 19200 Baud, 8 Datenbits, keine Parität, 1 Stoppbit, kein Handshake
  (aus den persistierten MSComm-Eigenschaften des Formulars `frm_Kommunikation`)
* Vor jedem Befehl leert die Software den Empfangspuffer.

## Anschlüsse und Pinbelegung

### Klemmen des TK-Gateways (laut Handbuch 12901310, S. 8–9)

Reiheneinbaugerät, 6 TE. Schraubklemmen an der Unterseite, von links nach rechts:

| Klemme | Funktion |
|---|---|
| `Ub` (2 Klemmen) | Versorgung 12–24 V DC oder 12 V AC (Steuergerät, TKS-Netzteil 24 V DC oder Klingeltrafo) |
| `Amt a/b` | analoger Telefonanschluss bzw. analoger Nebenstellenport einer TK-Anlage |
| `TLN a'/b'` | analoges Tonwahl-Telefon (DTMF-Programmierung, Amtsbetrieb) |
| `BUS` (2 Klemmen) | 2-Draht-Bus des Gira Türkommunikations-Systems |

LEDs: grün „Betrieb“ (an = Normalbetrieb, blinkt = Programmiermodus des TKS),
gelb „TLN aktiv“ (Gespräch über TLN). Rechts neben den LEDs befindet sich ein
quadratisches Feld, vermutlich die Abdeckung der Buchse für das Programmierset.

### Programmierschnittstelle (Programmierset 1291 00)

Laut offizieller Anleitung der Inbetriebnahmesoftware ([12911310.pdf](https://partner4.gira.com/data3/12911310.pdf))
steckt der „Jack Western-Stecker“ des Kabels in der Buchse des TK-Gateways,
das andere Ende (RS232) am COM-Port des PCs. Im Kabel sitzt ein Pegelwandler,
zwei Drähte reichen also nicht.

#### Belegung des Programmiersteckers (RJ10, 4P4C, Gateway-Seite)

Quelle: Nutzer *MarkF-081* im [KNX-User-Forum, Thread 8264](https://knx-user-forum.de/forum/öffentlicher-bereich/knx-eib-forum/8264-steckerbelegung-gira-tk-gateway-programmierkabel)
(23.02.2020). Von Gira nicht bestätigt. Zwei weitere Nutzer berichten im selben
Thread, dass ihre USB-TTL-Adapter (CH340G, PL2303) damit am Gateway funktionieren.

| Pin | Signal | Richtung | Bemerkung |
|---|---|---|---|
| 1 | GND | – | Masse |
| 2 | +5 V | Gateway → Kabel | versorgt den Pegelwandler im Kabel |
| 3 | RxD (aus PC-Sicht) | Gateway → PC | **TTL**, Sendeausgang des Gateways |
| 4 | TxD (aus PC-Sicht) | PC → Gateway | **TTL**, Empfangseingang des Gateways |

Original-Kabel: D-Sub-9-Buchse am PC, GND auf Pin 5. Die +5 V versorgen einen
MAX232, der die TTL-Signale auf Pin 2 (RxD) bzw. Pin 3 (TxD) des COM-Ports umsetzt.

Die Zählrichtung der RJ10-Kontakte ist im Forum nicht angegeben. Vor dem
Anschließen deshalb messen. Das ist einfach, weil das Gateway selbst +5 V liefert:

1. Gateway versorgen (`Ub`), Stecker oder Buchse von vorn betrachten.
2. Die beiden Kontakte mit etwa **5 V** Gleichspannung zueinander sind GND (Pin 1) und +5 V (Pin 2).
3. Der Sendeausgang des Gateways (Pin 3) liegt im Ruhezustand ebenfalls auf etwa 5 V gegen GND (UART-Ruhepegel High).
4. Der verbleibende Kontakt ist Pin 4 (Eingang des Gateways).

#### Anschluss an einen USB-TTL-Adapter (z. B. FTDI FT232R / Waveshare)

| Gateway (RJ10) | Adapter |
|---|---|
| Pin 1 GND | GND |
| Pin 2 +5 V | **nicht verbinden** (beide Seiten haben eigene Versorgung) |
| Pin 3 (Gateway sendet) | RXD |
| Pin 4 (Gateway empfängt) | TXD |

* Den **TTL**-Ausgang des Konverters verwenden, **nicht** RS232 oder RS485.
  ±12 V am TTL-Eingang können den Controller des Gateways zerstören.
* Die I/O-Spannung des Adapters auf **5 V** stellen (Waveshare: Jumper bzw.
  Schalter VCCIO 5 V/3,3 V). 3,3 V wird vom 5-V-Gateway oft noch erkannt,
  5 V ist aber der passende Pegel.
* Kommt auf `i` keine Antwort: TX und RX tauschen. Laut Forum sind diese bei
  manchen Modulen vertauscht beschriftet.

Ergänzend gesichert aus Software und Firmware:

| Eigenschaft | Wert | Quelle |
|---|---|---|
| Datenformat | 19200 Baud, 8N1 | MSComm-Eigenschaften der Software, Firmware (`TH1=FCh`, `SMOD=1`, Quarz 14,7456 MHz) |
| Handshake | keiner (Software nutzt nur TxD/RxD) | Software sendet/liest ausschließlich `Output`/`Input` |
| Controller-Seite | interne UART des 8051 (`TxD`/`RxD` an P3.1/P3.0, TTL-Pegel am Controller) | Firmware: Timer 1 im Baudraten-Modus, serieller Interrupt-Vektor 0x0023 |

Prüfen der Verbindung: `tks-gateway -p /dev/ttyUSB0 version` bzw. in der
Oberfläche „Firmwarestand auslesen“. Erwartet wird eine Zeile mit
`Gira TK Koppler Version 01.26` (Text aus der Firmware, Adresse 0x4DCB).

## Befehle

Ein Befehl ist ein Buchstabe, gefolgt von `CR` (0x0D). Die Firmware
(`tkg_126.tsk`, Befehlsverteiler ab 0x0DEF) sammelt empfangene Zeichen in einem
Zeilenpuffer, wandelt `A`–`Z` in Kleinbuchstaben, verwirft Zeichen unter `'0'`
und wertet beim `CR` das erste Pufferzeichen aus. Groß-/Kleinschreibung ist
daher egal; die Software sendet `U` und `D` groß.

| Befehl | Funktion (Original) | Antwort |
|---|---|---|
| `i\r` | Firmwarestand auslesen (`FirmwareAuslesenSenden`) | `Gira TK Koppler Version 01.26 ` sofort, dann nach Bus-Abfrage des PIC `PIC Release NNNN` + `CR LF`; **ohne Bustreiber kein CR LF** |
| `u\r` | Konfiguration/Telefonbuch laden (`KonfigurationLadenInitSenden`) | XMODEM, Gateway sendet 6144 Byte |
| `d\r` | Konfiguration/Telefonbuch speichern (`KonfigurationSendenInitSenden`) | XMODEM, PC sendet 6144 Byte |
| `s\r` | Firmware übertragen (`FirmwareInitSenden`) | XMODEM, PC sendet `.tsk` unverändert |
| `p\r` | Bustreiber übertragen (`BustreiberInitSenden`) | XMODEM, PC sendet `.hex` unverändert |
| `z T NN\r` | Ruftaste zuordnen: `T` = Türstation 1–9, `NN` = Telefonbuchindex 01–50 (`RuftastenInformationAbholenSenden`) | `XX XX XX XX XX ` + `CR LF` (17 Zeichen; Busadresse des Türrufs) |
| `t\r` | Loggen ein (`LoggenEinSenden`) | fortlaufend Textzeilen |
| `n\r` | Loggen aus (`LoggenAusSenden`) | – |

Mehr Befehle kennt die Firmware 1.26 über die serielle Schnittstelle nicht
(vollständige Analyse siehe nächster Abschnitt).

### Vollständige Analyse der TTL-Schnittstelle (Firmware 1.26)

Untersucht wurde der gesamte Empfangspfad, nicht nur eine Mustersuche:

1. **Interrupt-Routine** (Vektor 0x0023 → 0x509D): Im Ruhezustand landet jedes
   Byte einzeln in `0x8000` und setzt ein Flag. In den Übertragungszuständen
   sammelt sie ab `SOH` ein 132-Byte-Paket mit Timeout. Es gibt **keine**
   Sonderbehandlung von Bytes (kein Escape, keine Break-Erkennung, keine
   „magischen“ Sequenzen).
2. **Zeilenpuffer** (0x0DEF): `0x8C00`, Groß- in Kleinbuchstaben, Zeichen
   < `'0'` verworfen. Beim `CR` wird nur das **erste** Zeichen ausgewertet.
   Argumente liest nur `z`, alle anderen Befehle ignorieren den Rest der Zeile.
3. **Befehlsverteiler**: genau `i z t n s u d p`. Für alles andere ein `RET` ohne Wirkung.
4. **Übertragungszustände** (`32h`, Handler 0x0F4B): nur XMODEM senden (`u`)
   bzw. empfangen (`d`, `p`); erkannt werden nur `ACK`/`NAK`/`CAN`/`EOT`/`SOH`.
5. **Feste Adressen, kein Speicherzugriff**: `u` liest immer `0xA000–0xB7FF`
   (RAM-Spiegel des EEPROMs, 6144 Byte – physisch ein Sektor des
   gebankten Flash, siehe [HARDWARE.md](HARDWARE.md#memory-map)), `d` schreibt immer über den Puffer
   `0xC000`. Es gibt keinen Peek/Poke- oder Speicherdump-Befehl mit Adresse.
6. **`d` übernimmt nur vollständige Abbilder**: Nur wenn genau 48 Blöcke
   empfangen wurden, kopiert die Firmware `0xC000–0xD7FF` nach `0xA000` und
   speichert ins EEPROM (0x1115). Sonst quittiert sie, verwirft aber die Daten.
7. **`p` (Bustreiber)**: Die 8051-Firmware parst die Intel-HEX-Datei selbst
   (`:`-Zeilen, Puffer `0x8400`). PIC-Adressen `0x4000`/`0x4200`
   (Konfiguration/EEPROM) werden auf `0xD000`/`0xD100` abgebildet, der
   Programmspeicher auf `0xC000`. Danach wird der PIC per Bit-Banging programmiert.
8. **`s` (Firmware)**: Kopiert Flash-Routinen aus 0x12AD ins RAM (`0x8100`):
   Löschen und Programmieren nach JEDEC (`AA`/`55` an `5555h`/`2AAAh`),
   Bankumschaltung über ein Latch bei `XDATA 0x0000`. Dann löscht sie die
   Firmware-Bank und übergibt an den Boot-Code. Der Boot-Code selbst (der `s`
   und `r` ohne CR versteht) liegt in einem anderen Flash-Bereich und ist
   **nicht** in der `.tsk` enthalten. Ob er weitere Befehle kennt, lässt sich
   nur mit einem Auslesen des Flash-Bausteins klären.
9. **`t`/`n` (Log)**: Setzt nur das Flag `35h`. Ausgabe: `S: ` / `E: ` +
   9 Telegrammbytes (`XX `) bzw. `T: DIAL  ` / `T: LOCAL ` + Index, Variante,
   AB-Flag + `- ` + Rufnummer. Im Logmodus gelten dieselben Befehle.
   Das Flag liegt im RAM und überlebt einen Neustart des PCs: Verschwindet PC
   oder Container während des Loggens, loggt das Gateway bis zu `n` oder einem
   Neustart weiter. Antworten sind dann mit Logzeilen vermischt (z. B. `i` →
   `…Version 01.26 S: 90 …` CR LF, `PIC Release 0101` erst in der nächsten
   Zeile), was wie ein fehlender Bustreiber aussieht. tks-gateway sendet deshalb
   nach dem Öffnen der Schnittstelle `n`, verwirft ausstehende Ausgaben und
   überspringt Logzeilen in Antworten.

10. **Konfigurationsbytes ohne Funktion**: Die Firmware wertet im
    Konfigurationsbereich nur die bekannten Felder aus (`0x01`, `0x02`, `0x06`,
    `0x0A`, `0x0E`, `0x0F`, `0x10`, `0x15`, `0x40`, `0x41`; direkt über DPTR und
    indirekt über die Seite `0xA0`). Byte `0x00` und `0x16–0x3F`/`0x5A–0xFF`
    werden nie gelesen, es gibt also keine versteckten Konfigurationsschalter.
11. **`p` löscht den Bustreiber sofort**: Vor dem Datenempfang führt die
    Firmware (0x0EA1) die PIC16-Prozedur „Code-Schutz aufheben“ aus
    (Konfiguration laden, 7 × Adresse erhöhen, Kommandos `01`/`07`/`08`,
    Wartezeit, `01`/`07`). Das löscht den PIC vollständig. Bricht die Übertragung
    danach ab, funktioniert der Bus erst nach einem erfolgreichen neuen Upload
    wieder. Analog löscht `s` die Gateway-Firmware. **`p`/`P`/`s`/`S` nie ohne
    Datei senden.**

**Gegenprobe am Gerät (Firmware 01.26, PIC 0101, ohne Bus):** Alle Zeichen
`0`–`~` + CR außer `s S p P d D u U z Z` gesendet. Antwort kam nur auf `i` und `I`
(Großbuchstaben werden umgewandelt). Bei eingeschaltetem Log (`T`) erscheint
dabei `S: 90 00 00 00 00 00 00 00 00`, das Bus-Telegramm der PIC-Abfrage.

**Fazit:** Über die TTL-Schnittstelle gibt es außer den acht Befehlen keine
versteckten Kommandos. Insbesondere kann man darüber keine DTMF-Codes eingeben,
keinen Speicher lesen oder schreiben und keine Bus-Telegramme senden. Eine
Sendefunktion besteht nur indirekt (`i` → `0x90`, `z` → `0x05`). Offen ist
nur der Boot-Code.

Nur der **Bootloader** (nicht in der `.tsk` enthalten) versteht einzelne Zeichen
ohne `CR`:

| Zeichen | Funktion |
|---|---|
| `s` | Firmware übertragen (Software nutzt das, wenn die Version „Bootlader“ enthält) |
| `r` | Bootloader-Reset/Neustart (`BootladerResettenSenden`, nur über versteckte Bedienung erreichbar, s. u.) |

`z T NN` entspricht dem DTMF-Code `*2*Türstation*Index#`. Die Firmware
prüft `NN` auf 1–50, die Türstation `T` dagegen gar nicht. Sie wird nur
lokal im Eintrag gespeichert (Offset +8) und nicht auf den Bus gesendet.

Am Gerät beobachtet (eingeschaltetes Log): `z105` → `S: 05 04 00 …`,
`z920` → `S: 05 13 00 …`. Das Gateway sendet also Telegramm `05` mit dem
**Telefonbuch-Index − 1** (0-basiert). Dann wartet es 2–3 s
(`58h` = 3 Ticks à 1 s). Ohne Antwort gibt es **keine** serielle Meldung, und das
Abbild bleibt unverändert (vor/nach den Tests verglichen).

#### Passives Anlernen über die serielle Schnittstelle? (geprüft)

* **Kein eigener Befehl.** Den Lernzustand (`04D2`, nur in `0x14BB` gesetzt)
  betreten genau zwei Stellen: `0x0882` (DTMF `*2`/`*7`) und `0x0F47` (seriell
  `z`). Der passive Zweig ohne Telegramm (`*7`, 15 s) ist nur aus dem DTMF-Menü
  erreichbar (`0x0703`). Das Menü wird ausschließlich vom DTMF-Empfänger gespeist.
  Der `z`-Pfad sendet immer Telegramm `05` (Flag `30h`) und lernt immer 3 Ticks.
* **Aber `z` lernt nicht nur die Antwort auf `05`.** Die Lernbedingung
  (`0x0C93`–`0x0CA2`) prüft nur Telegrammcode `0x11` (Türruf) und Zustand
  `04D2`, keinen Absender. Jeder Türruf im Fenster wird übernommen, auch ein
  normales Klingeln ohne Programmiermodus. Ein erneutes `z` startet das Fenster
  neu (`0x14BB` setzt Zustand und Zähler zurück), sendet dabei aber jedes Mal
  wieder `05`.
* **Rein passiv, ohne Bus-Telegramm**, geht es nur zusammengesetzt: Log
  einschalten (`t`), Türruf `E: 11 …` mitlesen, Adresse ins Abbild eintragen und
  mit `d` schreiben. So arbeitet Weg B („Per Mitschnitt“) der Weboberfläche.

Versionstext: enthält er „Bootlader“, ist keine Firmware installiert; fehlt
„PIC“, ist kein Bustreiber installiert.

Die Ruftasten-Antwort liefert 5 Byte als Hex-Paare an den Positionen 1, 4, 7,
10, 13; die Software ergänzt `00-00-00` zum 8-Byte-Tastercode.

## XMODEM

Standard-XMODEM mit Summenprüfsumme:

* Block: `SOH(0x01)`, Blocknummer `n` (ab 1, mod 256), `255-n`, 128 Datenbytes
  (letzter Block mit `0x1A` aufgefüllt), Summe der Datenbytes mod 256 (`BlockSenden`, `csum`)
* Quittungen: `ACK 0x06`, `NAK 0x15`; Ende `EOT 0x04`; Abbruch 3 × `CAN 0x18`
* PC sendet: wartet auf `NAK` des Gateways, dann Blöcke, nach dem letzten `EOT`, wartet auf `ACK`.
* PC empfängt: sendet im Sekundentakt `NAK` („Warte auf Daten. Noch n Sekunden“),
  prüft jedes 132-Byte-Paket, `ACK`/`NAK`; nach 3 Fehlern Abbruch mit `CAN`.
  Nach Block 48 wird `EOT` erwartet und mit `ACK` quittiert.
* Gesamt-Timeout im Original: 60 s.

## Speicherabbild (6144 Byte)

Offsets 0-basiert. Text: ASCII, mit 0x00 aufgefüllt; Lesen endet an 0x00/0xFF
(Rufnummern, Zeiten, PIN zusätzlich an `A`).

### Konfiguration 0x000–0x0FF

| Offset | Länge | Inhalt |
|---|---|---|
| 0x00 | 1 | unbekannt (wird erhalten) |
| 0x01 | 1 | Anschlussart: 0 = Amtsanschluss, sonst Nebenstelle |
| 0x02 | 4 | lokale Rufzeit (Sekunden, ASCII, max. 120) |
| 0x06 | 4 | externe Rufzeit |
| 0x0A | 4 | Türgesprächszeit |
| 0x0E | 1 | Variante: 0 = 1 (Tag), sonst 2 (Nacht) |
| 0x0F | 1 | Mithören: 0 = aus, sonst an |
| 0x10 | 5 | PIN (4 Ziffern + 0x00) |
| 0x15 | 1 | Masterumleitung: 0 aus, 1 verzögert, 2 sofort |
| 0x16 | 42 | unbekannt (wird erhalten) |
| 0x40 | 1 | Anrufbeantworter der Masterumleitung: `A` an, ` ` aus |
| 0x41 | 25 | Masterumleitungsnummer |
| 0x5A | 166 | unbekannt (wird erhalten) |

Werkseinstellung: Nebenstelle, Rufzeiten 030/030, Türgesprächszeit 060,
Variante 1, Mithören aus, PIN 0000, Masterumleitung aus.

Ergänzungen aus Handbuch (12901310) und Software-Anleitung (12911310):

* Alle drei Zeiten: max. 120 s.
* Rufnummern (Telefonbuch und Masterumleitung): **max. 24 Zeichen**, obwohl
  das Feld 25 Byte hat. Erlaubt sind Ziffern, `*`, `#` sowie die Sonderzeichen
  `P` (Wählpause ~1 s), `F` (Flash 100 ms + Pause) und `f` (Flash 80 ms + Pause).
  Die Sonderzeichen lassen sich nur per Software eingeben, nicht per Telefon.
  Eine leere Nummer bedeutet: Türruf an das Telefon an TLN.
* **Mithören (0x0F)** wird weder im Handbuch noch in der Software-Anleitung
  erklärt. Gira nennt in der Produktbeschreibung als Merkmal eine
  „Mithörsperre“ („Ruf und Gesprächsdauer einstellbar. Mithörsperre.“). Der
  Schalter ist vermutlich dafür gedacht (Aus = Sperre aktiv = Werkseinstellung).
  Weitere Belege: In der Originalsoftware haben nur diese beiden Optionen keinen
  Hilfetext in der Statuszeile. Sonst wird der Wert nur gelesen, angezeigt und
  gespeichert (0x4297D0, 0x42E3D0, 0x421F00, 0x430C20) und an nichts geknüpft. Die Firmware 1.26 beschreibt das Byte nur (`*8`, 0x0709), liest es
  aber nirgends, weder direkt noch indirekt über die Seite 0xA0. Die Einstellung
  ist damit wirkungslos.
* **Unbekannte Klingeln werden ignoriert**, auch bei aktiver Masterumleitung:
  Ein Türruf, dessen Adresse nicht im Telefonbuch steht, endet nach der Suche
  (0x0CE8 → 0x0DA0 → `JZ 0x0D21`) ohne Anruf. Klingeln müssen also immer
  angelernt sein.
* **Annahme eingehender Anrufe** (Nebenstellenbetrieb, beobachtet an einem
  Grandstream HT801 mit Klingelrhythmus 2 s an / 4 s aus): Das Gateway nimmt
  nach 12,4 s bzw. 18,4 s ab, also beim 3. oder 4. Klingeln. Danach folgt der
  Kommando-Ton: zwei kurze Töne (~425 Hz), etwa alle 5,5 s wiederholt. Das
  passt zum Symbol im Handbuch (S. 15). Für die Zahl der Klingelzeichen gibt es
  **keinen Konfigurationsparameter**, sie ist in der Firmware fest. Die
  Anlage darf den Ruf deshalb nicht vor ca. 20 s abbrechen.
* **Kommandomodus-Zeitgrenze 60 s** (Firmware): Nach dem Abheben startet
  `0x13EB` den Kommando-Ton und setzt `58h = 3Ch` (60 Ticks à 1 s). Jede
  DTMF-Taste setzt die Zeit neu (`0x0596`). Erst nach 60 s ohne Eingabe legt
  das Gateway auf (`0x056E` → `21h = 41h` → Ruhezustand `0x13C5`). Eine
  Erkennung „Anrufer hat aufgelegt“ wurde in diesem Zustand nicht gefunden
  (nicht abschließend geprüft). Folge: Ein erneuter Anruf innerhalb dieser Zeit
  ergibt **besetzt**.
* Das Gateway wählt nur nach außen, wenn ein Türruf einer **angelernten**
  Klingel über den Bus kommt. Ohne Bus wählt es nie. Es gibt auch keinen
  Telefon- oder seriellen Befehl, der einen Anruf auslöst.
* Ruftaste zuordnen (Original): Programmiermodus mit 3 s „Systemprogr.“ am
  Steuergerät, Ruftasten jeweils 3 s bis zum kurzen Quittierton in der
  Reihenfolge der Einträge drücken, dann je Eintrag „Ruftaste zuordnen“, am Ende
  „Systemprogr.“ kurz drücken. **Hält man eine Ruftaste nach dem Quittierton
  weitere 3 s, löscht das alle Zuordnungen der Türstation.**

### Telefonbuch 0x100 + 64·i (i = 0…49)

| Offset | Länge | Inhalt |
|---|---|---|
| +0 | 8 | Tastercode (Busadresse der Ruftaste; ≠ 0 → „gefangen“) |
| +8 | 1 | Türstation als ASCII `1`…`9`, 0x00 = keine |
| +9 | 1 | 0x00 |
| +10 | 1 | Anrufbeantworter Variante 1: `A` / ` ` |
| +11 | 25 | Telefonnummer Variante 1 |
| +36 | 1 | Anrufbeantworter Variante 2: `A` / ` ` |
| +37 | 25 | Telefonnummer Variante 2 |
| +62 | 2 | 0x00 |

0x0D80–0x0FFF: 0x00.
Bezeichnungen: 0x1000 + 20·i, je 20 Byte. Danach bis 0x17FF: 0x00.

Beim Speichern liest die Software zuerst das aktuelle Abbild und ersetzt nur
den bearbeiteten Bereich (Konfiguration oder Telefonbuch).

Eine verzögerte Masterumleitung ist nicht erlaubt, wenn in einem Eintrag die
Anrufbeantworterfunktion aktiv ist.

## Bus-Log

Textzeilen mit `CR LF`. Position 1 (1-basiert): `S` Gateway sendet, `E`
Gateway empfängt, `T` Gateway ruft. Pos. 4–5 Telegrammcode, Pos. 7–14
Busadresse, Pos. 16–17 Datenbyte/Subadresse.

| Typ | Code | Bedeutung |
|---|---|---|
| S | 12 / 21 / 22 / 20 / 31 | Internruf an / Türgesprächsbeginn / Interngesprächsbeginn / Gesprächsende / Tür öffnen |
| S | 42 | Schaltfunktion EIN (Daten `FF`) / AUS |
| S | 81 / 82 | Prüfgerätemodus EIN / AUS |
| S | A0 / A1 | Audioeingang TLN / Sendestufe an Bus EIN/AUS (Pos. 7–8 `FF` = EIN) |
| S | A2 / A3 | Reset des Systems / Ruf im Telefonbuch bekannt |
| E | 20 / 11 / 12 / 21 / 22 | Gesprächsende / Türruf / Internruf / Türrufannahme / Internrufannahme |
| E | 01 / 00 / 03 / 02 | Systemprogrammierung EIN/AUS, Aktorprogrammierung EIN/AUS |
| T | – | Pos. 10–11 Telefonbuchindex (hex, `00` = Masterumleitung), Pos. 13–14 Variante, `LOCAL`/`DIAL '<nr>'`, am Ende AB-Flag |

Die Feldpositionen der `T`-Zeilen sind nur teilweise gesichert.

**Bezug zum Busrahmen (GDoor).** Laut der unabhängigen
[GDoor-Dokumentation](https://gdoor-org.github.io/documentation/protocol.html) ist ein TKS-Busrahmen
`Länge/Flags · Status · Aktion · Quelle (3) · Parameter (2) · Gerätetyp ·
[Ziel (3)] · Prüfsumme`. Die `S:`/`E:`-Zeilen beginnen mit dem Aktionsbyte; die
Bytes danach sind die Quelladresse (3 Byte) und der Parameter (z. B.
Tastennummer). Der Tastercode eines Eintrags ist Quelladresse + Parameter
(Beispiel aus einer echten Sicherung: `CC-ED-19-83-00` = Türstation
`CC ED 19`, Tastenbyte `83`). `05` heißt bei GDoor CTRL_DOORSTATION_ACK
(„angelernte Klingeltaste bestätigen“), `21` AUDIO_REQUEST (danach liegt
analoger Ton auf dem Bus), `20` AUDIO_VIDEO_END. Details zur Bitübertragung:
[HARDWARE.md](HARDWARE.md#tks-bus-physical-layer).

## Versteckte und undokumentierte Funktionen

### Inbetriebnahmesoftware

* **Bootloader-Reset:** Reiter *Firmware*, Button „Auslesen“ fokussieren (Tab) und
  die Taste `r` drücken (KeyPress-Handler 0x416070). Die Software wartet 2,5 s, sendet `r` ohne
  CR, wartet 1 s und liest die Version neu. Das geht einmal pro Sitzung; wieder
  freigegeben wird es, wenn eine normale Firmware erkannt wurde. Bei laufender
  Firmware landet das `r` nur in deren Zeilenpuffer und verfälscht den nächsten
  Befehl.
* **`Debug_Fenster`:** Formular mit zwei Listen, wird aber nirgends geöffnet (toter Code).
  Das Modul `Versionshistory` enthält keinen Code.
* Sonst keine versteckten Tastenkombinationen, Passwörter oder Schalter. Die
  Formular-Events sind nur Load/Unload/Resize, MouseMove (Hilfetexte in der
  Statusleiste) und das Kontextmenü im Telefonbuch.

### Firmware (DTMF-Programmierung per Telefon)

DTMF-Menü nach `R * 0 * PIN #` (Verteiler ab 0x06CF; EEPROM-Spiegel ab 0xA000 = Abbild-Offset):

| Code | Handbuch | Wirkung (Offset) |
|---|---|---|
| `*1*…` | ja | Telefonbuch |
| `*2*T*NN#` | ja | Ruftaste zuordnen: sendet Bus-Telegramm `05`, wartet 3 s auf einen Türruf |
| `*3*K#` | ja | Anschlussart (0x01, K = 0/1) |
| `*4*/*5*/*6*ZZZ#` | ja | Rufzeiten / Türgesprächszeit (0x02 / 0x06 / 0x0A) |
| **`*7*T*NN#`** | **nein** | Ruftaste zuordnen **ohne** vorheriges Telegramm, wartet **15 s** auf einen Türruf |
| **`*8*K#`** | **nein** | **Mithören** (0x0F): K = 0 aus, 1 an |
| `*9*PIN*PIN#` | ja | PIN ändern (0x10) |

**Ablauf des Ruftasten-Lernens** (`*2`, `*7` und seriell `z T NN`, gemeinsamer Code ab 0x0C8B):
Die Firmware geht in einen Lernzustand (Handler 0x04D2) mit Countdown in `58h`
(1 Tick = 1 s; Timer 0 alle 5 ms × 200, Quarz 14,7456 MHz). Trifft in dieser Zeit
ein Bus-Telegramm mit Code `0x11` (Türruf) ein, werden dessen 5 Adressbytes als
Tastercode in Eintrag `NN` geschrieben, Türstation `T` an Offset +8, und das
EEPROM wird gespeichert. Danach folgen der positive Quittierton und bei `z` die
Hex-Zeile an den PC. Läuft die Zeit ab, kommt der negative Quittierton. `*2` und `z`
senden vorher das Bus-Telegramm `05` (Bedeutung aus der Firmware nicht ableitbar;
laut Handbuch ist der Programmiermodus am Steuergerät nötig). `*7` lauscht nur
passiv 15 s lang. Außerhalb des Lernzustands führt ein Türruf zur Suche im
Telefonbuch (0x0DA0) und bei einem Treffer zum Anruf.

Ebene ohne PIN (`R * x …`): `0` (PIN-Eingabe), `1`, `2`, `3`, `9` wie im Handbuch, mit einer Erweiterung:

* **`R * 1 * Nummer * 1 #`** setzt zusätzlich die Anrufbeantworter-Kennung der
  Masterumleitung (Offset 0x40 = `A`); `R * 1 * Nummer #` setzt sie zurück (` `).
  Das Handbuch nennt nur die zweite Form.

Werksreset `R * 9 * 1928374655 #` ist dokumentiert. Die Ziffernfolge steht als
Tabelle bei 0x08E5 in der Firmware. Die Routine 0x0986 setzt das **gesamte**
Abbild `0xA000–0xB7FF` auf 0x00 (Konfiguration, alle 50 Telefonbucheinträge,
alle Namen) und kopiert dann 22 Byte Standardkonfiguration aus 0x4DA8 zurück:
`00 01 "030" 00 "030" 00 "060" 00 00 00 "0000" 00 00`. Das entspricht genau den
Werkseinstellungen der Software (Nebenstelle, 030/030/060, Variante 1,
Mithören aus, PIN 0000, Masterumleitung aus). Danach wird ins EEPROM gespeichert.

Der Button **„Werkseinstellungen“ der Software** setzt dagegen nur die
Konfiguration zurück (`KonfigurationWerkseinstellungen`, 0x430C20). Das
Telefonbuch löscht man dort separat mit „Telefonbuch löschen“.

## Dateiformate der Originalsoftware

* `.gtk` – Konfiguration als Klartextbericht („Gira TK-Gatewaykonfiguration“, Werte bzw. `X`)
* `.gtb` – Telefonbuch-Grid, Zellen durch Tab, Zeilen durch CR getrennt;
  Spalten: Index, Teilnehmer, Nr. V1, Nr. V2, Anrufbeantworter (0–3), Türstation, frei/gefangen, Tastercode
* `.tsk` – Firmware (8051-Code), `.hex` – Bustreiber (PIC, Intel-HEX); beide werden unverändert übertragen
