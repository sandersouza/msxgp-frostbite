# Reconstruct and annotate the Atari 2600 disassembly and state map

Planning ID: P03. Research delivery and independent review: PR #21; live lifecycle tracked on GitHub.
GitHub: https://github.com/sandersouza/msxgp-frostbite/issues/3

## Goal

Turn the initial byte-identical automatic disassembly into reviewed research for a native port.

## Scope

Automate DiStella/DASM round-trip; map code/data, indirect flow, RAM, arithmetic/flags, TIA/RIOT access, collision latches and frame phases; record source addresses without publishing complete original-derived source.

## Dependencies and readiness

Dependencies: [P02 / #2](https://github.com/sandersouza/msxgp-frostbite/issues/2).

Definition of Ready: review the proposed Frostbite design, confirm dependency delivery and relevant reference/tool inputs, and start in a dedicated forked Frostbite issue chat before editing implementation. Unresolved source behavior is a research task, never permission to guess gameplay.

## Acceptance / Definition of Done

Reassembly is byte-identical; routines and state entries needed for gameplay are reviewed with provenance and uncertainty; code/data heuristics are not presented as semantic proof.

Link reproducible checks, exact source/target artifact identities, limitations and integration evidence before closing. A boot alone is not gameplay acceptance.

If this issue delivers a new testable MSX ROM version, publish a versioned GitHub prerelease with the exact ROM attached, SHA-256/source commit, current state and limitations, next steps, and a concrete human test checklist (setup, controls, actions, expected results and feedback requested). Appropriate automated checks precede publication; manual/physical results remain separate. This requirement applies from diagnostic builds onward.

## Delivery evidence

Delivery PR: https://github.com/sandersouza/msxgp-frostbite/pull/21

- [Reconstruction and reviewed state map](https://github.com/sandersouza/msxgp-frostbite/blob/codex/chore/3-reference-disassembly/docs/reference-disassembly.md), [compact map](https://github.com/sandersouza/msxgp-frostbite/blob/codex/chore/3-reference-disassembly/references/disassembly-map.json), and [handoff](https://github.com/sandersouza/msxgp-frostbite/blob/codex/chore/3-reference-disassembly/docs/handoffs/issue-3.md).
- Canonical original and two fresh reconstructed outputs: 4096 bytes, SHA-256 `cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834`.
- 26 original-free utility tests pass. Real DiStella/DASM round-trip passes; the short-input-name regression covers the pinned backend's filename limit.
- Reviewed partition: 3374 code bytes / 1769 instructions, 722 data/trailing-word bytes, 19 JSR entries / 34 call sites, all 128 physical RAM bytes mapped. Direct targets checked at instruction boundaries.
- Static review documents shared entries/flags, all hardware reads, collision clear/sample windows, reset preservation, fractional arithmetic, decimal score/temperature and RNG sites.
- Independent review's sole Important finding (three nested reset calls and FA/FB stack overlap) was reproduced by a bounded CPU probe, corrected and verified RED→GREEN; all 26 tests and a fresh real rebuild pass afterwards. No Critical or Minor findings remain.
- Dynamic contracts, complete path coverage/aligned replay and native/physical acceptance remain #4/#7 and later work. No MSX ROM or release is produced by this research issue.

## Project metadata

Project: [MSX Game Ports #7](https://github.com/users/sandersouza/projects/7).
Type: Task (repository native issue types unavailable at planning inspection).
Priority: P2 (intended label priority:p2 is unavailable; recorded here and in project Priority).
Size: L. Estimate: 12 hours, including implementation and validation; exploratory estimate, not a deadline.
Milestone: none, following existing project convention; no milestone was created.

Target: standard-speed MSX1, 64 KiB RAM, 16 KiB VRAM, TMS9918-family VDP and built-in PSG, no expansions. The supplied Atari ROM is gameplay authority. Keep automated, manual-emulator and physical evidence distinct.

Design: [Frostbite approved design](https://github.com/sandersouza/msxgp-frostbite/blob/main/docs/superpowers/specs/2026-10-31-frostbite-design.md).
