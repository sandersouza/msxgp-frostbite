# Igloo Colors Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reuse valid igloo PGT while updating only its exact CGT when shape stays unchanged.
**Architecture:** A scoped fixed-role publisher with exact-key hit, certified color-only path and unchanged full fallback. Additive builder from sealed v0.0.16; no new RAM/VRAM.
**Tech Stack:** Z80/sjasmplus, Python host models/oracles, standard MSX1/openMSX, artifact-tool workbook.
**Spec:** `docs/superpowers/specs/2026-11-12-igloo-colors-design.md`

## Global Constraints

- Standard-speed MSX1,64KiB RAM/16KiB VRAM,TMS9918-family VDP,built-in PSG; no expansions/turbo.
- Original source CPU/all128-RAM, input/audio order, graphics and mechanics remain exact in bounded checks.
- Parent151sources and all sealed evidence immutable. Root alone edits tracked checkout.
- Issue42 remains open; draft PR43 stays stacked on41. Every new testable ROM gets an exact-asset prerelease.

## Review Focus

- Background14 or nonuniform edge patterns must use full fallback.
- Zero upper/lower masks retain FF PGT rows and unmodified background colors.
- Cold/stale metadata and shape changes must upload the full correct tile.
- Both pages, forced IDs and invalid contexts retain ownership/validation behavior.
- Interrupts while reading banked CGT preserve registers, mapper shadow and visible data.

### Task1: Certified publisher and complete-route evidence

**Files:** create `scripts/presentation_igloo_colors.py`, `src/presentation_igloo_colors.asm`, `scripts/build_igloo_colors.py`, `tests/test_presentation_igloo_colors.py`.
**Interfaces:** `uniform_background(tile:bytes)->bool`; `can_reuse_pattern(previous:bytes,current:bytes,backgrounds:dict)->bool`; `compile_colors(backgrounds:dict)->(bytes,bytes)`; `build(base:Path,out:Path)->dict`.

- [ ] Write tests for valid color changes, changed masks/roles, invalid metadata, nonuniform/14 backgrounds and zero masks; compare compiled CGT against independent `presentation_constructors.construct`.
- [ ] Run tests RED before implementation; implement the minimal generator/certificate and run GREEN.
- [ ] Assemble the scoped publisher. Verify allocation, all2560 native far pointers and151source hashes; build into a new ignored directory.
- [ ] Run full natural NTSC/PAL via `presentation_ready_check.py`, measure cadence/landings and passive full foreground/ISR; inspect every result.
- [ ] Run matrix2115,density1920,header54,clipping10560,audio2115,9+9IRQ boundaries and AF2negative. Run complete host suite.
- [ ] Obtain one fresh independent code/rebuild/evidence review and fix material findings.
- [ ] Commit runtime, clean rebuild, verify same bytes/raw buffers, push and check exact-source CI.

### Task2: Workbook and verified diagnostic delivery

**Files:** new AD workbook under ignored outputs; `docs/igloo-colors.md`, `references/igloo-colors-{result,delivery}.json`, issue42/handoff/README updates.

- [ ] Preserve all29AB sheets; add measured whole-frame/cost/landing comparison, source/hash/qualification and limitations. Export, audit and visually verify.
- [ ] Publish next unused diagnostic version with exact ROM, workbook, source/build/validation records and checksums; notes include precise human tests and next work.
- [ ] Download all assets, verify bytes and remote tag/source; synchronize issue/PR, move In review, keep open.
- [ ] Commit delivery documentation, verify CI and clean checkout; seal new evidence only after final writes.
