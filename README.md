# Frostbite for MSX1

A native MSX1 port of Activision's Atari 2600 Frostbite, with the supplied
original ROM as the authority for gameplay mechanics.

## Current state

The first [MSX1 diagnostic prerelease](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.1-diagnostic)
provides a 16 KiB cartridge for video, interrupts, controls and built-in PSG tests.

The [v0.0.2 renderer benchmark](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.2-renderer)
adds a synthetic SCREEN2 workload in a plain32KiB cartridge. Its
[measured limits and commands](docs/renderer-feasibility.md) and
[human tests](docs/releases/v0.0.2-renderer.md) explain the current state.
[Original graphics extraction and SCREEN2 asset-fit evidence](docs/original-graphics.md)
are prepared locally. They are not yet integrated into the cartridge.

The [downloadable v0.0.3-movement diagnostic](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.3-movement)
([technical contract](docs/native-movement.md)) executes the original
post-visible phase as Z80, samples real MSX controls at source boundaries and
measures the complete input/mapper/render pipeline on NTSC/PAL. It uses a 256 KiB
ASCII16 cartridge with 64 KiB RAM/16KiB VRAM. **Contacts and graphics are diagnostic;
natural collisions, original presentation/audio and a complete game remain
pending.** Exact artifact identity and human tests accompany its versioned release.

The [v0.0.4-buildloop diagnostic](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.4-buildloop)
adds original-clock floe contacts and the native build-and-enter loop. Its
4 MiB ASCII16 cartridge still needs only 64 KiB RAM/16 KiB VRAM. Automated
NTSC/PAL replay completes construction, entry and the next-level transition.
Presentation remains synthetic and silent; full hazard/shore acquisition and
complete-game acceptance remain pending. See the [technical evidence](docs/floe-loop.md)
and [human test instructions](docs/releases/v0.0.4-buildloop.md). The tightest
measured PAL stress margin is 232 cycles; physical testing remains pending.

The [v0.0.5-hazards diagnostic](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.5-hazards)
adds actual threat/fish/bear/shore contacts and
original interaction ordering in the same 4 MiB ASCII16 hardware target.
Its sealed automated evidence covers 14,828 visible phases, 652 controlled
native cases, 65,536 Z80 shift/flag cases, all 32 natural route/clock/view
combinations and 15 crowded stress modes. The tightest measured PAL margin is
645 cycles. [Technical evidence](docs/hazard-collisions.md),
[compact validation](references/hazard-result.json) and
[release notes/human tests](docs/releases/v0.0.5-hazards.md) describe the exact
ROM and its synthetic, silent presentation. Independent review, merged-main
rebuild/CI and all four published asset downloads passed;
[delivery receipt](references/hazard-delivery.json). Whole-game, progression and
manual/physical acceptance remain separate.

The sealed `v0.0.6-progression` candidate adds all four original variations, score/reserve
boundaries, alternating records, progression, exhaustion and restart proof.
All 96 new/retained route/clock/view combinations pass (198,560 complete state
checkpoints and 182,308 pixel frames), plus controlled boundaries and dense
stress. The tightest PAL margin is 283 cycles. Its exact 4 MiB ASCII16 ROM
retains the same unexpanded MSX1 target. See [technical evidence](docs/scoring-progression.md),
[reproduction](docs/progression-checklist.md) and
[human test instructions](docs/releases/v0.0.6-progression.md).
[Compact validation](references/progression-result.json) records the complete raw
state/pixel/cycle audit. Independent review and its guard-error fix pass are
complete; integration and release delivery remain pending.
HUD/art remain synthetic and audio is absent; presentation belongs to #14.

The supplied 4 KiB Atari ROM has a verified immutable identity and measured
262-line / 19,912-CPU-cycle steady cadence. Disassembly reconstructs
byte-identically and has a reviewed routine/state/hardware map. Commercial
revision/provenance remains unverified. Bounded complete-state replays now repeat
under declared initialization; natural complete-game coverage remains pending.
Source-addressed mechanics contracts, independent CPU probes and native movement
are available at their declared boundaries. Historical Seaquest
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
- [Native movement, input, mapper, timing and reproduction](docs/native-movement.md)
- [Floe contacts, natural build loop and timing](docs/floe-loop.md)
- [Original hazard/fish/bear contacts, complete interaction routes and timing](docs/hazard-collisions.md)
- [Scoring, progression, player records, all modes and complete timing matrix](docs/scoring-progression.md)
- [Delivery workflow](docs/project-workflow.md)
- [Preserved baseline and provenance](docs/baseline-preservation.md)

## Target and fidelity

Standard-speed **MSX1, 64 KiB RAM and 16 KiB VRAM**, TMS9918-family VDP and
built-in PSG. No RAM expansion, turbo, disk drive or extra sound hardware.
The current build-loop diagnostic uses 4 MiB ASCII16, selected from measured
lossless original-clock contact tables; it requires no RAM or sound expansion.

The port aims to preserve original mechanics exactly: source-coordinate
movement, arithmetic/flags, update ordering, collisions, game modes and timing.
The implementation translates gameplay to native Z80 and compares
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
`make movement-build`, `make movement-check` and `make movement-run` build,
validate and launch the source-dependent native movement diagnostic. See its
dedicated checklist before canonical capture or packaging.

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
