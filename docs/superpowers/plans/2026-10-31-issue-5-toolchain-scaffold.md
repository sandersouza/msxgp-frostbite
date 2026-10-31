# Reproducible macOS toolchain and MSX1 diagnostic

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** A fresh-clone macOS cross-development setup and a released, explicitly diagnostic MSX1 cartridge.

**Architecture:** Source-pinned assemblers live in a new managed .tools/frostbite subtree; existing caches/environment are preserved. Python stdlib scripts expose setup/check/dry-run and deterministic 16 KiB plain-ROM build/run/validation. Bounded isolated openMSX checks exercise boot, video, interrupts and diagnostic controls on a verified 64 KiB/16 KiB TMS9918 machine; exact tested bytes go into a prerelease.

**Tech Stack:** macOS arm64/x86_64 source builds; Python>=3.11; sjasmplus1.24.0, DiStella1015ae5, DASMv2.20.17 pinned commits; py65==1.2.0; openMSX/C-BIOS and optional Stella reference backend.

**Spec:** approved Frostbite design and .github/issues/frostbite/p05-bootstrap-macos-toolchain-and-msx1-scaffold.md.

## Global Constraints

- Standard-speed MSX1, 64 KiB RAM / 16 KiB VRAM, TMS9918-family VDP and built-in PSG, no expansions/turbo/disk.
- No original ROM/assets required for scaffold build/smoke/public tests; research inputs remain ignored.
- Preserve .venv, existing .tools, .legacy/seaquest and external snapshot. Audit/credit selected infrastructure; no wholesale inheritance.
- Exclusive branch codex/chore/5-macos-toolchain-scaffold; no native gameplay acceptance in this issue.
- Every new testable ROM requires a versioned prerelease with exact bytes/hash/source commit and concrete human tests; diagnostic ROM must be named as such.

## Review Focus

- Dry-run/check must not install or overwrite anything; dirty/mismatched existing managed tools fail helpfully.
- Fresh setup must use pinned source/dependencies and be repeatable while preserving the supplied environment.
- Valid ROM size/header is insufficient: the bounded emulator must prove current ROM boot/video/interrupt/control behavior.
- Smoke cannot reuse stale evidence, silently add RAM/VDP expansions or leak user settings.
- Published attachment, tested ROM and source commit must identify the same build; changed bytes require a new version.

## Task 1: Managed environment setup/check/dry-run

**Files:** references/tools-lock.json; scripts/environment.py; scripts/setup.sh; tests/test_environment.py.

**Interfaces:** pinned source tool paths/receipts consumed by build and reference wrappers; supported host/prerequisite inspection is separate from mutations.

- [ ] Write/run original-free tests for read-only dry-run, supported hosts, mismatched/dirty checkout refusal and binary receipt corruption.
- [ ] Implement source-pinned local preparation and preserve existing Python environments. Expected: unit tests green; missing prerequisites produce actionable failures.
- [ ] Execute setup/check twice here and from a clean source clone on arm64. Expected: second setup changes no verified tool binaries or existing environment packages; Intel limits explicit.
- [ ] Commit environment delivery and pin provenance.

## Task 2: Diagnostic ROM and bounded MSX1 verification

**Files:** src/diagnostic.asm; scripts/rom.py; scripts/smoke.py; scripts/smoke.tcl; Makefile; tests/test_rom.py; compact diagnostic evidence.

**Interfaces:** consumes verified sjasmplus path; emits 16384-byte plain-ROM, symbols, hashes/build metadata and fresh smoke result.

- [ ] Write/run failing ROM validation tests for size/header/entry/damaged artifact.
- [ ] Implement minimal SCREEN1 diagnostic with heartbeat and keyboard/joystick/fire readouts, explicit no-gameplay labeling. Expected: deterministic cross-assembly and structural validation pass.
- [ ] Run bounded isolated openMSX smoke with explicit hardware/config identity, fresh boot signature/video/interrupt/input checks and negative controls. Expected: fail on wrong binary/stale/missing result; pass only current diagnostic.
- [ ] Inspect an actual diagnostic screenshot; record automated versus manual/physical limits. Expected: legible correct diagnostic display, no gameplay claim.
- [ ] Commit ROM/tooling/checks, with no generated binary staged.

## Task 3: Fresh-clone checklist, review, release and handoff

**Files:** scripts/package_diagnostic.py; tests/test_package_diagnostic.py; docs/development.md; docs/toolchain.md; docs/releases/v0.0.1-diagnostic.md; docs/handoffs/issue-5.md; issue copy/README.

**Interfaces:** exact build/smoke artifacts and commit become release attachment/notes, with named human checks and next issues.

- [ ] Run fresh-clone setup/check/test/build/smoke twice and compare ROM bytes. Expected: pass on available arm64; other host/hardware evidence remains explicitly pending.
- [ ] Record source pins/license/provenance and reproducible command-by-command checklist; prepare human test notes.
- [ ] Test the release identity gate before implementing packaging. Expected: dirty/stale/mismatched build/smoke inputs fail; a clean matching source snapshot packages exact validated ROM bytes.
- [ ] Obtain one fresh whole-branch independent review; fix material findings with reproducing checks and green suite.
- [ ] Focused PR/In review, integrate only after DoD; build/smoke exact integrated source and publish versioned diagnostic prerelease with ROM/SHA/build metadata.
- [ ] Verify remote release downloads against tested bytes; close/Done and hand off to a dependency-ready successor in another exclusive fork.
