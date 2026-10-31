# Validate 50/60 Hz cadence, input latency and full-density budgets

Planning ID: P15. Status: proposed backlog; implementation has not started.
GitHub: https://github.com/sandersouza/msxgp-frostbite/issues/15

## Goal

Prove timing under actual active gameplay on the target hardware class.

## Scope

Measure source cadence versus MSX output; validate accumulator/catch-up if used; profile dense scenes, transitions, audio and double-step frames on unexpanded 50/60 Hz MSX1 models; test input sampling and VRAM access margins.

## Dependencies and readiness

Dependencies: [P06 / #6](https://github.com/sandersouza/msxgp-frostbite/issues/6), [P14 / #14](https://github.com/sandersouza/msxgp-frostbite/issues/14).

Definition of Ready: review the proposed Frostbite design, confirm dependency delivery and relevant reference/tool inputs, and start in a dedicated forked Frostbite issue chat before editing implementation. Unresolved source behavior is a research task, never permission to guess gameplay.

## Acceptance / Definition of Done

Long deterministic runs show no game-time drift outside stated measured tolerance; all mechanics steps remain equivalent; CPU/VRAM/input-latency measurements and worst-case margin are linked to exact ROM hashes.

Link reproducible checks, exact source/target artifact identities, limitations and integration evidence before closing. A boot alone is not gameplay acceptance.

If this issue delivers a new testable MSX ROM version, publish a versioned GitHub prerelease with the exact ROM attached, SHA-256/source commit, current state and limitations, next steps, and a concrete human test checklist (setup, controls, actions, expected results and feedback requested). Appropriate automated checks precede publication; manual/physical results remain separate. This requirement applies from diagnostic builds onward.

## Tracking

Project: [MSX Game Ports #7](https://github.com/users/sandersouza/projects/7).
Type: Task (repository native issue types unavailable at planning inspection).
Priority: P2 (intended label priority:p2 is unavailable; recorded here and in project Priority).
Size: L. Estimate: 12 hours, including implementation and validation; exploratory estimate, not a deadline.
Milestone: none, following existing project convention; no milestone was created.

Target: standard-speed MSX1, 64 KiB RAM, 16 KiB VRAM, TMS9918-family VDP and built-in PSG, no expansions. The supplied Atari ROM is gameplay authority. Keep automated, manual-emulator and physical evidence distinct.

Design: [Frostbite proposed design](https://github.com/sandersouza/msxgp-frostbite/blob/codex/docs/frostbite-planning/docs/superpowers/specs/2026-10-31-frostbite-design.md).
