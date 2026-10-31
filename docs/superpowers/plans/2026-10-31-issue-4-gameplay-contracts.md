# Original mechanics contracts and bounded probes

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Define source-addressed, testable Frostbite behavior and edge-case acceptance before native implementation.

**Architecture:** A bounded py65 CPU-slice harness executes the verified ROM with explicit RAM/register state and declared MMIO inputs. It models RAM/stack mirrors and records hardware writes, but does not simulate raster timing or fabricate collisions. Compact case definitions/results support phase/state contracts; #7 still owns aligned full-emulator oracles.

**Tech Stack:** Python stdlib, optional pinned py65 1.2.0 in the existing .venv, canonical Atari ROM, Stella/manual corroboration.

**Spec:** docs/superpowers/specs/2026-10-31-frostbite-design.md and .github/issues/frostbite/p04-specify-original-gameplay-contracts.md.

## Global Constraints

- Standard-speed MSX1, 64 KiB RAM, 16 KiB VRAM, TMS9918-family VDP and built-in PSG, no expansions.
- Original ROM SHA-256 cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834 is authority.
- No complete disassembly/ROM/graphics in public files; compact numeric probe state/results are research metadata.
- Explicitly separate CPU-slice assumptions, static source facts, hardware geometry and complete-game acceptance.
- Exclusive shared checkout on codex/docs/4-gameplay-contracts; no MSX ROM or native implementation in #4.

## Review Focus

- Hardware reads without declared stimuli must fail, not silently supply zero collisions/input.
- CPU-only results must not be promoted to raster, reachable-game-state or complete-game proof.
- Decimal flags, stack FA/FB overlap, update order and input edges must remain phase-specific.
- All four variations and both player records must have observable acceptance, including terminal/restart boundaries.
- Manual descriptions yield to canonical code; unproven geometry remains an explicit #7 gate.

## Task 1: Bounded CPU slice research tool

**Files:** scripts/mechanics_probe.py; tests/test_mechanics_probe.py; requirements-reference.txt.

**Interfaces:** execute_slice(data, case) consumes explicit PC stop set, initial RAM/registers, MMIO samples and instruction limit; returns observed RAM/registers/MMIO events without original code bytes. CLI verifies canonical input before backend creation.

- [ ] Write failing original-free tests for RAM/stack mirrors, strict MMIO, ROM immutability, bounded stop/failure and register/BCD execution using synthetic instructions.
- [ ] Run tests and observe missing behavior. Expected: tests fail before implementation.
- [ ] Implement minimal explicit bus/slice execution; pin and report backend identity; no TIA/timer emulation claims.
- [ ] Run .venv/bin/python -B -m unittest discover -s tests -v. Expected: full suite passes without original inputs.
- [ ] Commit tool/tests/dependency declaration.

## Task 2: Contracts, boundary catalog and source probes

**Files:** references/mechanics-cases.json; references/mechanics-probes.json; docs/gameplay-contracts.md; docs/handoffs/issue-4.md; local issue/development links.

**Interfaces:** Task 1 consumes committed case definitions; exact report records source/backend/utility/case hashes and observed results. Contracts cite these bounded slices and source PCs, not inferred emulator equivalence.

- [ ] Read manual and relevant source paths; derive state/phase/input/output contracts for every issue subsystem.
- [ ] Enumerate boundary cases with concrete completion/failure predicates, including still-pending TIA/long-route scenarios.
- [ ] Execute canonical CPU probes to resolve arithmetic/state/input ambiguities; compare independently derived expected observables. Expected: each implemented case passes or yields a documented corrected interpretation.
- [ ] Run all unit tests, canonical identity/probes and publication checks. Expected: pass, no private source bytes staged.
- [ ] Commit delivery, obtain one fresh independent review, fix material findings with reproduction and verification.
- [ ] Focused PR/In review, integrate when DoD passes, close/Done and hand off through another exclusive successor fork.
