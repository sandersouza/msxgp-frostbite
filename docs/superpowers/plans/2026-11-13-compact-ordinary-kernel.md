# Compact Ordinary Enemy Kernel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace interior ordinary-enemy contact tables with a small measured Z80 component.

**Architecture:** Convolve seven source collision rows, retaining all eight visual rows. Shift reflected source enemy bytes at runtime, sharing the floe component's glyph pages and pose offsets. Expected outputs come directly from the accepted ROM's ordinary common-profile tables.

**Tech Stack:** Existing Python, sjasmplus, Z80 and openMSX fixture infrastructure.

**Spec:** `docs/superpowers/specs/2026-11-13-compact-native-formats-design.md`

## Global Constraints

- Standard-speed MSX1, 64 KiB RAM, no mapper for the isolated component.
- No default-game or published-ROM change; original-derived artifacts ignored.
- Scope is common-profile player X25..151 and one original enemy copy.
  Edge coordinates, copy union, shore contacts and full-game timing stay open.

## Review Focus

- Seven collision rows must preserve the original read timing; visual height is eight.
- Signed distances -7..7 must shift and clip, not rotate pixels across edges.
- Enemy and player reflection are independent.
- Y36..60 and the zero-at61 boundary must agree with the table oracle.
- Preserve IX/IY/SP and permit only bounded guest stack writes.

## Task 1: Host model and complete common-profile proof

Files: extend `scripts/compact_floe.py`, `tests/test_compact_floe.py`.

- [x] Add hand-derived synthetic shift/clipping/last-row tests; observe RED.
- [x] Implement generic seven-row ordinary convolution and compile source bytes.
- [x] Check all 25,740 common-profile cells, each containing 228 literal views,
  against emitted v30 table records. Reject the naive eight-row alternative.
- [x] Run focused and full synthetic host tests.

## Task 2: Z80 ordinary component

Files: extend `src/compact_floe_kernel.asm`, `scripts/compact_floe_probe.py`.

- [x] Add an enemy-only fixture before assembly implementation; observe failure.
- [x] Implement shifted seven-row collision without precomputed per-position
  geometry. Use the same seven-byte ABI: shape index, Y, distance+7, pose,
  shift, player reflection, enemy reflection. Return 7/135; preserve IX/IY/SP.
- [x] Qualify all shape/reflection/Y/distance/player-view cases, record exact
  outputs and cycles, and rerun the unchanged floe fixture for regression.
- [x] Review, document and commit bounded scope. Keep issue44 In progress,
  with no whole-frame or full-format completion claim.
