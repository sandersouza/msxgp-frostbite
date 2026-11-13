# Native prepared bear implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline. Root sole tracked writer, one independent final read-only review.

**Goal:** Reduce the measured live bear bottleneck toward30FPS while preserving v20 pixels/mechanics.
**Architecture:** Prepared final bear tiles, native fixed roles and exact context fallback, original fallbacks.
**Tech Stack:** Python/Z80/sjasmplus/openMSX/artifact-tool/WebMSX.
**Spec:** `docs/superpowers/specs/2026-11-12-bear-native-design.md`.

## Global constraints

Standard MSX1/64KiB/16KiB/TMS9918/PSG, unchanged source/input/audio clock/colors.
Preserve170parent sources and32sealed roots. Same Issue42 sole writer, no merge/
close acceptance. v20c036c3...43ac exact rollback. No new sprites or P0 recoloring.

## Review focus

- Batched dirty-row retirement/control-flow certificate and direct metadata/scratch liveness.
- Empty masks and foreground==background must match original16bytes, not only pixels.
- Bear wrap/left clipping,3/4columns, both coarseYstates and dirty partial rows.
- Cached roles/white-blueice/footer/atlas and both NAME pages across source IRQ.
- Mapper transitions through RAM dispatchers and live source snapshot/code guards.
- All512descriptors and contact14speculative tail reads; fallback without stale scratch.

### Task1: Prepared native bear and ownership

- [x] Add failing tests for256byte prepared-record padding/IDs/context-index layouts and exact
  uniform-row merge, source rawmask decoding, certified uniform/fallback boundary.
- [x] Add scripts/presentation_bear_native.py,scripts/build_bear_native.py,
  src/presentation_bear_native.asm,tests/test_presentation_bear_native.py only;
  audit kernel padding/copy count and transient scratch, exact original rollback.
- [x] Pass source/density/header directed pixels/owners/active-page guards.

### Task2: Whole-game comparison and qualified delivery

- [x] Measure full regular NTSC/PAL plus live bear, phases/foreground/ISR/gaps/
 26landings; reject regressions with no meaningful gain. Iterate toward30FPS.
- [x] Pass host/audio/realIRQ/negative/independent actualZ80/rebuild/contact/CI/
 clean-source replay checks. Preserve rejected/failed private evidence.
- [x] Update AIworkbook preserving all34historical tabs/native features, audit/preview.
- [x] Publish useful exact ROM/source/hash/human tests/WebMSX; verify downloads;
 sync issue/PR/handoff, retain rollback and honest limits; seal only new roots.
