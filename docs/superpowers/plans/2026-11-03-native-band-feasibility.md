# Native band feasibility implementation plan

> **For agentic workers:** use superpowers:executing-plans inline; preserve all
> experiment evidence. User has already authorized autonomous execution.

**Goal:** replace generic enemy traversal and measure its contribution to a
whole-frame architecture budget, using M-C as an immutable control.

**Architecture:** fixed band destinations and bounded direct traversal, with
the existing exact publisher/overlap combiner as the first comparison boundary.
Bank-7 code uses resident mapper-restoring trampolines in proven-unreachable
atlas space. Build-a's initial bank-2 padding proposal was rejected by the
occupied-byte guard before any ROM was produced.

**Tech Stack:** Z80/sjasmplus, Python in .venv, openMSX, existing source oracles.

**Spec:** docs/superpowers/specs/2026-11-03-native-band-architecture-design.md

## Global constraints

- Standard MSX1, 64 KiB RAM, 16 KiB VRAM, built-in PSG; no turbo or expansions.
- No source logic, colors, actors, viewport, input, audio or update-rate reduction.
- M-C and all previous artifacts remain unchanged. Issue #39 stays open until
  original cadence is actually demonstrated.
- Public implementation contains no original ROM, derived tables or raw traces.

## Review focus

- Wrapping copies crossing columns 30/31 must retain the exact clipped pixels.
- A partially dirty band must preserve the other row and its valid references.
- Enemy/ice overlap must use its own fused role, not a shared mono role.
- Bank-switching helpers must restore code visibility before returning.
- Zero patterns, all copy modes and coarse shifts must preserve both generations.

### Task 1: Native band traversal and build contract

Files: src/presentation_band_spike.asm, scripts/presentation_band_spike.py,
tests/test_presentation_band_spike.py; ignored outputs/presentation/native-bands-n/.

Consumes pinned M-C ROM/symbols; produces a separate instrumentable diagnostic
build with patch provenance. Preserve resident routine addresses.

- [x] Test padding/parent rejection and coordinate table bounds using synthetic data.
- [x] Implement resident bank-restoring wrappers and the fixed-row walker.
- [x] Assemble, verify every changed range and execute the complete source matrix.
- [x] Resolve actual pixel/ownership/ABI failures before timing claims.

### Task 2: Whole-frame decision

Consumes Task 1 build and immutable M-C routes/density; produces paired timing
and equivalence receipts with exact identities.

- [x] Run original F profiler/input adapter in NTSC and PAL without state injection.
- [x] Run dense synthetic scenes including wrap, reflection and both coarse states.
- [x] Compare full CPU/RAM chains and three full VRAM snapshots per paced frame.
- [x] Report total active cadence, mean/P95/max, transfer volume and non-world costs.
- [x] Record a complete-frame budget ledger: measured replacement versus unresolved
  stages. Reject negative or insignificant results as a final architecture solution.

### Task 3: Review, preservation and tracking

- [x] Obtain independent code/evidence review and address material findings.
- [x] Seal private sources, results and hashes; verify M-C's entire existing seal.
- [x] Update the issue's local body, GitHub checkpoint and durable handoff.
- [x] Commit only focused original-free code/tests/docs, run relevant host checks.
- [x] Deliver the measured feasibility result; use the release workflow only for
  a qualified useful human-test ROM, never for a failed internal build.
