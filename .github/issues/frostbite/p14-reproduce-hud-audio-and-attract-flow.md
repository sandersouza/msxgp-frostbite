# Reproduce Frostbite HUD, PSG event timing and attract flow

Planning ID: P14. Status: In progress in the dedicated Frostbite — ISSUE #14 fork; source raster/audio observation and native presentation integration are starting.
GitHub: https://github.com/sandersouza/msxgp-frostbite/issues/14

## Goal

Complete source-faithful presentation around the validated mechanics.

## Scope

Port score/temperature/reserves/igloo display, transitions and attract behavior; derive source audio register/event timelines and approximate on built-in PSG; test channel ownership and timing; document visual/listening differences.

## Dependencies and readiness

Dependencies: [P09 / #9](https://github.com/sandersouza/msxgp-frostbite/issues/9), [P13 / #13](https://github.com/sandersouza/msxgp-frostbite/issues/13).

Definition of Ready: review the proposed Frostbite design, confirm dependency delivery and relevant reference/tool inputs, and start in a dedicated forked Frostbite issue chat before editing implementation. Unresolved source behavior is a research task, never permission to guess gameplay.

## Acceptance / Definition of Done

HUD and sound events agree with source state/time, automated checks pass and visual/listening review is recorded separately; no extra sound hardware or presentation-induced mechanic changes.

Link reproducible checks, exact source/target artifact identities, limitations and integration evidence before closing. A boot alone is not gameplay acceptance.

If this issue delivers a new testable MSX ROM version, publish a versioned GitHub prerelease with the exact ROM attached, SHA-256/source commit, current state and limitations, next steps, and a concrete human test checklist (setup, controls, actions, expected results and feedback requested). Appropriate automated checks precede publication; manual/physical results remain separate. This requirement applies from diagnostic builds onward.

## Tracking

The clean delivered baseline is main `f516b9e22b44644bafac222a5565287f8e80a949`,
with303 original-free tests passing. Issues9/13 are closed. Exclusive branch:
`codex/feat/14-hud-psg-attract`. The approved native design is being executed
through [the issue14 plan](https://github.com/sandersouza/msxgp-frostbite/blob/main/docs/superpowers/plans/2026-11-01-issue-14-presentation.md).
Static original-graphics fit from9 is separate from live renderer feasibility;
all integrated graphics/HUD/PSG changes require fresh source/pixel/event/state
and complete standard-clock timing checks. No new ROM release is claimed yet.


Project: [MSX Game Ports #7](https://github.com/users/sandersouza/projects/7).
Type: Task (repository native issue types unavailable at planning inspection).
Priority: P2 (intended label priority:p2 is unavailable; recorded here and in project Priority).
Size: L. Estimate: 12 hours, including implementation and validation; exploratory estimate, not a deadline.
Milestone: none, following existing project convention; no milestone was created.

Target: standard-speed MSX1, 64 KiB RAM, 16 KiB VRAM, TMS9918-family VDP and built-in PSG, no expansions. The supplied Atari ROM is gameplay authority. Keep automated, manual-emulator and physical evidence distinct.

Design: [Frostbite approved design](https://github.com/sandersouza/msxgp-frostbite/blob/main/docs/superpowers/specs/2026-10-31-frostbite-design.md).
