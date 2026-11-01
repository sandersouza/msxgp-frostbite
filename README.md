# Frostbite for MSX1

A native MSX1 port of Activision's Atari 2600 Frostbite, with the supplied
original ROM as the authority for gameplay mechanics.

## Current state

The first [MSX1 diagnostic prerelease](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.1-diagnostic)
provides a 16 KiB cartridge for video, interrupts, controls and built-in PSG tests.
**Frostbite gameplay is not implemented yet.**

The [v0.0.2 renderer benchmark](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.2-renderer)
adds a synthetic SCREEN2 workload in a plain32KiB cartridge. Its
[measured limits and commands](docs/renderer-feasibility.md) and
[human tests](docs/releases/v0.0.2-renderer.md) explain the current state.
[Original graphics extraction and SCREEN2 asset-fit evidence](docs/original-graphics.md)
are prepared locally. They are not yet integrated into the cartridge; native
gameplay remains later work.

The supplied 4 KiB Atari ROM has a verified immutable identity and measured
262-line / 19,912-CPU-cycle steady cadence. Disassembly reconstructs
byte-identically and has a reviewed routine/state/hardware map. Commercial
revision/provenance remains unverified. Bounded complete-state replays now repeat
under declared initialization; natural complete-game coverage remains pending.
Source-addressed mechanics contracts and bounded CPU probes are available;
native gameplay remains planned work. Historical Seaquest
results are not Frostbite evidence.

- [Approved design](docs/superpowers/specs/2026-10-31-frostbite-design.md)
- [Issue roadmap](docs/superpowers/specs/2026-10-31-frostbite-backlog.md)
- [GitHub project — MSX Game Ports #7](https://github.com/users/sandersouza/projects/7)
- [Development status](docs/development.md)
- [macOS setup/build/smoke checklist](docs/toolchain.md)
- [Original reference inventory and timing](docs/reference-inventory.md)
- [Disassembly reconstruction and state map](docs/reference-disassembly.md)
- [Gameplay contracts and boundary routes](docs/gameplay-contracts.md)
- [Independent original-execution oracles](docs/reference-traces.md)
- [Renderer feasibility and synthetic benchmark](docs/renderer-feasibility.md)
- [Original graphics, coordinate/palette mapping and asset fit](docs/original-graphics.md)
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

[Issue #5](https://github.com/sandersouza/msxgp-frostbite/issues/5) provides
the macOS setup script, pinned tools, cross-build commands and diagnostic ROM.
[Issue #6](https://github.com/sandersouza/msxgp-frostbite/issues/6) provides
original-free CI. `make render-build` and `make render-bench` build/test the
synthetic renderer; the original diagnostic remains the default `make build`.

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
