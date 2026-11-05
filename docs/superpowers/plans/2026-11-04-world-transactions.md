# World transaction optimization implementation plan

> **For agentic workers:** Use superpowers:executing-plans; root owns the existing issue42 checkout. Independent profiling and final review are read-only.

**Goal:** Reduce skipped pictures by reducing complete ice/enemy preparation at unchanged source clock.
**Architecture:** Keep T as immutable control. Compile final ice NAME templates for the legal row/coarse domain into certified empty contact tails; use a RAM-resident private decoder and avoid the redundant packed-name read. Replace the enemy cell walker with register-held cursors, retaining exact clipping, zero masks and the original fusion fallback.
**Tech Stack:** Python, sjasmplus Z80, openMSX, artifact-tool XLSX.
**Spec:** docs/superpowers/specs/2026-10-31-frostbite-design.md; docs/fixed-clock-cadence-feedback.md; latest owner authorization.

## Global constraints

- Standard-speed MSX1, 64 KiB RAM, 16 KiB VRAM, built-in PSG.
- Supplied Atari source CPU/RAM progression and mapped pixels remain authoritative.
- No actor, color, mask, collision or source-clock reduction.
- Never modify preserved T or earlier outputs. One source writer; existing issue42 branch/chat.
- Release only the exact fully checked ROM, with hash, source commit and human test instructions.

## Review focus

- Sparse NAME table covers both coarse phases of all four rows, all deltas/roots and both generations; missing entries fail closed.
- Enemy tile-row boundary, zero cells and left/wrapped clipping retain the original pixels.
- Fusion fallback receives exact column, ordinal, name pointer and geometry ID.
- New RAM code is initialized, mapper writes tracked, protected by the existing code guard and IRQ tests.
- Compiled assets occupy only verified empty tails, with every inherited live allocation and original data preserved.

### Task 1: Final NAME transactions

- [x] Add failing host tests for legal role/program coverage, zero-to-water translation, first+code-1 and fail-closed invalid inputs.
- [x] Implement scripts/presentation_world_packets.py, scripts/build_world_transactions.py and src/presentation_world_transactions.asm. Consume exact T build and its live program directory; emit immutable new build with complete source closure.
- [x] Run focused tests, full host suite and before/after natural NTSC route. Reuse semantic pixel/owner/native oracles; no claims from helper cycles.

### Task 2: Enemy cursor

- [x] Verify expected NAME grid, clipping and fusion context against the existing geometric oracle before replacement.
- [x] Add RAM-resident register-cursor walker with unchanged geometry/bulk upload and existing fusion fallback.
- [x] Run source/density matrices and natural NTSC/PAL routes plus IRQ boundary/register checks. Retain only a measured complete-picture gain.

### Task 3: Evidence and delivery

- [x] Independent whole-change review; fix material findings once, with regression proof.
- [x] Preserve prior workbook tabs/features; append whole-route and active-picture comparison with raw receipts and gap distributions.
- [x] Commit corresponding source, rebuild clean bytes and verify exact identity. Publish versioned diagnostic prerelease, verify downloaded bytes/tag, update issue/PR/handoff.

## Execution ledger

2026-11-04: Owner explicitly authorized continued native optimization and publication. Existing dedicated branch/chat reused; no new worktree or repeated approval required. T remains immutable. Baseline passive profiling: world100548, floes52148, enemies40251 foreground cycles per active snapshot; fusion is only1615. This bounds the selected changes.

Review correction: forced geometry failure exposed an unbalanced stack in the new cursor. Moving the conditional jump after POP HL/DE/BC preserves carry, code size and valid-path timing. The directed target test rejects the former ROM and accepts the fixed candidate. All final verification is rebound to the corrected ROM before delivery. Compact immutable geometry occupancy was added after the first candidate yielded only3.25%active NTSC gain; normal fusion still uses original full geometry.

Delivery complete: v0.0.11-world-transactions-diagnostic published froma43e2f1, four assets downloaded byte-identical and remote tag verified. Final V workbook preserves all six T tabs/296476cells and native features,180independent aggregates,9stage comparisons, zero errors. Human/physical acceptance and original presentation target remain open.
