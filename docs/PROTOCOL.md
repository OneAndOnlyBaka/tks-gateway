# Gira TK gateway 1290 00 – programming set protocol

Reconstructed by disassembling the original commissioning software V1.01
(`TK_Gateway.exe`, VB6 native code, 28 Nov 2005) and the gateway firmware 1.26
(`tkg_126.tsk`, 8051). Names in parentheses are the procedure names from the
original. (German version: [PROTOKOLL.md](PROTOKOLL.md).)

Related documents: [User guide](USER_GUIDE.md) · [UI reference](UI.md) · [Software architecture](ARCHITECTURE.md) · [Hardware overview](HARDWARE.md) · [README](../README.md)

## Interface

* 19200 baud, 8 data bits, no parity, 1 stop bit, no handshake
  (from the persisted MSComm properties of the form `frm_Kommunikation`)
* The software clears the receive buffer before each command.

## Connections and pinout

### Gateway terminals (manual 12901310, pp. 8–9)

DIN rail device, 6 modules. Screw terminals on the bottom, left to right:

| Terminal | Function |
|---|---|
| `Ub` (2 terminals) | supply 12–24 V DC or 12 V AC (control unit, TKS power supply 24 V DC or bell transformer) |
| `Amt a/b` | analogue telephone line or analogue extension port of a PBX |
| `TLN a'/b'` | analogue tone-dialling telephone (DTMF programming, direct line operation) |
| `BUS` (2 terminals) | 2-wire bus of the Gira door communication system (TKS) |

LEDs: green "Betrieb" (on = normal operation, flashing = TKS programming mode),
yellow "TLN aktiv" (call via TLN). To the right of the LEDs is a square field,
presumably the cover of the socket for the programming set.

### Programming interface (programming set 1291 00)

