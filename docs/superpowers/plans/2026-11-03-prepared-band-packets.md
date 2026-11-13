# Prepared band packets implementation plan

> Execute inline using superpowers:executing-plans; autonomous implementation
> authorized. This replaces the failed shared-residency delivery hypothesis.

**Goal:** direct fixed-band output with bounded CPU work and whole-frame evidence.
**Architecture:** lossless14-bit contact blocks reclaim bank-local asset tails;
source-derived fixed packets replace per-tile ice resolution and metadata.
**Spec:** docs/superpowers/specs/2026-11-03-prepared-band-packets-design.md
**Tech Stack:** Z80/sjasmplus, Python .venv, openMSX, original source oracles.

## Constraints / review focus

MSX1/64KiB/16KiB/PSG, unchanged original mechanics/pixels/actors/input/audio;
M-C immutable; no extra ROM mapper bits, no player tiles. Validate high packed
bits and field neighbours, contact bank boundaries, lazy old-ice metadata,
same-program/different-tuple transitions and complete CGT interval ownership.

### Task 1: Contact14 storage and executable proof

- [x] Synthetic packing/field tests fail then pass.
- [x] Authenticated M-C builder repacks only block bodies and patches resident
  address/field extraction. Prove all59246×16 old indices equal independently.
- [x] Actual Z80 reads every packed block's16 fields; preserve ABI and guards.

### Task 2: Ready ice packets and physical role audit

- [x] Compile all1280 packets into reclaimed tails, prove original bytes/keys.
- [x] Implement direct strip IO/color identity and lazy raw-key fusion lookup.
- [x] Target full-template cold/hit/color/owner cases plus independent negative
  metadata/visible-reference tests, then complete source and density matrices.

### Task 3: Full-frame decision and delivery

- [x] Matched NTSC/PAL original CPU/RAM/pixel/input routes with all decoder costs.
- [x] Update new workbook; complete seals and final review remain in Task3.
- [ ] Independent review, relevant checks, GitHub issue/PR and useful-ROM release
  with exact artifact/source/hash and human tests. Keep unmet cadence gates open.
