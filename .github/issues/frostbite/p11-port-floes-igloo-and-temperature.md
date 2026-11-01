# Port ice floes, reversal costs, igloo construction and temperature

Planning ID: P11. Status: automated acceptance and independent review complete; final integration/release receipt is tracked in the live issue. Dependency #10 is integrated, closed and released.
GitHub: https://github.com/sandersouza/msxgp-frostbite/issues/11

## Goal

Implement the central build-and-enter gameplay loop without changing original timing.

## Scope

Port row movement/wrapping/activation/rearming, button reversal semantics and costs, igloo completion/entry and temperature/countdown transitions; test simultaneous landing, input and timeout events.

## Dependencies and readiness

Dependencies: [P10 / #10](https://github.com/sandersouza/msxgp-frostbite/issues/10).

Definition of Ready: review the proposed Frostbite design, confirm dependency delivery and relevant reference/tool inputs, and start in a dedicated forked Frostbite issue chat before editing implementation. Unresolved source behavior is a research task, never permission to guess gameplay.

## Acceptance / Definition of Done

Source-state comparisons and a continuous natural route demonstrate construction, entry and next-level transition; boundary/cost/timeout cases match; worst-case timing is remeasured.

Link reproducible checks, exact source/target artifact identities, limitations and integration evidence before closing. A boot alone is not gameplay acceptance.

If this issue delivers a new testable MSX ROM version, publish a versioned GitHub prerelease with the exact ROM attached, SHA-256/source commit, current state and limitations, next steps, and a concrete human test checklist (setup, controls, actions, expected results and feedback requested). Appropriate automated checks precede publication; manual/physical results remain separate. This requirement applies from diagnostic builds onward.

## Tracking

Project: [MSX Game Ports #7](https://github.com/users/sandersouza/projects/7).
Type: Task (repository native issue types unavailable at planning inspection).
Priority: P2 (intended label priority:p2 is unavailable; recorded here and in project Priority).
Size: L. Estimate: 14 hours, including implementation and validation; exploratory estimate, not a deadline.
Milestone: none, following existing project convention; no milestone was created.

Target: standard-speed MSX1, 64 KiB RAM, 16 KiB VRAM, TMS9918-family VDP and built-in PSG, no expansions. The supplied Atari ROM is gameplay authority. Keep automated, manual-emulator and physical evidence distinct.

Execution plan: docs/superpowers/plans/2026-11-01-issue-11-floe-construction.md. Exclusive branch:codex/feat/11-floe-construction, base05c5f29507ee9cfa3d2c1ceb9964eb53beae9532. The visible-phase adapter will preserve original state effects and use original-clock literal-view floe tables (raster-only collision inference was rejected by source edge probes); synthetic display geometry cannot determine contacts. Natural first-level construction/entry/next-level acceptance is distinct from the full hazard acquisition owned by12.

Design: [Frostbite approved design](https://github.com/sandersouza/msxgp-frostbite/blob/main/docs/superpowers/specs/2026-10-31-frostbite-design.md).

## Delivery evidence

Native original-clock floes and the build-and-enter loop pass automated issue acceptance.
The natural original route contains 2,254 checkpoints, completing construction at 1,733,
entry at 1,912 and next-level initialization at 2,252; it loses three reserves.
Actual paced NTSC/PAL replay checks all CPU/RAM states and 4,139 completed frames.
Geometry: 1,368 cases, including 1,081 full-original phases and 287 explicitly neutral
odd/shore cases. Whole-ROM mechanics: 86 cases; CPU: 4,497 generic/1,793 specialized.
Thirteen stress scenarios check 3,120 frames; all eight intended faults are detected.
All 203 host tests pass. Worst PAL stress margin is 232 cycles, natural PAL 1,159.

Independent whole-branch review found two Important sealing gaps; both have
RED→GREEN regression tests and a green full suite. No concrete runtime regression
or deferred minor was reported. The corrected packager binds observer acceptance
and strict replay raw identities; all existing capture identities remain unchanged.

- Tested ROM source: `81619c058e04a644564404ec4bd8582ac46cee41`.
- ROM: `frostbite-0.0.4-buildloop.rom`, 4,194,304 bytes, ASCII16.
- SHA-256: `c298a0311eb263b4e2fdc5ce490d29880ac27ebbc92f53e492f17b7f5747d600`.
- [PR #33](https://github.com/sandersouza/msxgp-frostbite/pull/33).
- [Versioned prerelease and human tests](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.4-buildloop).
- [Technical evidence/reproduction](https://github.com/sandersouza/msxgp-frostbite/blob/main/docs/floe-loop.md).
- [Compact result](https://github.com/sandersouza/msxgp-frostbite/blob/main/references/floe-result.json).
- [Handoff](https://github.com/sandersouza/msxgp-frostbite/blob/main/docs/handoffs/issue-11.md).

Synthetic graphics/silent audio, full hazard/shore acquisition (#12), later-level
progression and whole-game acceptance remain explicit limits. The natural route
uses no source/contact injections or disabled source hazards. Manual-emulator
and physical-hardware feedback remain pending. The live issue records the final
merged commit/CI and downloaded release verification before close/Done; the
prepared successor receives exclusive ownership only afterward. Legacy removal
remains #17 after replacement acceptance.
