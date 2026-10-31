# Capture independent deterministic Atari traces and comparison oracles

Planning ID: P07. Status: proposed backlog; implementation has not started.
GitHub: https://github.com/sandersouza/msxgp-frostbite/issues/7

## Goal

Build independent source-execution evidence for native Z80 validation.

## Scope

Capture raw controller/console input, complete relevant RAM and TIA state, seed and source-step boundaries with frame_skip=1 and repeat probability=0; cover all four variations including two-controller cases; validate py65 adapters against Stella/ALE and include deliberate negative controls.

## Dependencies and readiness

Dependencies: [P03 / #3](https://github.com/sandersouza/msxgp-frostbite/issues/3), [P04 / #4](https://github.com/sandersouza/msxgp-frostbite/issues/4), [P05 / #5](https://github.com/sandersouza/msxgp-frostbite/issues/5).

Definition of Ready: review the proposed Frostbite design, confirm dependency delivery and relevant reference/tool inputs, and start in a dedicated forked Frostbite issue chat before editing implementation. Unresolved source behavior is a research task, never permission to guess gameplay.

## Acceptance / Definition of Done

Hash/revision/seed-bound traces reproduce independently; comparator detects injected coordinate/flag/collision/order errors; backend limitations and any instrumented two-player coverage are explicit.

Link reproducible checks, exact source/target artifact identities, limitations and integration evidence before closing. A boot alone is not gameplay acceptance.

## Tracking

Project: [MSX Game Ports #7](https://github.com/users/sandersouza/projects/7).
Type: Task (repository native issue types unavailable at planning inspection).
Priority: P2 (intended label priority:p2 is unavailable; recorded here and in project Priority).
Size: L. Estimate: 14 hours, including implementation and validation; exploratory estimate, not a deadline.
Milestone: none, following existing project convention; no milestone was created.

Target: standard-speed MSX1, 64 KiB RAM, 16 KiB VRAM, TMS9918-family VDP and built-in PSG, no expansions. The supplied Atari ROM is gameplay authority. Keep automated, manual-emulator and physical evidence distinct.

Design: [Frostbite proposed design](https://github.com/sandersouza/msxgp-frostbite/blob/codex/docs/frostbite-planning/docs/superpowers/specs/2026-10-31-frostbite-design.md).
