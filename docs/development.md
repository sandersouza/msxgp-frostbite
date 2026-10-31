# Frostbite development status

## Current supported target

Standard-speed MSX1, 64 KiB RAM, 16 KiB VRAM, TMS9918-family VDP and built-in PSG.
No extra accessories. The owner approved the
[design](superpowers/specs/2026-10-31-frostbite-design.md) on 2026-10-31.

## What is available now

- A verified local Atari reference identity and measured NTSC steady cadence:
  262 scanlines / 19,912 CPU cycles per frame. See the
  [inventory/timing evidence](reference-inventory.md) for startup observations,
  revision/provenance limits and pending full-state replay repeatability.
- A byte-identical initial automatic disassembly/rebuild; semantic labels still
  need research in issue #3.
- The [issue roadmap](superpowers/specs/2026-10-31-frostbite-backlog.md),
  [workflow](project-workflow.md) and verified
  [baseline preservation](baseline-preservation.md).
- Locally preserved tools/environment from the supplied copy; their presence
  does not establish a fresh Frostbite installation.

Reference utilities now run with Python's standard library:
\`python3 -B scripts/reference_inventory.py\` and
\`python3 -B scripts/source_timing.py\` (the latter requires Stella 7.0/Debugger).
\`python3 -B -m unittest discover -s tests -v\` runs original-free utility tests.

There is no Frostbite MSX scaffold, build command, gameplay ROM or CI acceptance
yet. The copied Seaquest Makefile/scripts/tests/results are quarantined under
ignored .legacy/seaquest/. Do not run them as Frostbite tooling or treat their
historical pass records as current results.

## Upcoming developer entry points

[Issue #5](https://github.com/sandersouza/msxgp-frostbite/issues/5) will deliver
the reproducible macOS environment: setup/check/dry-run, pinned host tools,
cross-assembly, ROM validation and openMSX diagnostic build/run/smoke.
It must include a reproducible command-by-command fresh-clone checklist and
record which host architectures were actually tested.

[Issue #6](https://github.com/sandersouza/msxgp-frostbite/issues/6) will deliver
synthetic CI and tracking helpers without original inputs.
Do not advertise those entry points until verified deliverables exist.

## Human tests and releases

Each new testable ROM comes through a versioned GitHub release with the exact
ROM attached, hash/source commit, current state, next work and a specific human
test checklist. Development builds are prereleases. Load/mapper/controls and
expected results will be given in each release.

Issue #1 changes documentation and local preservation only, so it produces no
testable ROM and requires no human gameplay test. Automated checks, manual
emulator review and physical hardware acceptance remain separate.
