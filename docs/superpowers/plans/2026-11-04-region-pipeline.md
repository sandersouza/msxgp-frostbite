# Native region preparation implementation plan

> Execute with superpowers:executing-plans. Source-chain integration is delegated
> independently under superpowers:dispatching-parallel-agents; disjoint ownership.

**Goal:** reduce complete-frame prepare cost without changing visible or source state.
**Architecture:** RAM-resident region driver, exact prepared igloo records, last-way
player lookup with original fallback, existing typed physical ownership retained.
**Tech Stack:** Z80/sjasmplus, Python .venv, standard MSX1/openMSX, original F routes.
**Spec:** docs/superpowers/specs/2026-11-04-region-pipeline-design.md

## Constraints / review focus

MSX1/64KiB/16KiB/PSG, original pixels/mechanics/input/audio, player/mask unchanged.
Cold invalid page, palette-only and one-digit updates must restore every dirty
NAME; aurora/igloo backgrounds must retain all scanline colours. Never publish
region/typed validity before both planes. Mapper changes cannot unmap executing
code. Cross-page/invalid player ways retain original replacement/fallback behavior.

## Task1: measured root cause and source integration

- [x] Add inclusive probes with missing-scaffold negatives and per-frame reset/dump.
- [x] Reprofile unchanged Q-E, compare all original evidence bytes and identify costs.
- [ ] Independently expose the full original-free F→I/J/K/L/M→contact14→P/Q chain;
 preserve historical defaults and reproduce exact hashes from a fresh output.

## Task2: native region driver

- [ ] Write failing tests for changed-column selection, igloo construction/slabs and
 RAM protection. Implement scripts/presentation_region_pipeline.py and tests.
- [ ] Implement src/presentation_region_pipeline.asm and a fresh-output authenticated
 builder scripts/build_region_pipeline.py. Do not edit source-chain agent files.
- [ ] Run actual Z80 component proofs, source and dense matrices, then paired full
 route checks. Reject wrong/slower variants and retain their evidence.

## Task3: integrated delivery

- [ ] Update a separate workbook with complete-frame results and exact evidence.
- [ ] Single independent whole-change review, TDD material fixes and full checks.
- [ ] Canonical source/ROM reproduction, useful selected prerelease, exact binary,
 SHA/source, limits/next work and concrete human setup/actions/expected results.
- [ ] Update issue42/PR43 tracking without closing unmet original-speed39 or15/16.

Ruling: existing owner autonomy replaces repeated approach/design approval rounds;
the change stays within original hardware/fidelity constraints. Measurements,
not a component estimate, determine whether the candidate is useful for delivery.
