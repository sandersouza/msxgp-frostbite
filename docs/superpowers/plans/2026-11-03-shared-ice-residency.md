# Shared ice residency implementation plan

> Execute inline with superpowers:executing-plans. Owner authorized autonomy;
> dedicated branch42 and exclusive checkout transfer already established.

**Goal:** implement exact shared physical ice residency and measure whole-frame gain.
**Architecture:** persistent per-bank hashed pool, per-page/row references and
physical NAME mapping; original game logic and other rendering remain controls.
**Tech Stack:** sjasmplus/Z80, Python .venv, openMSX, existing source oracles.
**Spec:** docs/superpowers/specs/2026-11-03-shared-ice-residency-design.md

## Global constraints

Standard MSX1/64KiB RAM/16KiB VRAM/PSG, M-C immutable, no altered mechanics,
input/audio order, pixels, colors, actors, viewport or simulation rate. Original
inputs/generated assets/traces stay ignored. Player tiles remain on hold.

## Review focus

- Clean rows keep their references while a different row changes.
- Both colors of one pattern coexist and survive alternating generations.
- Dirty row replacement cannot evict displayed or already prepared tiles.
- Fusion reads physical metadata across pages and retains separate fused roles.
- Mapper helpers return into visible code; ownership audits follow actual names.

### Task 1: Residency lifecycle and target builder

Files: scripts/presentation_shared_ice.py, src/presentation_shared_ice.asm,
tests/test_presentation_shared_ice.py; private outputs/presentation/shared-ice-o/.

- [ ] Write synthetic lifecycle/ownership negative tests; observe failure.
- [ ] Implement exact host reference policy and authenticated target builder.
- [ ] Implement bounded target pool, physical decode, old-key and init wrappers.
- [ ] Run isolated real-Z80 lifecycle cases, including eviction and hash collision.

### Task 2: Independent physical and whole-frame qualification

Files: scripts/presentation_shared_ownership.py, tests/test_presentation_shared_ownership.py,
scripts/presentation_shared_check.py; original private F profiler/input adapter.

- [ ] Write negative displayed-reference and cross-generation metadata tests.
- [ ] Validate actual NAME/PGT/CGT references and declared RAM without weakening
  guards for other roles, SAT/SGT, source state or ABI.
- [ ] Full2115 scene matrix, paired active NTSC/PAL original-input routes, dense
  synthetic scenes; compare decoded pixels and native CPU/allRAM, not tile IDs.
- [ ] Measure complete busy cost/cadence and all stage/IO distributions.

### Task 3: Review and delivery

- [ ] Update a new workbook and exact evidence seal, preserve predecessors.
- [ ] Fresh independent review; resolve important findings with meaningful checks.
- [ ] Update issue/handoff, focused PR, CI; release only a useful validated
  human-test candidate with exact ROM/hash/source and concrete tests.
- [ ] Keep original-speed and final timing/full-game gates explicitly open until met.
