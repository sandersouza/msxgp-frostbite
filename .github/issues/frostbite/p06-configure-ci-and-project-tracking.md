# Configure original-free CI and GitHub project tracking

Planning ID: P06. Implementation verified; final independent review/CI/integration pending.
GitHub: https://github.com/sandersouza/msxgp-frostbite/issues/6

## Goal

Make development checks and issue tracking reproducible for Frostbite.

## Scope

Adapt pinned synthetic CI and issue/PR templates; reject tracked ROMs and original-derived assets; provide idempotent project attachment/status/priority/size/estimate workflow; preserve shared project fields and unrelated items.

## Dependencies and readiness

Dependencies: [P01 / #1](https://github.com/sandersouza/msxgp-frostbite/issues/1), [P05 / #5](https://github.com/sandersouza/msxgp-frostbite/issues/5).

Definition of Ready: review the proposed Frostbite design, confirm dependency delivery and relevant reference/tool inputs, and start in a dedicated forked Frostbite issue chat before editing implementation. Unresolved source behavior is a research task, never permission to guess gameplay.

## Acceptance / Definition of Done

Clean CI builds/tests synthetic diagnostic material without original inputs or secrets; all Frostbite items carry intended metadata; project lifecycle and per-issue handoff are demonstrated without changing another game's items.

Link reproducible checks, exact source/target artifact identities, limitations and integration evidence before closing. A boot alone is not gameplay acceptance.

If this issue delivers a new testable MSX ROM version, publish a versioned GitHub prerelease with the exact ROM attached, SHA-256/source commit, current state and limitations, next steps, and a concrete human test checklist (setup, controls, actions, expected results and feedback requested). Appropriate automated checks precede publication; manual/physical results remain separate. This requirement applies from diagnostic builds onward.

## Tracking

## Delivery evidence

- [CI/tracking checklist](https://github.com/sandersouza/msxgp-frostbite/blob/codex/chore/6-original-free-ci-tracking/docs/ci-and-tracking.md), [handoff](https://github.com/sandersouza/msxgp-frostbite/blob/codex/chore/6-original-free-ci-tracking/docs/handoffs/issue-6.md).
- Read-only Ubuntu CI builds pinned sjasmplus and the original-free diagnostic with hash-locked py65. [Run41244088656](https://github.com/sandersouza/msxgp-frostbite/actions/runs/41244088656) passed69 tests/repeated builds; downloaded artifacts contain only the three intended reports. Current suite70 adds staged-size/encoding coverage.
- Git-index source gate rejects prohibited paths, binary/non-UTF8/oversized blobs, links and disassembly markers without reading ignored research. Arbitrary text-table provenance still requires review.
- All17 intended metadata records match local issue bodies; live63-item audit and repeat apply are no-ops. Helper moved only issue6 to In review and a second apply made no write. Existing shared fields/other-game items preserved.
- ROM bytes/version remain identical to published v0.0.1-diagnostic, SHA-256 `d46320aec4b148c3b885d54de051bc078539b65a7a8bf739bb4e9e956c2028ca`; no new ROM release is produced by this infrastructure delivery. Build CI does not establish emulator/gameplay/physical acceptance.

## Project metadata

Project: [MSX Game Ports #7](https://github.com/users/sandersouza/projects/7).
Type: Task (repository native issue types unavailable at planning inspection).
Priority: P2 (intended label priority:p2 is unavailable; recorded here and in project Priority).
Size: M. Estimate: 5 hours, including implementation and validation; exploratory estimate, not a deadline.
Milestone: none, following existing project convention; no milestone was created.

Target: standard-speed MSX1, 64 KiB RAM, 16 KiB VRAM, TMS9918-family VDP and built-in PSG, no expansions. The supplied Atari ROM is gameplay authority. Keep automated, manual-emulator and physical evidence distinct.

Design: [Frostbite approved design](https://github.com/sandersouza/msxgp-frostbite/blob/main/docs/superpowers/specs/2026-10-31-frostbite-design.md).
