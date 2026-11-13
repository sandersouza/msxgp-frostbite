# Compact Floe Contact Kernel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Prove an actual small Z80 floe-contact component before replacing the accepted game's tables.

**Architecture:** Shared seven-byte footprints and a420-byte independent shadow channel. A mapperless component fixture compares actual Z80 results with the accepted ROM's contact oracle. This fixture is not a playable game release and does not change the default build.

**Tech Stack:** Python, sjasmplus, Z80, openMSX, existing local original/baseline.

**Spec:** `docs/superpowers/specs/2026-11-13-compact-native-formats-design.md`

## Global Constraints

- Standard MSX1,64KiB RAM/16KiB VRAM, no mapper or turbo for the component.
- Accepted v30 remains immutable and the default playable artifact.
- Generated original-derived inputs/captures remain ignored.
- Geometric bit7 domain is playerX9..153 only; other coordinates, enemies and
  shore remain explicit unsolved work. Bit6 retains all controls/Y/absoluteX.

## Review Focus

- Y clipping at45/49/50/68/74/77 and the outside sentinel must preserve latches.
- Reflected glyphs and terminal19-byte views must use the source bytes exactly.
- Footprint aliases must preserve three copies and modulo160 positions.
- Actual Z80 must preserve IX/IY/SP and avoid mapper/RAM writes outside its ABI.
- A component cycle measurement must not be claimed as whole-game cadence.

## Task 1: Host compiler and source oracle

Files: `scripts/compact_floe.py`, `tests/test_compact_floe.py`.

- [x] Write hand-derived synthetic footprint/convolution tests; observe RED.
- [x] Implement pure footprint and glyph convolution helpers and strict
  emitted-table reader. Factor/check all shadow cells and the complete interior
  bit7 domain against the immutable contact table oracle.
- [x] Run synthetic tests, exact finite comparisons and full host suite.

## Task 2: Actual Z80 component and cycle proof

Files: `src/compact_floe_kernel.asm`, `scripts/compact_floe_probe.py`.

- [x] Build a fresh ignored fixture/expected-output harness before the kernel;
  verify it fails while the component is absent.
- [x] Implement a register/stack-bounded Z80 component. Inputs are seven bytes
  atC780..C786: control, relative sourceY, relative floeX, pose, shift, reflection,
  absolute floeX. Return the exact electrical byte in A; clobber AF/BC/DE/HL
  only. No scratch write or mapper access.

Measured refinement: the420-byte shadow dictionary admits an exact scalar rule,
verified against all8,704,000cells. The component uses zero shadow-table bytes;
the footprint/glyph data occupy3,147bytes and initial native smoke passes20,000
cases. Full native-domain qualification is still pending.
- [ ] Exercise all shared footprints/Y/literal views and all shadow-X entries
  on actual standard-speed Z80. Record exact outputs, cycles and preserved ABI.
- [ ] Compare cold/loading layout and bounds, document component size and mean/
  worst cycles. Keep the actual original-contact oracle independent of the
  implementation and reject any mismatch.
- [ ] Review and commit the component with explicit remaining edge/hazard and
  whole-game timing limitations. Issue44 stays In progress; no game release.
