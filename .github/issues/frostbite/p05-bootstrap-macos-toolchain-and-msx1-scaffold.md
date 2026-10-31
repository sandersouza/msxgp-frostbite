# Bootstrap a reproducible macOS toolchain and MSX1 ROM scaffold

Planning ID: P05. Status: proposed backlog; implementation has not started.
GitHub: https://github.com/sandersouza/msxgp-frostbite/issues/5

## Goal

Provide a fresh-clone cross-development environment and an explicitly diagnostic cartridge.

## Scope

Adapt setup/check/dry-run for arm64/x86_64 where supported; pin sjasmplus/DiStella/DASM/Python dependencies; preserve existing .venv/tools; remove mandatory Atari 800/MADS requirements; add build/run/smoke/hash and ROM/RAM checks plus a command-by-command checklist.

## Dependencies and readiness

Dependencies: [P01 / #1](https://github.com/sandersouza/msxgp-frostbite/issues/1).

Definition of Ready: review the proposed Frostbite design, confirm dependency delivery and relevant reference/tool inputs, and start in a dedicated forked Frostbite issue chat before editing implementation. Unresolved source behavior is a research task, never permission to guess gameplay.

## Acceptance / Definition of Done

Setup is idempotent and fails helpfully on missing prerequisites; clean setup is tested on available architecture with other support limits recorded; deterministic scaffold boots in unexpanded MSX1 openMSX; no gameplay acceptance claim.

Link reproducible checks, exact source/target artifact identities, limitations and integration evidence before closing. A boot alone is not gameplay acceptance.

If this issue delivers a new testable MSX ROM version, publish a versioned GitHub prerelease with the exact ROM attached, SHA-256/source commit, current state and limitations, next steps, and a concrete human test checklist (setup, controls, actions, expected results and feedback requested). Appropriate automated checks precede publication; manual/physical results remain separate. This requirement applies from diagnostic builds onward.

## Tracking

Project: [MSX Game Ports #7](https://github.com/users/sandersouza/projects/7).
Type: Task (repository native issue types unavailable at planning inspection).
Priority: P2 (intended label priority:p2 is unavailable; recorded here and in project Priority).
Size: M. Estimate: 8 hours, including implementation and validation; exploratory estimate, not a deadline.
Milestone: none, following existing project convention; no milestone was created.

Target: standard-speed MSX1, 64 KiB RAM, 16 KiB VRAM, TMS9918-family VDP and built-in PSG, no expansions. The supplied Atari ROM is gameplay authority. Keep automated, manual-emulator and physical evidence distinct.

Design: [Frostbite proposed design](https://github.com/sandersouza/msxgp-frostbite/blob/codex/docs/frostbite-planning/docs/superpowers/specs/2026-10-31-frostbite-design.md).
