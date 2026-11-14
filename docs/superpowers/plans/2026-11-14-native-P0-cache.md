# Native P0 Cache Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans inline. The owner authorized autonomous execution; this plan is not another approval checkpoint.

**Goal:** Reduce native P0 cache-hit CPU work without changing its SAT or metadata.
**Architecture:** Replace only the bounded SAT byte writer in its existing extent, then bypass one redundant initialization through the certified caller. Qualify optional all-RAM images before any new ROM.
**Tech Stack:** Z80/sjasmplus,Python in.venv,standard-speed MSX1/openMSX.
**Spec:** docs/superpowers/specs/2026-11-14-native-P0-cache-design.md

## Global Constraints

- Standard-speed MSX1,64KiB RAM,16KiB VRAM,TMS9918-family VDP,built-in PSG.
- Published v30/v31 remain immutable; no new graphics, mechanics or key semantics.
- Same sole-writer Issue44 chat/branch and accepted source/input/audio oracles.
- First measure all four routes against v31; routine-only savings never promote.

## Review Focus

- Six metadata ways remain32-byte aligned; no low-byte pointer wrap.
- Source signed displacement and Y arithmetic keep modulo256 behavior.
- SAT maximum6entries remains below C418; final IY and p_s_sat match.
- Invalid/miss/replacement cache paths still invalidate before publication.
- IRQ between foreground stores preserves register/snapshot/slot invariants.

### Task 1: exact bounded SAT publisher

**Files:** create scripts/native_p0_sat_probe.py and src/native_p0_sat.asm.
**Interfaces:** consume the v31 parent/control code; produce source-bound component-result.json with original-byte equality, all inputs/outputs/ABI/cycles.

- [ ] Write the native fixture and independent byte oracle first; run and observe missing implementation fail.
- [ ] Implement entry A=pattern id,B=count,C=X,HL=signed dy/color records; no allocation, preserve IX and final IY/p_s_sat, return NC.
- [ ] Exercise2pages x3ways x6counts xoffset/wrap vectors xedge X positions; match control assembly to actual selected code.
- [ ] Commit only when every native case passes with a measured component saving.

### Task 2: optional integration and whole-frame measurement

**Files:** modify scripts/build_native_flat_image.py; retain a source-bound optional flag.
**Interfaces:** consume Task1 proof; produce a patched native image in a fresh output root. Existing cold builder/checker consumes it unchanged.

- [ ] Verify exact old SAT prefix/body bytes and the unique certified variant-lookup caller, initial default and source instruction provenance.
- [ ] Patch the SAT body within its original extent and redirect only the caller to .scan; preserve all other entry/miss metadata semantics.
- [ ] Run fresh control/candidate source-defined cold NTSC/PAL regular/bear routes with unchanged input-only/pixel/owner/IRQ oracles, then2115 scenes if worthwhile.
- [ ] Select only a defensible whole-frame improvement; otherwise retain private evidence and revert optional runtime selection.

### Task 3: continue Issue44 delivery

- [ ] If selected, qualify actual new native ROM/DOS/BASIC, density/header/IRQ and host suite; update measurements and obtain fresh focused review.
- [ ] Publish changed testable bytes as a new version, preserve rollback and continue until Issue44 acceptance passes. No silent replacement, merge or Done while cadence acceptance remains unresolved.
