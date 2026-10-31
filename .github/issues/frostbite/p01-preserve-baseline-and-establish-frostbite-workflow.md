# Preserve the copied baseline and establish Frostbite issue/chat workflow

Planning ID: P01. Status: delivery tracked in PR #19; the live GitHub project is authoritative.
GitHub: https://github.com/sandersouza/msxgp-frostbite/issues/1

## Goal

Snapshot the supplied copy outside the active tree, record provenance and make all active guidance identify Frostbite.

## Scope

Verify backup hashes and ownership of untracked files; replace Seaquest-only active instructions and README release claims; document forked issue chats, branch/handoff ownership and the final cleanup gate.

## Dependencies and readiness

Dependencies: none.

Definition of Ready: review the proposed Frostbite design, confirm dependency delivery and relevant reference/tool inputs, and start in a dedicated forked Frostbite issue chat before editing implementation. Unresolved source behavior is a research task, never permission to guess gameplay.

## Acceptance / Definition of Done

A verified local snapshot exists; active instructions target this repository/project; inherited evidence is clearly isolated; no original inputs are published and no supplied material is lost.

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

## Implementation evidence — issue #1

Owner approval: 2026-10-31 in the planning chat ("aprovado, pode seguir"). Planning PR #18 integrated as 468bfa53ac77e99af10aa0fa22130c230d019698. A complete external baseline archive was verified (6,452 files, 4 symlinks); 1,641 isolated file relocations/copies match the original manifest. Active Frostbite guidance replaces inherited claims. See docs/baseline-preservation.md and docs/handoffs/issue-1.md for hashes, recovery, boundaries and successor actions. Independent whole-branch review found no blocking findings. Verification evidence and the integration outcome are recorded in https://github.com/sandersouza/msxgp-frostbite/pull/19; use its exact head/merge commit. No testable ROM is produced by this documentation-only delivery.
