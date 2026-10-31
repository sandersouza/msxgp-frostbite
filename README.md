# Frostbite for MSX1

A native MSX1 port of Activision's Atari 2600 Frostbite, with the supplied
original ROM as the authority for gameplay mechanics.

## Current state

The design is approved and repository preparation is underway.
There is **no Frostbite MSX ROM to play or test yet**.

The supplied 4 KiB Atari ROM has a verified immutable identity and measured
262-line / 19,912-CPU-cycle steady cadence. Initial automatic disassembly rebuilt
byte-identically. Commercial revision/provenance and full-state replay
repeatability remain unverified; semantic disassembly, the MSX scaffold and
gameplay are still planned work. Historical Seaquest results are not Frostbite evidence.

- [Approved design](docs/superpowers/specs/2026-10-31-frostbite-design.md)
- [Issue roadmap](docs/superpowers/specs/2026-10-31-frostbite-backlog.md)
- [GitHub project — MSX Game Ports #7](https://github.com/users/sandersouza/projects/7)
- [Development status](docs/development.md)
- [Original reference inventory and timing](docs/reference-inventory.md)
- [Delivery workflow](docs/project-workflow.md)
- [Preserved baseline and provenance](docs/baseline-preservation.md)

## Target and fidelity

Standard-speed **MSX1, 64 KiB RAM and 16 KiB VRAM**, TMS9918-family VDP and
built-in PSG. No RAM expansion, turbo, disk drive or extra sound hardware.
Cartridge size/mapper will be selected from measured implementation needs.

The port aims to preserve original mechanics exactly: source-coordinate
movement, arithmetic/flags, update ordering, collisions, game modes and timing.
The proposed implementation translates gameplay to native Z80 and compares
state against independent execution of the original. Graphics and sound are
adapted to MSX hardware, with differences documented explicitly.

## Development and testing

The owner-provided Seaquest copy is preserved locally and quarantined under
ignored `.legacy/seaquest/`. Reuse requires a file-by-file audit. Its Makefile,
scripts, tests, screenshots and success reports are not an active Frostbite
build or test suite.

[Issue #5](https://github.com/sandersouza/msxgp-frostbite/issues/5) will provide
the macOS setup script, pinned tools, cross-build commands and diagnostic ROM.
[Issue #6](https://github.com/sandersouza/msxgp-frostbite/issues/6) will provide
original-free CI. Until those deliverables exist, no inherited command is
advertised as a working Frostbite development entry point.

Every new testable MSX ROM version will have a versioned GitHub release
(prerelease during development), with the exact ROM attached, its hash/source
commit, current state and limitations, next steps and concrete human tests.
The release will explain setup, controls, expected results and feedback needed.
Automated checks, manual emulator review and physical hardware evidence remain
separate.

Original Atari ROMs and complete original-derived disassemblies/assets stay
local. They are not downloaded by public CI or included in this source tree.

## License and provenance

The supplied [GPLv3 license text](LICENSE) is preserved unchanged.
This does not include or change ownership of the original Atari/Activision
material. Retained infrastructure from the Seaquest project will carry its
provenance and applicable notices.
