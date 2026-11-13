# Compact Native Inventory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Establish a reproducible byte budget and tested live set before changing the accepted runtime.

**Architecture:** Read-only ROM inventory plus passive openMSX observation. Preserve the existing oracle and compare raw source/ownership/timing buffers against the sealed baseline. Observed reads are a lower bound, not dead-code proof.

**Tech Stack:** Existing Python venv, unittest, openMSX, existing native checks.

**Spec:** `docs/superpowers/specs/2026-11-13-compact-native-formats-design.md`

## Global Constraints

- Standard MSX1, 64 KiB RAM / 16 KiB VRAM, TMS9918, PSG.
- Accepted control ROM SHA-256 e75535923a5751e3f4924dc7a3a2f762041b825efb7a5336650d35890cd3ff1d.
- No writes to previous evidence roots; use fresh `outputs/compact/issue44-*`.
- No runtime change or testable ROM in the inventory stage.

## Review Focus

- Bank-window aliasing must not merge equal CPU addresses in different banks.
- Missing mapper state or out-of-range access must reject the trace.
- Unobserved data must never be classified as dead.
- Corrupt ROM identity or producer changes must reject evidence.
- Instrumentation must retain exact emulated timing and source buffers.

## Task 1: ROM inventory and physical-address accounting

Files: create `scripts/compact_inventory.py`, `tests/test_compact_inventory.py`.

Interfaces: `image_inventory(data: bytes, bank_size: int = 16384) -> dict`;
`physical_offset(bank: int, address: int, image_size: int) -> int`.

- [x] Write synthetic tests for distinct physical banks, range rejection,
  partial images, padding and duplicate banks.
- [x] Run the new tests and observe missing implementation failures.
- [x] Implement the read-only accounting and immutable-output CLI.
- [x] Run focused tests and the existing full host suite.
- [x] Generate a hash-bound inventory under a fresh ignored root.

## Task 2: Passive live-set measurements

Files: create a private producer under the new inventory root; retain its hash
in the receipt. Add a maintained producer only after its observer semantics are
verified against a minimal CPU fixture and the actual route oracle.
Maintained files: `scripts/compact_live_probe.py`,
`tests/test_compact_live_probe.py`; the latter executes both completion forms
in Tcl rather than matching source text.

- [x] Verify read-watchpoint semantics, including opcode fetch and debugger
  reads, against a minimal known instruction sequence.
- [x] Run regular and bear NTSC/PAL routes with actual mapper-write tracking.
- [x] Compare source, ownership, IRQ and picture timing buffers byte-for-byte
  with the sealed control; report any difference instead of claiming parity.
- [x] Preserve raw reads, mapping statistics, configuration and producer hashes.

## Task 3: Byte ledger and next implementation boundary

Files: create `docs/compact-native-inventory.md` and a compact aggregate receipt
under `references/compact-delivery/`; update `docs/handoffs/issue-44.md`.

- [x] Audit active contact lookup and graphics allocations, distinguishing
  startup copies, live runtime, model estimates and unclassified data.
- [x] Record measured sizes and the next exact replacement/equivalence gate.
- [ ] Review the diff, commit explicit paths and update issue #44. Leave it
  In progress; do not claim formats, release or 32 KiB completion.

Later runtime/loader tasks require a concrete layout derived from this ledger;
they are not guessed here before the inventory exists.
