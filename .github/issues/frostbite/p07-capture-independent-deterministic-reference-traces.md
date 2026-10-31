# Capture independent deterministic Atari traces and comparison oracles

Planning ID: P07. Status: implementation complete; independent review and integration pending.
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

## Delivery evidence

- [Reference operations and limits](https://github.com/sandersouza/msxgp-frostbite/blob/codex/chore/7-independent-reference-traces/docs/reference-traces.md), [compact hashes/report](https://github.com/sandersouza/msxgp-frostbite/blob/codex/chore/7-independent-reference-traces/references/reference-traces.json) and [handoff](https://github.com/sandersouza/msxgp-frostbite/blob/codex/chore/7-independent-reference-traces/docs/handoffs/issue-7.md).
- Stella7.0: all four variations, raw both-controller/console pins, complete structural source state, deterministic initial capsule, paired active routes and controlled selected-player fixtures; 1472 recorded checkpoints and six deliberate corruption classes per variation.
- Actual Stella instructions agree with py65 for 86 no-MMIO mechanics cases and 288 binary/decimal ADC/SBC vectors, checking CPU flags/registers and all128 RAM bytes.
- Secondary ALE0.12.1 single-player modes0/2: seed1, frame_skip1, sticky probability0, repeated27-frame whole-system states; no claimed Stella/ALE initial alignment.
- A natural1056-interval jump/refuge route repeats completely and preserves X09/reserve3 during768 wait intervals with the bear blocked at0F. Walking-only refuge was rejected by source execution. Paired125-interval console route verifies variation wrap, held Select and Reset precedence.
- Synthetic public tests require no original data or optional emulator imports. Original ROM/full states/traces remain ignored; no target ROM bytes changed. A future native adapter must obtain actual target values for the explicit logical comparison contract.

Natural complete-game/two-player turn transitions, every collision geometry, native performance, presentation and physical hardware remain separate downstream acceptance gates.

If this issue delivers a new testable MSX ROM version, publish a versioned GitHub prerelease with the exact ROM attached, SHA-256/source commit, current state and limitations, next steps, and a concrete human test checklist (setup, controls, actions, expected results and feedback requested). Appropriate automated checks precede publication; manual/physical results remain separate. This requirement applies from diagnostic builds onward.

## Tracking

Project: [MSX Game Ports #7](https://github.com/users/sandersouza/projects/7).
Type: Task (repository native issue types unavailable at planning inspection).
Priority: P2 (intended label priority:p2 is unavailable; recorded here and in project Priority).
Size: L. Estimate: 14 hours, including implementation and validation; exploratory estimate, not a deadline.
Milestone: none, following existing project convention; no milestone was created.

Target: standard-speed MSX1, 64 KiB RAM, 16 KiB VRAM, TMS9918-family VDP and built-in PSG, no expansions. The supplied Atari ROM is gameplay authority. Keep automated, manual-emulator and physical evidence distinct.

Design: [Frostbite approved design](https://github.com/sandersouza/msxgp-frostbite/blob/main/docs/superpowers/specs/2026-10-31-frostbite-design.md).
