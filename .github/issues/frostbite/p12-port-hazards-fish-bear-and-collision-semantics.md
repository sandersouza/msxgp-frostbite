# Port hazards, fish, bear and original collision semantics

Planning ID: P12. Status: proposed backlog; implementation has not started.
GitHub: https://github.com/sandersouza/msxgp-frostbite/issues/12

## Goal

Preserve interactions and death behavior independently of VDP collision hardware.

## Scope

Port spawn/RNG paths, threat movement, fish collection, bear/shore behavior and TIA-derived collision acquisition/latch timing; cover grounded/airborne and simultaneous events; include water/contact/temperature death transitions.

## Dependencies and readiness

Dependencies: [P11 / #11](https://github.com/sandersouza/msxgp-frostbite/issues/11).

Definition of Ready: review the proposed Frostbite design, confirm dependency delivery and relevant reference/tool inputs, and start in a dedicated forked Frostbite issue chat before editing implementation. Unresolved source behavior is a research task, never permission to guess gameplay.

## Acceptance / Definition of Done

Independent traces match source hazards, rewards and death sequencing across relevant stages and seeds; software collision boundary cases and negative controls pass; crowded natural play is measured.

Link reproducible checks, exact source/target artifact identities, limitations and integration evidence before closing. A boot alone is not gameplay acceptance.

## Tracking

Project: [MSX Game Ports #7](https://github.com/users/sandersouza/projects/7).
Type: Task (repository native issue types unavailable at planning inspection).
Priority: P2 (intended label priority:p2 is unavailable; recorded here and in project Priority).
Size: L. Estimate: 16 hours, including implementation and validation; exploratory estimate, not a deadline.
Milestone: none, following existing project convention; no milestone was created.

Target: standard-speed MSX1, 64 KiB RAM, 16 KiB VRAM, TMS9918-family VDP and built-in PSG, no expansions. The supplied Atari ROM is gameplay authority. Keep automated, manual-emulator and physical evidence distinct.

Design: [Frostbite proposed design](https://github.com/sandersouza/msxgp-frostbite/blob/codex/docs/frostbite-planning/docs/superpowers/specs/2026-10-31-frostbite-design.md).