According to the official manual of the commissioning software
([12911310.pdf](https://partner4.gira.com/data3/12911310.pdf)) the cable's
"Western jack" plugs into the gateway socket and the other end (RS232) into the
PC's COM port. The cable contains a level converter, so two wires are not enough.

#### Pinout of the programming plug (RJ10, 4P4C, gateway side)

Source: user *MarkF-081* in the [KNX-User-Forum, thread 8264](https://knx-user-forum.de/forum/öffentlicher-bereich/knx-eib-forum/8264-steckerbelegung-gira-tk-gateway-programmierkabel)
(23 Feb 2020). Not confirmed by Gira. Two other users in the same thread report
that their USB-TTL adapters (CH340G, PL2303) work with the gateway this way.

| Pin | Signal | Direction | Note |
|---|---|---|---|
| 1 | GND | – | ground |
| 2 | +5 V | gateway → cable | powers the level converter in the cable |
| 3 | RxD (PC view) | gateway → PC | **TTL**, gateway transmit output |
| 4 | TxD (PC view) | PC → gateway | **TTL**, gateway receive input |

Original cable: D-sub 9 female at the PC, GND on pin 5. The +5 V supply a
MAX232 that converts the TTL signals to pin 2 (RxD) and pin 3 (TxD) of the COM port.

The forum does not state the counting direction of the RJ10 contacts. Measure
before connecting. This is easy because the gateway supplies +5 V itself:

1. Power the gateway (`Ub`), look at the plug or socket from the front.
2. The two contacts with about **5 V** DC between them are GND (pin 1) and +5 V (pin 2).
3. The gateway transmit output (pin 3) also sits at about 5 V against GND when idle (UART idle level high).
4. The remaining contact is pin 4 (gateway input).

#### Connecting a USB-TTL adapter (e.g. FTDI FT232R / Waveshare)

| Gateway (RJ10) | Adapter |
|---|---|
| pin 1 GND | GND |
| pin 2 +5 V | **do not connect** (both sides have their own supply) |
| pin 3 (gateway transmits) | RXD |
| pin 4 (gateway receives) | TXD |

* Use the **TTL** output of the converter, **not** RS232 or RS485.
  ±12 V on the TTL input can destroy the gateway's controller.
* Set the adapter I/O voltage to **5 V** (Waveshare: jumper or switch
  VCCIO 5 V/3.3 V). 3.3 V is often still recognised by the 5 V gateway, but 5 V
  is the proper level.
* If `i` gets no answer: swap TX and RX. According to the forum, some modules
  have them labelled the wrong way round.

Additionally confirmed from software and firmware:

| Property | Value | Source |
|---|---|---|
| Data format | 19200 baud, 8N1 | MSComm properties of the software, firmware (`TH1=FCh`, `SMOD=1`, crystal 14.7456 MHz) |
| Handshake | none (software uses TxD/RxD only) | software only uses `Output`/`Input` |
| Controller side | internal UART of the 8051 (`TxD`/`RxD` on P3.1/P3.0, TTL level at the controller) | firmware: timer 1 in baud rate mode, serial interrupt vector 0x0023 |

Checking the connection: `tks-gateway -p /dev/ttyUSB0 version` or "Read firmware
version" in the UI. Expected is a line with `Gira TK Koppler Version 01.26`
(text in the firmware at address 0x4DCB).

## Commands

A command is one letter followed by `CR` (0x0D). The firmware (`tkg_126.tsk`,
command dispatcher at 0x0DEF) collects received characters in a line buffer,
converts `A`–`Z` to lower case, drops characters below `'0'` and evaluates the
first buffer character on `CR`. Case therefore does not matter; the software
sends `U` and `D` in upper case.

| Command | Function (original) | Response |
|---|---|---|
| `i\r` | read firmware version (`FirmwareAuslesenSenden`) | `Gira TK Koppler Version 01.26 ` immediately, then after querying the PIC over the bus `PIC Release NNNN` + `CR LF`; **no CR LF without bus driver** |
| `u\r` | load configuration/phonebook (`KonfigurationLadenInitSenden`) | XMODEM, gateway sends 6144 bytes |
| `d\r` | save configuration/phonebook (`KonfigurationSendenInitSenden`) | XMODEM, PC sends 6144 bytes |
| `s\r` | transfer firmware (`FirmwareInitSenden`) | XMODEM, PC sends the `.tsk` unchanged |
| `p\r` | transfer bus driver (`BustreiberInitSenden`) | XMODEM, PC sends the `.hex` unchanged |
| `z T NN\r` | assign call button: `T` = door station 1–9, `NN` = phonebook index 01–50 (`RuftastenInformationAbholenSenden`) | `XX XX XX XX XX ` + `CR LF` (17 characters; bus address of the door call) |
| `t\r` | log on (`LoggenEinSenden`) | continuous text lines |
| `n\r` | log off (`LoggenAusSenden`) | – |

Firmware 1.26 knows no other commands on the serial interface (full analysis
in the next section).

### Full analysis of the TTL interface (firmware 1.26)

The whole receive path was examined, not just a pattern search:

1. **Interrupt routine** (vector 0x0023 → 0x509D): when idle, each byte lands
   individually in `0x8000` and sets a flag. In the transfer states it collects
   a 132-byte packet starting at `SOH`, with timeout. There is **no** special
   handling of bytes (no escape, no break detection, no "magic" sequences).
2. **Line buffer** (0x0DEF): `0x8C00`, upper case converted to lower case,
   characters < `'0'` dropped. On `CR` only the **first** character is
   evaluated. Only `z` reads arguments; all other commands ignore the rest of
   the line.
3. **Command dispatcher**: exactly `i z t n s u d p`. Anything else is a `RET`
   without effect.
4. **Transfer states** (`32h`, handler 0x0F4B): only XMODEM send (`u`) or
   receive (`d`, `p`); only `ACK`/`NAK`/`CAN`/`EOT`/`SOH` are recognised.
5. **Fixed addresses, no memory access**: `u` always reads `0xA000–0xB7FF`
   (RAM mirror of the EEPROM, 6144 bytes – physically a sector of the banked
   flash, see [HARDWARE.md](HARDWARE.md#memory-map)), `d` always writes via the buffer
   `0xC000`. There is no peek/poke or memory dump command with an address.
6. **`d` only accepts complete images**: only when exactly 48 blocks were
   received does the firmware copy `0xC000–0xD7FF` to `0xA000` and save to the
   EEPROM (0x1115). Otherwise it acknowledges but discards the data.
7. **`p` (bus driver)**: the 8051 firmware parses the Intel HEX file itself
   (`:` lines, buffer `0x8400`). PIC addresses `0x4000`/`0x4200`
   (configuration/EEPROM) are mapped to `0xD000`/`0xD100`, program memory to
   `0xC000`. The PIC is then programmed by bit-banging.
8. **`s` (firmware)**: copies flash routines from 0x12AD to RAM (`0x8100`):
   JEDEC erase and program (`AA`/`55` to `5555h`/`2AAAh`), bank switching via a
   latch at `XDATA 0x0000`. Then it erases the firmware bank and hands over to
   the boot code. The boot code itself (which understands `s` and `r` without
   CR) lives in another flash area and is **not** contained in the `.tsk`.
   Whether it knows further commands can only be clarified by reading out the
   flash chip.
9. **`t`/`n` (log)**: only sets flag `35h`. Output: `S: ` / `E: ` + 9 telegram
   bytes (`XX `), or `T: DIAL  ` / `T: LOCAL ` + index, variant, AB flag +
   `- ` + phone number. The same commands work in log mode.
   The flag lives in RAM and survives a restart of the host: if the PC or
   container goes away while logging, the gateway keeps logging until `n` or a
   power cycle. Answers are then interleaved with log lines (e.g. `i` →
   `…Version 01.26 S: 90 …` CR LF, `PIC Release 0101` on the next line), which
   looks as if no bus driver were installed. tks-gateway therefore sends `n` and
   discards pending output after opening the port, and skips log lines in
   answers.
10. **Configuration bytes without function**: in the configuration area the
    firmware only evaluates the known fields (`0x01`, `0x02`, `0x06`, `0x0A`,
    `0x0E`, `0x0F`, `0x10`, `0x15`, `0x40`, `0x41`; directly via DPTR and
    indirectly via page `0xA0`). Byte `0x00` and `0x16–0x3F`/`0x5A–0xFF` are
    never read, so there are no hidden configuration switches.
11. **`p` erases the bus driver immediately**: before receiving data the
    firmware (0x0EA1) runs the PIC16 "disable code protection" procedure
    (load configuration, increment address 7 times, commands `01`/`07`/`08`,
    delay, `01`/`07`). This erases the PIC completely. If the transfer aborts
    afterwards, the bus only works again after a successful new upload.
    Likewise `s` erases the gateway firmware. **Never send `p`/`P`/`s`/`S`
    without a file.**

**Cross-check on the device (firmware 01.26, PIC 0101, no bus):** all
characters `0`–`~` + CR except `s S p P d D u U z Z` were sent. Only `i` and
`I` got an answer (upper case is converted). With log enabled (`T`) this shows
`S: 90 00 00 00 00 00 00 00 00`, the bus telegram of the PIC query.

**Conclusion:** apart from the eight commands there are no hidden commands on
the TTL interface. In particular it cannot be used to enter DTMF codes, read or
write memory, or send arbitrary bus telegrams. Sending exists only indirectly
(`i` → `0x90`, `z` → `0x05`). Only the boot code remains open.

Only the **bootloader** (not contained in the `.tsk`) understands single
characters without `CR`:

| Character | Function |
|---|---|
| `s` | transfer firmware (the software uses this when the version contains "Bootlader") |
| `r` | bootloader reset/restart (`BootladerResettenSenden`, only reachable via a hidden operation, see below) |

`z T NN` corresponds to the DTMF code `*2*door station*index#`. The firmware
checks `NN` for 1–50 but does not check the door station `T` at all. It is only
stored locally in the entry (offset +8) and not sent on the bus.

Observed on the device (log enabled): `z105` → `S: 05 04 00 …`,
`z920` → `S: 05 13 00 …`. So the gateway sends telegram `05` with the
**phonebook index − 1** (0-based). Then it waits 2–3 s (`58h` = 3 ticks of
1 s). Without an answer there is **no** serial message and the image stays
unchanged (compared before/after the tests).

#### Passive learning via the serial interface? (checked)

* **No dedicated command.** The learning state (`04D2`, only set in `0x14BB`)
  is entered from exactly two places: `0x0882` (DTMF `*2`/`*7`) and `0x0F47`
  (serial `z`). The passive branch without telegram (`*7`, 15 s) is only
  reachable from the DTMF menu (`0x0703`), which is fed exclusively by the
  DTMF receiver. The `z` path always sends telegram `05` (flag `30h`) and
  always learns for 3 ticks.
* **But `z` does not only learn the answer to `05`.** The learning condition
  (`0x0C93`–`0x0CA2`) only checks telegram code `0x11` (door call) and state
  `04D2`, not the sender. Any door call within the window is accepted, even a
  normal ring without programming mode. Another `z` restarts the window
  (`0x14BB` resets state and counter) but sends `05` again each time.
* **Purely passive, without a bus telegram**, it only works as a combination:
  enable the log (`t`), capture the door call `E: 11 …`, enter the address into
  the image and write it with `d`. This is how method B ("by capture") of the
  web UI works.

Version text: if it contains "Bootlader", no firmware is installed; if "PIC"
is missing, no bus driver is installed.

The call-button response contains 5 bytes as hex pairs at positions 1, 4, 7,
10, 13; the software appends `00-00-00` to form the 8-byte button code.

## XMODEM

Standard XMODEM with checksum:

* Block: `SOH(0x01)`, block number `n` (from 1, mod 256), `255-n`, 128 data
  bytes (last block padded with `0x1A`), sum of the data bytes mod 256
  (`BlockSenden`, `csum`)
* Acknowledgements: `ACK 0x06`, `NAK 0x15`; end `EOT 0x04`; abort 3 × `CAN 0x18`
* PC sends: waits for the gateway's `NAK`, then blocks, after the last one `EOT`, waits for `ACK`.
* PC receives: sends `NAK` every second ("Warte auf Daten. Noch n Sekunden"),
  checks each 132-byte packet, `ACK`/`NAK`; aborts with `CAN` after 3 errors.
  After block 48 `EOT` is expected and acknowledged with `ACK`.
* Overall timeout in the original: 60 s.

## Memory image (6144 bytes)

Offsets 0-based. Text: ASCII padded with 0x00; reading stops at 0x00/0xFF
(phone numbers, times and PIN additionally at `A`).

### Configuration 0x000–0x0FF

| Offset | Length | Content |
|---|---|---|
| 0x00 | 1 | unknown (preserved) |
| 0x01 | 1 | connection type: 0 = direct line (Amt), otherwise extension |
| 0x02 | 4 | local ring time (seconds, ASCII, max. 120) |
| 0x06 | 4 | external ring time |
| 0x0A | 4 | door talk time |
| 0x0E | 1 | variant: 0 = 1 (day), otherwise 2 (night) |
| 0x0F | 1 | listen-in (Mithören): 0 = off, otherwise on |
| 0x10 | 5 | PIN (4 digits + 0x00) |
| 0x15 | 1 | master redirect: 0 off, 1 delayed, 2 immediate |
| 0x16 | 42 | unknown (preserved) |
| 0x40 | 1 | answering machine flag of the master redirect: `A` on, ` ` off |
| 0x41 | 25 | master redirect number |
| 0x5A | 166 | unknown (preserved) |

Factory settings: extension, ring times 030/030, door talk time 060,
variant 1, listen-in off, PIN 0000, master redirect off.

Additions from the device manual (12901310) and the software manual (12911310):

* All three times: max. 120 s.
* Phone numbers (phonebook and master redirect): **max. 24 characters**,
  although the field has 25 bytes. Allowed are digits, `*`, `#` and the special
  characters `P` (dial pause ~1 s), `F` (flash 100 ms + pause) and `f` (flash
  80 ms + pause). The special characters can only be entered via the software,
  not by telephone. An empty number means: door call goes to the telephone on TLN.
* **Listen-in (0x0F)** is explained neither in the device manual nor in the
  software manual. Gira's product description lists a "Mithörsperre"
  (listen-in lock) as a feature ("Ruf und Gesprächsdauer einstellbar.
  Mithörsperre."). The switch is probably meant for that (off = lock active =
  factory setting). Further evidence: in the original software only these two
  options have no help text in the status bar. Otherwise the value is only
  read, displayed and saved (0x4297D0, 0x42E3D0, 0x421F00, 0x430C20) and tied
  to nothing. Firmware 1.26 only writes the byte (`*8`, 0x0709) and never reads
  it, neither directly nor indirectly via page 0xA0. The setting therefore has
  no effect.
* **Unknown call buttons are ignored**, even with master redirect active: a
  door call whose address is not in the phonebook ends after the search
  (0x0CE8 → 0x0DA0 → `JZ 0x0D21`) without a call. Call buttons must therefore
  always be learned.
* **Answering incoming calls** (extension mode, observed on a Grandstream
  HT801 with ring cadence 2 s on / 4 s off): the gateway picks up after 12.4 s
  or 18.4 s, i.e. on the 3rd or 4th ring. Then the command tone follows: two
  short tones (~425 Hz), repeated about every 5.5 s. This matches the symbol in
  the manual (p. 15). There is **no configuration parameter** for the number
  of rings; it is fixed in the firmware. The PBX must therefore not cancel the
  call before about 20 s.
* **Command mode time limit 60 s** (firmware): after picking up, `0x13EB`
  starts the command tone and sets `58h = 3Ch` (60 ticks of 1 s). Every DTMF
  key restarts the timer (`0x0596`). Only after 60 s without input does the
  gateway hang up (`0x056E` → `21h = 41h` → idle state `0x13C5`). No detection
  of "caller hung up" was found in this state (not checked exhaustively).
  Consequence: calling again within this time gives a **busy** signal.
* The gateway only dials out when a door call from a **learned** call button
  arrives on the bus. Without a bus it never dials. There is also no telephone
  or serial command that triggers a call.
* Assigning call buttons (original): programming mode by holding
  "Systemprogr." on the control unit for 3 s, press the call buttons in the
  order of the entries for 3 s each until the short acknowledgement tone, then
  "Assign call button" for each entry, finally press "Systemprogr." briefly.
  **Holding a call button for another 3 s after the acknowledgement tone
  deletes all assignments of the door station.**

### Phonebook 0x100 + 64·i (i = 0…49)

| Offset | Length | Content |
|---|---|---|
| +0 | 8 | button code (bus address of the call button; ≠ 0 → "assigned") |
| +8 | 1 | door station as ASCII `1`…`9` (`0` = none in empty entries) |
| +9 | 1 | 0x00 |
| +10 | 1 | answering machine variant 1: `A` / ` ` |
| +11 | 25 | phone number variant 1 |
| +36 | 1 | answering machine variant 2: `A` / ` ` |
| +37 | 25 | phone number variant 2 |
| +62 | 2 | 0x00 |

0x0D80–0x0FFF: 0x00.
Names: 0x1000 + 20·i, 20 bytes each. Then 0x00 up to 0x17FF.

When saving, the software first reads the current image and replaces only the
edited area (configuration or phonebook).

A delayed master redirect is not allowed if the answering machine function is
active in any entry.

## Bus log

Text lines with `CR LF`. Position 1 (1-based): `S` gateway sends, `E` gateway
receives, `T` gateway calls. Pos. 4–5 telegram code, pos. 7–14 bus address,
pos. 16–17 data byte/sub-address.

| Type | Code | Meaning |
|---|---|---|
| S | 12 / 21 / 22 / 20 / 31 | internal call on / door call start / internal call start / call end / open door |
| S | 42 | switching function ON (data `FF`) / OFF |
| S | 81 / 82 | test device mode ON / OFF |
| S | A0 / A1 | audio input TLN / transmitter to bus ON/OFF (pos. 7–8 `FF` = ON) |
| S | A2 / A3 | system reset / call known in phonebook |
| S | 90 | bus driver version request (sent by `i`) |
| S | 05 | request call button for entry n (sent by `z`/`*2`, data = index − 1) |
| E | 20 / 11 / 12 / 21 / 22 | call end / door call / internal call / door call accepted / internal call accepted |
| E | 01 / 00 / 03 / 02 | system programming ON/OFF, actuator programming ON/OFF |
| T | – | pos. 10–11 phonebook index (hex, `00` = master redirect), pos. 13–14 variant, `LOCAL`/`DIAL '<nr>'`, AB flag at the end |

The field positions of the `T` lines are only partly confirmed.

**Relation to the bus frame (GDoor).** The independent
[GDoor documentation](https://gdoor-org.github.io/documentation/protocol.html) describes the TKS bus frame as
`length/flags · status · action · source (3) · parameter (2) · device type ·
[destination (3)] · checksum`. The gateway's `S:`/`E:` lines start with the
**action** byte, i.e. the bus driver strips the header and checksum. This
refines the fields above:

* log pos. 7–14 (the three bytes after the code) = **source address** of the
  sending device, pos. 16–17 and the next byte = **parameter** (e.g. button
  number) – this matches the "bus address" and "data byte" positions above;
* the stored **button code** of a phonebook entry is source address +
  parameter: the real backup contains `CC-ED-19-83-00` = door station `CC ED 19`,
  button byte `83` (the gateway pads it to 8 bytes with `00`).

| Code | GDoor name | Meaning (this document) |
|---|---|---|
| `00` / `01` | CTRL_PROGRAMMING_STOP / START | system programming OFF / ON |
| `02` / `03` | CTRL_DOOROPENER_TRAINING_STOP / START | actuator programming OFF / ON |
| `05` | CTRL_DOORSTATION_ACK – confirm learned doorbell button | sent by `z` / `*2` (request call button for entry n) |
| `11` | BUTTON_RING | door call |
| `12` | CALL_INTERNAL | internal call |
| `20` | AUDIO_VIDEO_END | call end |
| `21` | AUDIO_REQUEST | door call start / accepted – after it the door station puts analogue audio on the bus |
| `31` | DOOR_OPEN | open door |
| `42` | BUTTON (generic button / switching function) | switching function ON / OFF |

The physical layer (60 kHz carrier bursts, bit lengths, parity) and how the
bus driver implements it are described in
[HARDWARE.md](HARDWARE.md#tks-bus-physical-layer).

The firmware has only four log output sites (`S:`, `E:`, `T: DIAL`,
`T: LOCAL`). Incoming calls, the command mode and DTMF input are **not**
logged; without a bus the log stays empty apart from `S: 90` after `i`.

## Hidden and undocumented functions

### Commissioning software

* **Bootloader reset:** on the *Firmware* tab focus the "Auslesen" button
  (Tab) and press `r` (KeyPress handler 0x416070). The software waits 2.5 s,
  sends `r` without CR, waits 1 s and reads the version again. This works once
  per session; it is enabled again when a normal firmware is detected. With
  running firmware the `r` only ends up in its line buffer and corrupts the
  next command.
* **`Debug_Fenster`:** form with two lists, but never opened (dead code).
  The module `Versionshistory` contains no code.
* Otherwise no hidden key combinations, passwords or switches. The form events
  are only Load/Unload/Resize, MouseMove (help texts in the status bar) and the
  context menu in the phonebook.

### Firmware (DTMF programming by telephone)

DTMF menu after `R * 0 * PIN #` (dispatcher at 0x06CF; EEPROM mirror from
0xA000 = image offset):

| Code | Manual | Effect (offset) |
|---|---|---|
| `*1*…` | yes | phonebook |
| `*2*T*NN#` | yes | assign call button: sends bus telegram `05`, waits 3 s for a door call |
| `*3*K#` | yes | connection type (0x01, K = 0/1) |
| `*4*/*5*/*6*ZZZ#` | yes | ring times / door talk time (0x02 / 0x06 / 0x0A) |
| **`*7*T*NN#`** | **no** | assign call button **without** prior telegram, waits **15 s** for a door call |
| **`*8*K#`** | **no** | **listen-in** (0x0F): K = 0 off, 1 on |
| `*9*PIN*PIN#` | yes | change PIN (0x10) |

**Call-button learning sequence** (`*2`, `*7` and serial `z T NN`, shared code
from 0x0C8B): the firmware enters a learning state (handler 0x04D2) with a
countdown in `58h` (1 tick = 1 s; timer 0 every 5 ms × 200, crystal
14.7456 MHz). If a bus telegram with code `0x11` (door call) arrives in this
time, its 5 address bytes are written as button code to entry `NN`, door
station `T` to offset +8, and the EEPROM is saved. Then the positive
acknowledgement tone follows and, for `z`, the hex line to the PC. If the time
runs out, the negative acknowledgement tone sounds. `*2` and `z` send bus
telegram `05` first (requests the call button for entry `NN`; according to the
manual programming mode on the control unit is required). `*7` only listens
passively for 15 s. Outside the learning state a door call leads to a
phonebook search (0x0DA0) and, on a match, to a call.

Level without PIN (`R * x …`): `0` (PIN entry), `1`, `2`, `3`, `9` as in the
manual, with one extension:

* **`R * 1 * number * 1 #`** additionally sets the answering machine flag of
  the master redirect (offset 0x40 = `A`); `R * 1 * number #` resets it (` `).
  The manual only mentions the second form.

The factory reset `R * 9 * 1928374655 #` is documented. The digit sequence is
stored as a table at 0x08E5 in the firmware. Routine 0x0986 sets the **entire**
image `0xA000–0xB7FF` to 0x00 (configuration, all 50 phonebook entries, all
names) and then copies 22 bytes of default configuration back from 0x4DA8:
`00 01 "030" 00 "030" 00 "060" 00 00 00 "0000" 00 00`. This matches exactly the
software's factory settings (extension, 030/030/060, variant 1, listen-in off,
PIN 0000, master redirect off). Then it saves to the EEPROM.

The **"Werkseinstellungen" (factory settings) button of the software**, in
contrast, only resets the configuration (`KonfigurationWerkseinstellungen`,
0x430C20). The phonebook is cleared separately there with "Telefonbuch
löschen" (clear phonebook).

## File formats of the original software

* `.gtk` – configuration as plain-text report ("Gira TK-Gatewaykonfiguration",
  values or `X`). Labels are German and are kept that way for compatibility.
* `.gtb` – phonebook grid, cells separated by tab, rows by CR; columns: index,
  subscriber, no. V1, no. V2, answering machine (0–3), door station,
  free/assigned (frei/gefangen), button code
* `.tsk` – firmware (8051 code), `.hex` – bus driver (PIC, Intel HEX); both are
  transferred unchanged
