# Port hazards, fish, bear and original collision semantics

Planning ID: P12. Status: implemented, independently reviewed, integrated and released; all four release downloads verified. Final receipt integration precedes close/Done and exclusive successor handoff. Dependency11 is integrated, closed/Done and released.
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

## Historical initial research checkpoint

The frozen additive all-window observer passes 9,476 controlled cases/all 228 literal views, 32 unchanged-Stella full CPU/RAM phase comparisons, 768 row/header/other-window invariance links, 2,560 exact object-window pairs and 2,880 shore-window pairs across every player X. The old floe protocol remains identical in 64 compatibility cases. The domain includes cold-cleared A3=0 and all 32 animated pointers, producing 264 shape/reflection/NUSIZ modes. A real count-zero edge ghost is reproduced.

Canonical source components are being acquired with frozen committed helpers, immutable backend/capsule identities and bounded workers. An explicitly partial 34,650-case ordinary-X smoke capture passed its complete raw-file/fixture/profile audit. Original-free negative tests reject missing domains, altered profiles/cases and a substituted preparation capsule, including attempts to recompute hashes.

The conditional native lookup and compact table compiler are under implementation. An original-free unit cartridge passes 464 actual standard-MSX1 Z80 checks: 288 physical sparse/slot decoder cases, 16 banked profile-directory cases including mode 264, and all 160 copy distances. Its first run caught an incorrect carry result for a noncontact distance; the corrected full check passes. This synthetic fixture is not a playable Frostbite ROM or whole-game acceptance. Current host suite: 232 tests passing.

The original odd latch is sampled during the final graphic line, not after the whole sprite. Simplified edge/bear raster formulas remain rejected. At this historical checkpoint, complete/native/paced acceptance was pending and the PR was draft. The final delivered result follows.

## Verified delivery

[PR35](https://github.com/sandersouza/msxgp-frostbite/pull/35) merged at
9454d9cbced1ff1fc2a37cf980328e7a3c9c3dc7. Exact-head and merged-main CI passed,
as did268 clean main tests/source policy and a complete byte-identical rebuild.
[v0.0.5-hazards](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.5-hazards)
publishes the exact4MiB ASCII16 ROM, SHA/build/compact-validation files. Every
download is byte-identical to the sealed package; tag source is
e83569dfde46f9bb6f39ea05817d6e3204333a54 and ROM SHA-256 is
37beb4d58bfc6566ba064ff59d48118ce6bc70655f92dcc9695cb534a88bfd93.

Acceptance includes50,289,350 source cells,14828 complete actual visible phases,
652 full-native cases,65536 Z80 shift cases,32 input-only route/clock/view
combinations (24604 completed pixel frames),15 stress modes and11 intended
faults. Tightest PAL margin645 cycles with unchanged budgets and29-cycle IO.
Independent review found no blocker; one metadata-summary minor is deferred.

See [technical evidence](https://github.com/sandersouza/msxgp-frostbite/blob/main/docs/hazard-collisions.md),
[delivery receipt](https://github.com/sandersouza/msxgp-frostbite/blob/main/references/hazard-delivery.json)
and [human tests](https://github.com/sandersouza/msxgp-frostbite/blob/main/docs/releases/v0.0.5-hazards.md).
Synthetic graphics/limited HUD/silence are explicit limits; progression/full-game,
manual-emulator and physical acceptance remain separate. Prepared dedicated
successor `Frostbite — ISSUE #13`, thread01a197d6-373a-7f30-9389-070dc5ac992b,
has the correct Frostbite project/workspace and stays idle until receipt
integration, closed/Done and explicit exclusive ownership transfer.
