# Compact Shore Contact Kernel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Qualify a small shore/bear contact component before flat-runtime integration.

**Architecture:** Compile the source bear's doubled-width pixels into shared
17-row footprints. Reuse the player glyph pages and pose offsets already
qualified for ice and ordinary enemies. Compare every common-X source cell
against the accepted ROM, then execute every declared native input/view.

**Tech Stack:** Existing Python, sjasmplus, Z80 and openMSX component fixtures.

**Spec:** `docs/superpowers/specs/2026-11-13-compact-native-formats-design.md`

## Constraints and review

- Player X25..151 only; all source bear X/modes/Y and 228 player views.
- Source rows0/1 are blank in the selected aliases; retain all visual pixels.
- Reflect the eight source bits before doubling and clip without wraparound.
- Preserve IX/IY/SP and permit only bounded stack writes.
- Default game, sealed outputs and previous releases remain unchanged.
- No whole-game performance, complete-format or hardware acceptance claim.

## Task 1: Host proof

- [x] Add hand-derived width/reflection/clipping tests; observe RED.
- [x] Implement footprint compiler and independently read shore records.
- [x] Verify every common-X cell, not just representative X80.
- [x] Run focused and full synthetic host checks.

## Task 2: Native proof

- [x] Add shore fixture and observe missing-entry failure.
- [x] Implement clipped 17-row Z80 convolution with the shared input ABI.
- [x] Execute full shore corpus; verify ABI, writes, hashes and cycles.
- [x] Check unchanged floe/enemy fixture bytes against sealed controls.
- [x] Obtain independent review, document exact storage/scope and commit.

Edge contacts, copy dispatch, flat layout, cartridge/DOS/BASIC loading and
whole-game qualification remain subsequent work in issue44.
