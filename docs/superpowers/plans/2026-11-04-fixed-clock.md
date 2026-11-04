# Fixed source clock implementation plan

> Use superpowers:executing-plans. Listing/source integration is delegated under
> superpowers:dispatching-parallel-agents with disjoint file ownership.

**Goal:** preserve real-time original logic while rendering coherent full frames.
**Architecture:** IM1 VBlank source service, snapshot renderer and pending-frame commit.
**Tech Stack:** standard64KiB MSX1, TMS9918/PSG, Z80/RAM kernel, Python/openMSX.
**Spec:** docs/superpowers/specs/2026-11-04-fixed-clock-design.md

## Constraints / review focus

Exact original source/input/audio, all pixels/actors/player/mask and no expansions.
Boot gates must work before RAM code load. Nested IRQs/mapper and alternate-register
restoration cannot corrupt a ROM stream. Address latches must remain atomic and
commits finish in VBlank. Snapshot/CPU scratch/stack do not overlap. PAL source
accumulator remains exact; report actual render cadence independently.

- [x] TDD listing inventory and corresponding metadata; regenerate exact Q baseline
 with full current public producers and listings, preserving every previous artifact.
- [x] Implement src/presentation_fixed_clock.asm and authenticated snapshot/mapper
 builder. TDD gates cover selectors/patch bounds/slot mapping and timing counters.
- [x] Disabled-clock source/density matrices; enabled source-clock route and exact
 original CPU/allRAM/pixels, VBlank, IRQ/bank/control-latch/slot/stack proofs.
- [x] Quantify real source and presentation rates, handler/prepare/commit tails;
 update workbook; independent whole-change review and material fixes.
- [ ] Reproduce clean committed-source candidate and publish a useful diagnostic
 prerelease with ROM/SHA/source, limitations/next work and concrete human tests.

Ruling: R's measured marginal gain rejects it as a human candidate. It remains
preserved. Existing owner authority includes a30fps presentation test, but this
does not waive correct mechanics/graphics or authorize calling slower drawing
60fps. Original-speed39 and final qualification15/16 remain independently open.
