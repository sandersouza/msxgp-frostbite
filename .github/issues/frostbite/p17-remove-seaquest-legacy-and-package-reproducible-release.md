# Remove Seaquest legacy and package a reproducible Frostbite release

Planning ID: P17. Status: approved backlog; implementation has not started.
GitHub: https://github.com/sandersouza/msxgp-frostbite/issues/17

## Goal

Finish the repository migration only after the replacement is working and tested.

## Scope

Audit/remove obsolete game code, tests, evidence, documentation, screenshots, CI and dependencies using the verified snapshot; preserve required attribution; prove clean-clone setup/build/research/acceptance and package mapper/size/RAM/hash metadata.

## Dependencies and readiness

Dependencies: [P16 / #16](https://github.com/sandersouza/msxgp-frostbite/issues/16).

Definition of Ready: review the proposed Frostbite design, confirm dependency delivery and relevant reference/tool inputs, and start in a dedicated forked Frostbite issue chat before editing implementation. Unresolved source behavior is a research task, never permission to guess gameplay.

## Acceptance / Definition of Done

Repository contains only Frostbite implementation and justified shared infrastructure; no stale Seaquest release claims/evidence or restricted inputs are tracked; clean-clone checks pass; release readiness reflects all acceptance gates and never upgrades pending hardware evidence.

Link reproducible checks, exact source/target artifact identities, limitations and integration evidence before closing. A boot alone is not gameplay acceptance.

If this issue delivers a new testable MSX ROM version, publish a versioned GitHub prerelease with the exact ROM attached, SHA-256/source commit, current state and limitations, next steps, and a concrete human test checklist (setup, controls, actions, expected results and feedback requested). Appropriate automated checks precede publication; manual/physical results remain separate. This requirement applies from diagnostic builds onward.

## Tracking

Project: [MSX Game Ports #7](https://github.com/users/sandersouza/projects/7).
Type: Task (repository native issue types unavailable at planning inspection).
Priority: P2 (intended label priority:p2 is unavailable; recorded here and in project Priority).
Size: M. Estimate: 8 hours, including implementation and validation; exploratory estimate, not a deadline.
Milestone: none, following existing project convention; no milestone was created.

Target: standard-speed MSX1, 64 KiB RAM, 16 KiB VRAM, TMS9918-family VDP and built-in PSG, no expansions. The supplied Atari ROM is gameplay authority. Keep automated, manual-emulator and physical evidence distinct.

Design: [Frostbite approved design](https://github.com/sandersouza/msxgp-frostbite/blob/main/docs/superpowers/specs/2026-10-31-frostbite-design.md).
