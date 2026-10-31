# Reference reconstruction and reviewed state map

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Deliver a repeatable byte-identical Atari reconstruction and a source-addressed research map for issue #4.

**Architecture:** Verify the immutable input before invoking DiStella/DASM. Keep generated source, listing and rebuilt image under ignored outputs; publish compact hashes, reviewed ranges and state descriptions. The round-trip proves bytes, while source review establishes bounded semantic findings and leaves dynamic contracts to #4/#7.

**Tech Stack:** Python stdlib/unittest, pinned local DiStella, DASM, original 4096-byte image.

**Spec:** docs/superpowers/specs/2026-10-31-frostbite-design.md and .github/issues/frostbite/p03-reconstruct-and-annotate-atari-disassembly.md.

## Global Constraints

- Standard-speed MSX1, 64 KiB RAM, 16 KiB VRAM, TMS9918-family VDP and built-in PSG; no expansions.
- Supplied Atari ROM is gameplay authority; no original ROM, full disassembly or original-derived generated assets in public source.
- One issue chat owns the shared checkout; exclusive ownership transferred from #2. Work on codex/chore/3-reference-disassembly.
- Keep automatic classification, reviewed inference, dynamic emulator evidence and physical evidence distinct.
- No new MSX ROM is planned; every later testable MSX ROM requires a release.

## Review Focus

- Canonical ROM failure must happen before any external tool runs.
- A successful assembler exit with changed, truncated or prefixed bytes must fail equivalence.
- Indexed, indirect and read-modify-write hardware accesses must not inherit misleading write-register labels.
- Byte identity does not prove code/data classification, path coverage or exact gameplay contracts.
- Local original-derived artifacts must remain ignored, including failed-run outputs.

## Task 1: Verified reconstruction utility

**Files:** scripts/reference_rebuild.py; tests/test_reference_rebuild.py; references/rebuild.json.

**Interfaces:** consumes reference_inventory.verified_input; emits a compact report with tool/input/output identities and byte equality, plus ignored generated files.

- [ ] Write tests for identical/changed/short output, missing or corrupt input before backend, executable resolution and ignored artifact paths.
- [ ] Run tests and observe missing implementation failures. Expected: named new behaviors fail.
- [ ] Implement bounded subprocess reconstruction in a fresh ignored directory, preserving exact command/tool hashes and errors. No automatic authority update.
- [ ] Run the full original-free unittest suite. Expected: all tests pass.
- [ ] Run real canonical reconstruction twice, compare byte hashes and stable report fields. Expected: 4096 identical bytes; generated source timestamp need not repeat.
- [ ] Commit the utility, tests and compact report.

## Task 2: Reviewed disassembly/state handoff

**Files:** references/disassembly-map.json; docs/reference-disassembly.md; docs/handoffs/issue-3.md; local issue copy; README/development links as useful.

**Interfaces:** consumes Task 1 local listing/report. Publishes source-addressed reviewed code/data ranges, gameplay entries/state, arithmetic and hardware boundaries without complete source or tables.

- [ ] Review the entire 4 KiB listing, all direct entries and indirect addressing/control flow; inspect source uses before naming state.
- [ ] Record ranges, routine roles, all RAM regions including scratch/stack, table references, frame phases and collision latch windows. Mark unresolved meanings explicitly.
- [ ] Reproduce claims against the canonical listing and source bytes. Expected: exact address/operation correspondence, complete address coverage, no claimed dynamic gameplay acceptance.
- [ ] Run original-free suite, real rebuild and publication-boundary/whitespace checks. Expected: all pass; ignored binaries/source stay untracked.
- [ ] Commit delivery; obtain fresh independent whole-branch review and resolve material findings with reproducing tests where applicable.
- [ ] Open focused PR, move #3 In review, integrate only after its DoD passes; close/Done and transfer to another dedicated #4 fork.
