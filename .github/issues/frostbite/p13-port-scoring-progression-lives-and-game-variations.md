# Port scoring, progression, reserves and all game variations

Planning ID: P13. Status: implementation and all capture matrices pass; raw-evidence sealing, independent review and delivery remain pending.
GitHub: https://github.com/sandersouza/msxgp-frostbite/issues/13

## Goal

Complete the original state machine, including alternating-player modes.

## Scope

Port BCD scores/bonuses/overflow, extra-life thresholds/cap, progression and day/night changes, regular/advanced starts, all Game Select modes, per-player state, game over and restart; prove unused switches do not add new mechanics.

## Dependencies and readiness

Dependencies: [P12 / #12](https://github.com/sandersouza/msxgp-frostbite/issues/12).

Definition of Ready: review the proposed Frostbite design, confirm dependency delivery and relevant reference/tool inputs, and start in a dedicated forked Frostbite issue chat before editing implementation. Unresolved source behavior is a research task, never permission to guess gameplay.

## Acceptance / Definition of Done

Boundary comparisons pass and natural routes cover progression, reserves and both player transitions; all four variations have source-backed acceptance; no gameplay rules originate from Seaquest.

Link reproducible checks, exact source/target artifact identities, limitations and integration evidence before closing. A boot alone is not gameplay acceptance.

If this issue delivers a new testable MSX ROM version, publish a versioned GitHub prerelease with the exact ROM attached, SHA-256/source commit, current state and limitations, next steps, and a concrete human test checklist (setup, controls, actions, expected results and feedback requested). Appropriate automated checks precede publication; manual/physical results remain separate. This requirement applies from diagnostic builds onward.

## Current evidence

All four variations have cold input-only progression and exhaustion/restart
routes with independent full original replays (21468 logical intervals).
The current diagnostic also passes12 native routes,818 progression phases,
14828 geometry phases,652 interaction phases,135168 guarded-loop microcases,
65536 shift/flag cases and all96 route/clock/view combinations (198560 complete
CPU/128RAM checkpoints,182308 pixel frames). Fifteen stress modes and14 named
runtime faults pass. The minimum PAL margin is283 cycles; future presentation
changes require fresh timing proof.

Candidate:4194304-byte ASCII16 `0.0.6-progression`, build source
`ac146a7c82bd5ab77a5dff2deb5d5452a0478c99`, ROM SHA-256
`1223931972bd7e0ec02a8c66805cb30ac0defaad1abd71dd67c9c8a7746be5f6`.
See [technical evidence](https://github.com/sandersouza/msxgp-frostbite/blob/main/docs/scoring-progression.md),
[reproduction](https://github.com/sandersouza/msxgp-frostbite/blob/main/docs/progression-checklist.md)
and [human test instructions](https://github.com/sandersouza/msxgp-frostbite/blob/main/docs/releases/v0.0.6-progression.md).
Definitive HUD/art/audio remain #14; whole-game and manual/physical acceptance
are separate. This issue remains open until integration/release/download gates pass.

## Project metadata

Project: [MSX Game Ports #7](https://github.com/users/sandersouza/projects/7).
Type: Task (repository native issue types unavailable at planning inspection).
Priority: P2 (intended label priority:p2 is unavailable; recorded here and in project Priority).
Size: L. Estimate: 14 hours, including implementation and validation; exploratory estimate, not a deadline.
Milestone: none, following existing project convention; no milestone was created.

Target: standard-speed MSX1, 64 KiB RAM, 16 KiB VRAM, TMS9918-family VDP and built-in PSG, no expansions. The supplied Atari ROM is gameplay authority. Keep automated, manual-emulator and physical evidence distinct.

Design: [Frostbite approved design](https://github.com/sandersouza/msxgp-frostbite/blob/main/docs/superpowers/specs/2026-10-31-frostbite-design.md).
