# Recover original gameplay speed using Atari 400/800 implementation research

GitHub: https://github.com/sandersouza/msxgp-frostbite/issues/39

## Goal

Owner-directed successor to #14: analyze the supplied fan-made Atari 400/800
implementation and test equivalent MSX1 performance corrections. The Atari 2600
ROM remains the gameplay authority; the fan port is an architectural reference,
not a replacement specification. Its speed and fidelity have not been verified.

## Baseline and inputs

- Integrate #14's pre-mask-removal runtime (v0.0.9, source
  `12e204e6ecf6403fed63fd0e2f8c602ef84099a4`) into main first.
- MSX ROM SHA-256: `838b67ae6ba4c7cbed72f643f64f78b45bb404a1e43b395f36331343f6656ae6`.
  Restore/retain the black left-edge sprite mask. Local A-D experiments are
  retired and preserved; do not incorporate their viewport or sprite changes.
- Local-only reference: `references/roms/frostbite_atari800.car`, 8208 bytes,
  SHA-256 `e3fc0fd44748810def7f3313720ed65f320624ec1cc832d087d983d00e947243`.
- Current active NTSC performance is approximately 28 updates/s, not the original
  approximately 60/s cadence. Do not confuse VDP refresh with logical update rate.

## Work

- Identify the CAR container, mapper, author/version/provenance and available
  source/license; retain ROM/disassembly/derived assets locally and ignored.
- Measure the reference in a suitable Atari emulator. Analyze update scheduling,
  movement/collisions, drawing, scrolling and caching. Separate ANTIC/GTIA-specific
  hardware advantages from algorithms applicable to TMS9918/Z80.
- Produce an evidence-backed comparison and choose a bounded MSX experiment.
  Preserve the Atari 2600 behavior contracts; independently validate any rewritten
  logic rather than assuming the fan port matches the original.
- Profile CPU work and VRAM traffic against the exact masked baseline using the
  same inputs/scenarios, active play, dense rows, transitions and NTSC/PAL.
- Deliver measured improvements without removing actors, colors, visibility,
  audio, source updates or required input/collision semantics. Player-as-tiles
  remains an idea on hold, not an approved implementation.

## Definition of Ready

Input exists and is hashed; owner approved the investigation and baseline.
Main integration and dedicated issue-chat handoff must precede implementation.
Reference authorship, format details and performance are research questions.

## Definition of Done

Reproducible reference analysis and selected implementation are reviewed;
original state/input/collision/audio contracts and graphics checks pass; exact
ROM/source hashes and active/worst-case timing demonstrate original cadence on
standard MSX1 NTSC/PAL without dropped required updates. Remaining failures stay
explicit and this issue stays open if speed is not restored. Publish each new
testable ROM as a versioned prerelease with exact ROM, SHA/source, limitations,
next steps and concrete human tests, unless the owner explicitly requests a
local-only experiment. Manual and physical evidence remain separate.

#15 remains the independent final cadence/input/full-density qualification gate;
#16 remains full-game/hardware acceptance. This issue implements the corrections
needed before those gates; it does not replace them or automatically close #14.

## Tracking

Project: MSX Game Ports #7. Type: Bug. Priority: P1. Size: XL.
Estimate: 24 hours, exploratory analysis + implementation + validation, not a
deadline. Native issue types and priority labels are unavailable in the existing
repository convention; record priority in the project field. No milestone.
Target: standard-speed MSX1, 64 KiB RAM, 16 KiB VRAM, TMS9918, built-in PSG.
