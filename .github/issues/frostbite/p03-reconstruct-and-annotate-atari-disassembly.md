# Reconstruct and annotate the Atari 2600 disassembly and state map

Planning ID: P03. Status: approved backlog; implementation has not started.
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

## Tracking

Project: [MSX Game Ports #7](https://github.com/users/sandersouza/projects/7).
Type: Task (repository native issue types unavailable at planning inspection).
Priority: P2 (intended label priority:p2 is unavailable; recorded here and in project Priority).
Size: L. Estimate: 12 hours, including implementation and validation; exploratory estimate, not a deadline.
Milestone: none, following existing project convention; no milestone was created.

Target: standard-speed MSX1, 64 KiB RAM, 16 KiB VRAM, TMS9918-family VDP and built-in PSG, no expansions. The supplied Atari ROM is gameplay authority. Keep automated, manual-emulator and physical evidence distinct.

Design: [Frostbite approved design](https://github.com/sandersouza/msxgp-frostbite/blob/main/docs/superpowers/specs/2026-10-31-frostbite-design.md).
