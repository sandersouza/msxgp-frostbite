# Frostbite development status

## Current supported target

Standard-speed MSX1, 64 KiB RAM, 16 KiB VRAM, TMS9918-family VDP and built-in PSG.
No extra accessories. The owner approved the
[design](superpowers/specs/2026-10-31-frostbite-design.md) on 2026-10-31.

## What is available now

The published issue13 diagnostic and its accepted capture matrix are documented in
[scoring-progression.md](scoring-progression.md); use the
[dedicated reproduction checklist](progression-checklist.md) for source/native
checks. It has all-four-mode progression/terminal/restart evidence on the
standard MSX1 target. Complete raw sealing and independent review/fix checks pass;
integration, clean-main rebuild and four published release downloads pass. The
[compact validation](../references/progression-result.json) binds the exact ROM;
definitive HUD/art/audio and whole-game/manual/physical acceptance remain separate.
The older reference/toolchain milestones below retain their own evidence scope.

- A verified local Atari reference identity and measured NTSC steady cadence:
  262 scanlines / 19,912 CPU cycles per frame. See the
  [inventory/timing evidence](reference-inventory.md) for startup observations,
  revision/provenance limits and pending full-state replay repeatability.
- A verified [disassembly reconstruction and state map](reference-disassembly.md):
  byte-identical rebuild, reviewed routine/RAM/hardware boundaries and explicit
  open contracts for issues #4/#7.
- [Gameplay contracts and boundary routes](gameplay-contracts.md), supported by
  101 bounded CPU-slice probes. These do not establish TIA geometry, aligned
  full-game replay or native gameplay acceptance.
- The [issue roadmap](superpowers/specs/2026-10-31-frostbite-backlog.md),
  [workflow](project-workflow.md) and verified
  [baseline preservation](baseline-preservation.md).
- Locally preserved tools/environment from the supplied copy; their presence
  does not establish a fresh Frostbite installation.
- A [macOS toolchain and MSX1 diagnostic scaffold](toolchain.md), exercised from
  a fresh source clone on arm64. The 16 KiB plain-ROM diagnostic checks video,
  interrupts, controls and PSG; native Frostbite gameplay remains pending.

Reference utilities now run with Python's standard library:
`python3 -B scripts/reference_inventory.py` and
`python3 -B scripts/source_timing.py` (the latter requires Stella 7.0/Debugger).
`python3 -B scripts/reference_rebuild.py` reconstructs the original with local
DiStella/DASM and compares all bytes; generated source/binaries remain ignored.
`python3 -B -m unittest discover -s tests -v` runs original-free utility tests.
The optional CPU-slice backend is pinned in requirements-reference.txt;
`.venv/bin/python -B scripts/mechanics_probe.py` runs the canonical source cases.
Use `.venv/bin/python -B -m unittest discover -s tests -v` for the full suite
with py65 present; standard Python explicitly skips CPU-specific unit cases
when that optional backend is unavailable.

`make environment`, `make environment-check`, `make environment-dry-run`,
`make test`, `make build`, `make smoke`, `make run` and `make package` are the
current development entry points. See the command-by-command checklist in
[toolchain.md](toolchain.md). The copied Seaquest tree remains quarantined;
its historical results are not current acceptance.

## Upcoming developer entry points

[Issue #5](https://github.com/sandersouza/msxgp-frostbite/issues/5) supplies the
toolchain/diagnostic. macOS Intel, physical MSX and human listening results
remain pending; automatic checks here use an isolated NTSC C-BIOS MSX1 profile.

[Issue #6](https://github.com/sandersouza/msxgp-frostbite/issues/6) delivered
original-free CI and scoped tracking helpers; see [ci-and-tracking.md](ci-and-tracking.md).
Original-dependent native/pixel acquisition remains a local acceptance step.

## Human tests and releases

Each new testable ROM comes through a versioned GitHub release with the exact
ROM attached, hash/source commit, current state, next work and a specific human
test checklist. Development builds are prereleases. Load/mapper/controls and
expected results will be given in each release.

The first diagnostic is [v0.0.1-diagnostic](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.1-diagnostic),
with concrete human checks in its release notes. It has no Frostbite gameplay.
Automated checks, rendered preview, human listening and physical hardware
acceptance remain separate.
