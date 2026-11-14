# Native Bear Bitmap Renderer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Continue the already authorized Issue44 through native-format delivery; this component is not a stopping checkpoint.

**Goal:** Remove the expanded native bear representation while preserving accepted graphics, controls, mechanics and measured cadence.

**Architecture:** Build the4x3 tile mask grid from the existing six sprite pictures, then paint and publish only exact-key misses in the existing physical roles. Introduce an explicit semantic kind10 key with an independent original-ROM constructor and role audit. Retain complete sprites and native edge fallbacks.

**Tech Stack:** Z80/sjasmplus, Python3 in.venv, standard MSX1/openMSX.

**Spec:** docs/superpowers/specs/2026-11-14-native-bear-renderer-design.md

## Global Constraints

- Standard-speed MSX1,64KiB RAM,16KiB VRAM,TMS9918-family VDP, built-in PSG.
- Acceptedv0.0.30 and all published bytes remain immutable.
- Original Atari ROM controls gameplay; change renderer representation only.
- No new human release before complete automated/emulator qualification.
- Continue to the shared native executable, Normal32K attempt, DOS1 COM and BASIC BIN.

## Review Focus

- X wrap at both playfield edges, including partly hidden cells.
- Coarse transition and the last duplicated source bear row.
- Empty glyph cells and foreground color equal to either background color.
- Kind10 keys outside the bear's exact physical roles or with invalid fields.
- Concurrent source IRQ while publishing the inactive page's patterns and keys.

### Task 1: exact native mask grid

Files: create scripts/native_bear_grid_probe.py and src/native_bear_grid.asm.

- [ ] Write a512-case original-glyph mask oracle and native fixture; observe missing implementation fail.
- [ ] Implement16groups x16source phases x2coarse offsets, fixed96-byte output and bounded existing scratch.
- [ ] Run all512 native cases, preserve IX/IY/SP/IFF and all unowned writes.
- [ ] Record exact source/pattern hashes and cycles; commit the component.

### Task 2: semantic key and palette painter

Files: create scripts/native_bear_keys.py, tests/test_native_bear_keys.py and a native painter fixture.

- [ ] Add negative key/physical-role tests before implementation.
- [ ] Independently derive masks from original Atari glyphs; preserve full16-byte PGT/CGT merge semantics.
- [ ] Prove all512 grids across the original palette/background contexts and unused/empty cells.
- [ ] Keep old key kinds and their audits unchanged; commit passing component.

### Task 3: native fallback integration

Files: create scripts/build_native_bear_renderer.py, src/native_bear_renderer.asm and scripts/native_bear_renderer_check.py.

- [ ] Reproduce and bind the exact resident-enemy parent, then replace only its tile fallback.
- [ ] Preserve sprite admission, dirty union, wrap and both generations; publish kind10 keys only after full tile IO.
- [ ] Extend the independent constructor/role checker through an explicit feature node.
- [ ] Run four natural routes and2115 scenes; compare whole-frame rates and costs with the exact parent.

### Task 4: retire expanded bear assets

- [ ] Prove all old record/mask/strip consumers are superseded, then install cold CPU-read guards.
- [ ] Keep original/control tables as independent host inputs where needed.
- [ ] Run dense1920/header54 and NTSC/PAL IRQ boundaries, plus the relevant host suite.
- [ ] Archive evidence and commit the resulting component; continue the flat link.

### Task 5: continue Issue44 delivery

- [ ] Update the conservative flat object/lifetime map with the actual new allocations.
- [ ] Finish no-mapper linking, native loaders and their real DOS/BASIC boot checks.
- [ ] Recover accepted cadence, perform the final whole-branch independent review and integrate.
- [ ] Publish exact testable ROM/COM/BIN artifacts with hashes, source and human tests; close44 only after its acceptance gates pass.
