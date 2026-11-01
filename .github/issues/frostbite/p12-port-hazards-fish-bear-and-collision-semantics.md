# Port hazards, fish, bear and original collision semantics

Planning ID: P12. Status: In progress in dedicated Frostbite issue 12 fork; dependency #11 is integrated, closed/Done and released.
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

If this issue delivers a new testable MSX ROM version, publish a versioned GitHub prerelease with the exact ROM attached, SHA-256/source commit, current state and limitations, next steps, and a concrete human test checklist (setup, controls, actions, expected results and feedback requested). Appropriate automated checks precede publication; manual/physical results remain separate. This requirement applies from diagnostic builds onward.

## Tracking

Project: [MSX Game Ports #7](https://github.com/users/sandersouza/projects/7).
Type: Task (repository native issue types unavailable at planning inspection).
Priority: P2 (intended label priority:p2 is unavailable; recorded here and in project Priority).
Size: L. Estimate: 16 hours, including implementation and validation; exploratory estimate, not a deadline.
Milestone: none, following existing project convention; no milestone was created.

Target: standard-speed MSX1, 64 KiB RAM, 16 KiB VRAM, TMS9918-family VDP and built-in PSG, no expansions. The supplied Atari ROM is gameplay authority. Keep automated, manual-emulator and physical evidence distinct.

Design: [Frostbite approved design](https://github.com/sandersouza/msxgp-frostbite/blob/main/docs/superpowers/specs/2026-10-31-frostbite-design.md).

## Execution

Exclusive fork: `Frostbite — ISSUE #12`, thread `01a19650-5f24-78c3-b4cf-3b2942a756ac`, in the Frostbite project. Branch: `codex/feat/12-hazards-collisions`, clean base `d6f214fd8923e11eea5cd3f71bdbb0cdb7ec93f7`. The parent completed its exclusive handoff; 203 baseline host tests pass and project status is In progress.

Plan: `docs/superpowers/plans/2026-11-01-issue-12-hazard-collisions.md`. Extend independent original-clock observation to every row window and sticky shore latch, measure lossless lookup capacity/cost, then validate native acquisition plus RNG/interaction/death ordering with controlled and natural routes. Count-zero edge ghosts remain real source behavior. Prior issue 11's neutral hazard fixtures do not prove this issue's collision acceptance.

The released dependency is [v0.0.4-buildloop](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.4-buildloop), ROM SHA-256 `c298a0311eb263b4e2fdc5ce490d29880ac27ebbc92f53e492f17b7f5747d600`. Its 232-cycle worst PAL margin requires fresh crowded paced measurement for this work. Original graphics/HUD/audio and whole-game/manual/physical acceptance remain separate later gates. No new issue 12 testable ROM exists yet.

## Source research checkpoint

The additive all-window observer passes 9,444 controlled cases/all 228 literal views, 32 unchanged-Stella full CPU/RAM phase comparisons, 384 row/header/other-window invariance links and 2,560 exact cached/full-window pairs across every player X. The old floe protocol remains identical in 64 compatibility cases. A real count-zero edge ghost is reproduced.

The original odd latch is sampled during the final graphic line, not after the whole sprite. A source-clock reduction is being investigated; its remaining edge differences are explicitly unaccepted. Complete lossless lookup capacity, native acquisition and crowded natural/timing/release acceptance remain pending. Current full host suite: 211 tests passing. See `docs/hazard-collisions.md` for scope and reproduction.
