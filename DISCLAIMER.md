# Disclaimer

**tks-gateway is an independent, unofficial project. It is not affiliated with,
endorsed by or supported by Gira Giersiepen GmbH & Co. KG.** "Gira" and product
names such as "TK-Gateway" are trademarks of their respective owners and are
used here only to describe compatibility.

## Reverse engineering and interoperability

The serial protocol, the memory layout and the device behaviour documented in
this repository were reconstructed by reverse engineering, using:

* disassembly of the original Windows commissioning software V1.01
  (`TK_Gateway.exe`, VB6 native code, 2005),
* disassembly of the gateway firmware 1.26 (8051) and the bus driver
  firmware (PIC16),
* observation of a real gateway on its serial interface,
* the publicly available Gira manuals 12901310 and 12911310 and public forum
  posts (sources are cited in [docs/PROTOCOL.md](docs/PROTOCOL.md)),
* for the TKS bus side, the independent public reverse engineering of the
  [GDoor project](https://gdoor-org.github.io/documentation/protocol.html)
  (documentation only; no GDoor code is included).

The analysis was carried out by the lawful owner of the device, on copies of
the software and firmware that Gira offers as a free public download, and with
a single purpose:
interoperability, i.e. operating and configuring the gateway from current
operating systems. The original commissioning software dates from 2005 and is
no longer practical to run; the protocol is not documented publicly by the
manufacturer. The work is intended to stay within the limits that copyright
law sets for decompilation to achieve interoperability (Art. 6 of Directive
2009/24/EC, § 69e UrhG in Germany). The findings are used only to talk to the
existing device, not to replace or reproduce the manufacturer's firmware or
software.

## What this repository does and does not contain

This repository contains **no code, firmware, software or documents from
Gira**. All program code and documentation were written independently; the
protocol description is the author's own wording. Firmware files (`.tsk`,
`.hex`), the original software and the manuals are not redistributed here; they
can be downloaded free of charge from Gira's
[download page](https://partner.gira.de/service/download/index.html?id=2386).

## No warranty, use at your own risk

The findings are based on analysis and may be incomplete or wrong. Writing the
configuration, and in particular transferring firmware or bus driver firmware,
can leave the gateway in an unusable state: the `s` and `p` commands erase the
firmware or bus driver immediately. **Always make a backup before writing.**
The software is provided "as is", without warranty of any kind; see
[LICENSE](LICENSE).

The web UI has no authentication. Do not expose it to untrusted networks.

## Rights holders

If you are a rights holder and believe that something in this repository
infringes your rights, please open an issue or contact the author before
taking other steps. Concerns will be reviewed promptly, and content will be
corrected or removed where justified.
