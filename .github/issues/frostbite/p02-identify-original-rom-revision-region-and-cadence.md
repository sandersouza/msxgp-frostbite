# Identify the original ROM revision, region and measured cadence

Planning ID: P02. Status: implemented in its dedicated fork; verification/review and integration tracked in https://github.com/sandersouza/msxgp-frostbite/pull/20.
GitHub: https://github.com/sandersouza/msxgp-frostbite/issues/2

## Goal

Establish the immutable gameplay authority from references/roms/frostbite.bin.

## Scope

Record size, SHA-256, MD5, cartridge layout/vectors and Stella catalog match; measure source scanlines/cadence and Reset/Select startup; distinguish catalog identity from region/revision proof.

## Dependencies and readiness

Dependencies: [P01 / #1](https://github.com/sandersouza/msxgp-frostbite/issues/1).

Definition of Ready: review the proposed Frostbite design, confirm dependency delivery and relevant reference/tool inputs, and start in a dedicated forked Frostbite issue chat before editing implementation. Unresolved source behavior is a research task, never permission to guess gameplay.

## Acceptance / Definition of Done

A hash-bound reference manifest and reproducible probe confirm the selected image and source timing; unresolved revision claims are explicitly marked; mismatch/unknown input fails clearly.

Link reproducible checks, exact source/target artifact identities, limitations and integration evidence before closing. A boot alone is not gameplay acceptance.

If this issue delivers a new testable MSX ROM version, publish a versioned GitHub prerelease with the exact ROM attached, SHA-256/source commit, current state and limitations, next steps, and a concrete human test checklist (setup, controls, actions, expected results and feedback requested). Appropriate automated checks precede publication; manual/physical results remain separate. This requirement applies from diagnostic builds onward.

## Tracking

Project: [MSX Game Ports #7](https://github.com/users/sandersouza/projects/7).
Type: Task (repository native issue types unavailable at planning inspection).
Priority: P2 (intended label priority:p2 is unavailable; recorded here and in project Priority).
Size: S. Estimate: 3 hours, including implementation and validation; exploratory estimate, not a deadline.
Milestone: none, following existing project convention; no milestone was created.

Target: standard-speed MSX1, 64 KiB RAM, 16 KiB VRAM, TMS9918-family VDP and built-in PSG, no expansions. The supplied Atari ROM is gameplay authority. Keep automated, manual-emulator and physical evidence distinct.

Design: [Frostbite approved design](https://github.com/sandersouza/msxgp-frostbite/blob/main/docs/superpowers/specs/2026-10-31-frostbite-design.md).

## Issue #2 delivery evidence

The owner-approved canonical image is verified by an immutable 4K manifest. Original-free utility tests pass (19 cases), including same-size corruption rejection before backend launch, malformed state-format checks, variable delay queues and publication boundaries. Two isolated Stella 7.0 probes measure an aligned 601-frame / 11,967,112-cycle interval: 262 lines and 19,912 CPU cycles per steady frame; Select observations progress through RAM[$80]=0,1,2,3 and Reset preserves the selected value. ALE 0.12.1+8a8fafb corroborates 262 lines in 600 post-warmup frames.

Commercial revision/upstream provenance remain unverified. Startup includes 51/310-line emulator boundary events and possible partial frames. Full checkpoint/RAM/serialized repeatability is explicitly NOT established; that alignment belongs to #7 before gameplay-equivalence acceptance. See docs/reference-inventory.md, references/source-timing.json and docs/handoffs/issue-2.md. Independent review found no blocking issues; the relative-backend-path case was fixed with a RED→GREEN regression test. No MSX ROM or physical/gameplay acceptance is claimed, and no testable-ROM release is produced by this research-only delivery.
