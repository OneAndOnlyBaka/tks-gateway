# tks-gateway

Python re-implementation of the **Gira TK gateway 1290 00 commissioning software**
(original V1.01, Windows/VB6) with a web UI (Flask) and a command line.

Same functions as the original: load/save configuration and phonebook, assign
call buttons, capture the bus communication, update firmware and bus driver,
factory settings, import/export (.gtk, .gtb, plus .json and raw image .bin).
On top of that: a call-button learning wizard, a PBX connection wizard, PBX
connection tests, tooltips for every parameter and a reference of all DTMF
codes including the undocumented ones.

## Documentation

| Document | Content |
|---|---|
| [User guide](docs/USER_GUIDE.md) | system overview, [RJ10 pinout](docs/USER_GUIDE.md#2-programming-plug-rj10--pinout), first setup, [door call sequence](docs/USER_GUIDE.md#4-what-happens-on-a-door-call), [opening the door via SIP](docs/USER_GUIDE.md#5-open-the-door-without-a-door-call-sip), [command mode and busy tone](docs/USER_GUIDE.md#6-command-mode-and-busy-tone), [learning call buttons](docs/USER_GUIDE.md#7-learning-call-buttons), [working copy and saving](docs/USER_GUIDE.md#8-working-copy-and-saving), [log](docs/USER_GUIDE.md#9-reading-the-log), [phone codes](docs/USER_GUIDE.md#10-phone-codes-dtmf), [troubleshooting](docs/USER_GUIDE.md#11-troubleshooting) – background on the system, with diagrams |
| [UI reference](docs/UI.md) | every tab, dialog, wizard and button of the web UI and what it does on the gateway |
| [Software architecture](docs/ARCHITECTURE.md) | modules, data flow, concurrency and serial access, [HTTP API](docs/ARCHITECTURE.md#http-api), frontend, [internationalisation](docs/ARCHITECTURE.md#internationalisation), [licenses and SBOM](docs/ARCHITECTURE.md#licenses-and-sbom), simulator, deployment, tests |
| [Hardware overview](docs/HARDWARE.md) | block diagram of the gateway reconstructed from firmware and manuals: 8051 controller, banked flash, SRAM, I/O latches, port pins, PIC16F628 bus driver, tone generation, telephone section, open points |
| [Protocol and firmware findings](docs/PROTOCOL.md) | serial interface, commands, XMODEM, memory image, bus log, [hidden and undocumented functions](docs/PROTOCOL.md#hidden-and-undocumented-functions) ([German version](docs/PROTOKOLL.md)) |
| [Disclaimer](DISCLAIMER.md) · [License](LICENSE) | reverse engineering, trademarks, no warranty · MIT |
| [.env.example](.env.example) · [compose.yaml](compose.yaml) · [Dockerfile](Dockerfile) | container configuration |

The Gira manuals (12901310 device, 12911310 software) are not part of this
repository; they are available from Gira.

## Installation

```sh
pip install -e .          # installs pyserial and flask
```

## Connecting the gateway (RJ10 pinout)

The programming socket of the gateway is an RJ10 (4P4C) jack with **TTL level (5 V)**, 19200 baud 8N1.
The original cable 1291 00 contains a MAX232; a USB-TTL adapter can be connected directly instead.

| Pin | Signal | Direction | USB-TTL adapter |
|---|---|---|---|
| 1 | GND | – | GND |
| 2 | +5 V | gateway → cable (powers the original converter) | **do not connect** |
| 3 | TxD of the gateway | gateway → PC | RXD |
| 4 | RxD of the gateway | PC → gateway | TXD |

- Use the **TTL** output set to **5 V** I/O, never RS232/RS485 (±12 V can destroy the controller).
- The counting direction of the contacts is not documented – measure first: with the gateway powered,
  the two contacts with ~5 V between them are GND (1) and +5 V (2); the gateway's TX (3) also idles at
  ~5 V against GND; the remaining contact is pin 4.
- No answer to "Test connection": swap TX and RX.

Source: KNX-User-Forum thread 8264 (2020), confirmed by several users, not by Gira. Details:
[user guide](docs/USER_GUIDE.md#2-programming-plug-rj10--pinout) and
[PROTOCOL.md](docs/PROTOCOL.md#pinout-of-the-programming-plug-rj10-4p4c-gateway-side); the web UI
shows the wiring in the **Help** tab.

## Web UI

```sh
tks-gateway --port /dev/ttyUSB0 web       # Linux
tks-gateway --port COM1 web               # Windows
tks-gateway --sim web                     # no hardware, simulated gateway
```

Then open <http://127.0.0.1:5000/>. The serial port can also be selected in the
UI. With `--host 0.0.0.0` the page is reachable on the network. It has no login,
so only use that in a trusted network. All tabs, dialogs and wizards are
described in the [UI reference](docs/UI.md).

### Help

The **Help** tab is a guide to operating the tool: quick start, connecting the adapter, how the
working copy and saving work, backup and restore, settings, phonebook, the ways to learn call buttons,
the PBX wizard and tests, logging, firmware update and troubleshooting – with a few diagrams (Mermaid,
bundled in `static/vendor/`, MIT, see `mermaid.LICENSE`, so the help also works offline). Background on
the system itself (door calls, SIP door opening, command mode) is in the [user guide](docs/USER_GUIDE.md).

### Licenses and SBOM

The **Licenses** tab lists all third-party components with version, license and license text. The list is
determined at runtime from the installed Python packages (dependencies of tks-gateway, plus waitress if
installed) and from the bundled JavaScript in `static/vendor/` (described by its original npm
`package.json`), so it always matches the running installation. The button there downloads a
**CycloneDX 1.5 SBOM** (JSON) generated on request; the same is available at `/api/sbom` and on the
command line:

```sh
tks-gateway sbom -o tks-gateway.cdx.json   # SBOM of this installation
tks-gateway licenses                    # short list of components and licenses
```

How the components are determined: [architecture](docs/ARCHITECTURE.md#licenses-and-sbom).

### Language

The UI is in **English** by default and can be switched to **German** with the
`EN | DE` switch in the header (stored in the `lang` cookie). The default for
new visitors and for the command line is set with `TKS_GATEWAY_LANG=de` or
`tks-gateway --lang de …`.

### Learning call buttons (wizard)

Phonebook → "Learn call buttons …". The wizard captures the bus, detects every
pressed call button (door call `E: 11`) and assigns it to phonebook entries.
The gateway sends nothing on the bus; neither programming mode nor a telephone
is needed. Steps: check the connection and load the current state (with
backup) → press the buttons one after another and assign them → review → save
once. Requirement: the gateway is connected to the TKS bus. All ways to learn
call buttons are compared in the [user guide](docs/USER_GUIDE.md#7-learning-call-buttons).

## Container (Podman/Docker Compose)

```sh
cp .env.example .env              # optional: adjust adapter/port
podman compose up -d --build --force-recreate   # or: docker compose up -d --build --force-recreate
```

Then open <http://127.0.0.1:5000/>. Always use `--force-recreate` after code
changes, otherwise Podman keeps the old container running. The USB serial
adapter is passed into the container via its stable path
`/dev/serial/by-id/…` as `/dev/ttyUSB0` (default: FTDI FT232R in the Waveshare
converter; other adapters via `SERIAL_DEVICE` in `.env`).

- **Rootless Podman** (e.g. Fedora): the user must be in the `dialout` group.
  `group_add: keep-groups` passes this group into the container.
  `security_opt: label=disable` is needed with SELinux, otherwise opening the
  device is denied. Alternatively set `sudo setsebool -P container_use_devices on`
  system-wide and remove that line.
- **Docker:** set `SERIAL_GROUP` to the numeric GID of `dialout` (`getent group dialout`).
- If the adapter is unplugged and replugged while the container runs, restart
  the container (`podman compose restart`).
- With `BIND_ADDRESS=0.0.0.0` the UI is reachable on the network. It has no login.
- `TKS_GATEWAY_LANG=de` in the environment makes German the default language.

Deployment details: [architecture](docs/ARCHITECTURE.md#deployment).

## Command line

```sh
tks-gateway ports                                   # list serial ports
tks-gateway -p /dev/ttyUSB0 version                 # firmware version
tks-gateway -p /dev/ttyUSB0 read -o backup.json     # back up everything
tks-gateway -p /dev/ttyUSB0 write backup.json       # write everything back
tks-gateway -p /dev/ttyUSB0 set --pin 4711 --external-ring-time 45
tks-gateway -p /dev/ttyUSB0 entry 1 --name "Ground floor" --v1 0221555 --door-station 1 --learn
tks-gateway -p /dev/ttyUSB0 log -o bus.log
tks-gateway -p /dev/ttyUSB0 firmware tkg_126.tsk
tks-gateway -p /dev/ttyUSB0 firmware tkg_101.hex --bus-driver
tks-gateway -p /dev/ttyUSB0 call-button 1 5         # door station 1 → entry 5
tks-gateway -p /dev/ttyUSB0 bootloader-reset        # hidden function of the original
tks-gateway sbom -o tks-gateway.cdx.json               # SBOM of this installation
tks-gateway licenses                                # third-party components and licenses
tks-gateway --lang de …                             # German messages
```

The German command and option names of earlier versions still work as aliases
(`eintrag`, `ruftaste`, `werkseinstellungen`, `--externe-rufzeit`,
`--tuerstation`, `--einlernen`, `--bustreiber`, `an`/`aus`, …).

Hidden and undocumented functions (software and firmware) are described in
[docs/PROTOCOL.md](docs/PROTOCOL.md#hidden-and-undocumented-functions).

Press the call button at the door station right before `--learn` or
"Assign call button".

## Tests

```sh
pip install -e .[test] && pytest
```

The tests run against a gateway simulator (`tks_gateway.simulator`). The
browser tests (`tests/test_e2e_wizard.py`) need Playwright and Chromium and are
skipped otherwise. Overview: [architecture](docs/ARCHITECTURE.md#tests).

## Status

Tested on a real gateway (firmware 01.26, PIC 0101) for reading only: version,
reading the image (byte-exact round trip), bus log and the `z` command. Writing
to a real device has not been tested yet. Confirmed from the program code:
interface parameters, commands, XMODEM sequence and memory layout. Less
certain: the field positions of the `T` log lines and the exact compatibility
of .gtk/.gtb files with original files. Make a backup before the first write
(`read -o backup.bin`).

## Disclaimer and license

Unofficial project, not affiliated with or endorsed by Gira. The protocol and
device behaviour were reverse engineered from the original software and
firmware for interoperability; no Gira code, firmware or documents are
included. Use at your own risk; see [DISCLAIMER.md](DISCLAIMER.md).

Copyright (c) 2026 OneAndOnlyBaka. Licensed under the [MIT License](LICENSE).
Third-party components and their licenses are listed in the web UI (tab
"Licenses") and with `tks-gateway licenses`; `tks-gateway sbom` writes a
CycloneDX SBOM. Bugs and questions:
[GitHub issues](https://github.com/OneAndOnlyBaka/tks-gateway/issues).
