# Bootstrap a reproducible macOS toolchain and MSX1 ROM scaffold

Planning ID: P05. Implemented and integrated through PR #23; diagnostic release published and downloaded assets verified.
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

## Delivery evidence

- [Toolchain/checklist](https://github.com/sandersouza/msxgp-frostbite/blob/main/docs/toolchain.md), [diagnostic evidence](https://github.com/sandersouza/msxgp-frostbite/blob/main/references/diagnostic-baseline.json), [handoff](https://github.com/sandersouza/msxgp-frostbite/blob/main/docs/handoffs/issue-5.md).
- Clean source clone/new venv/native pinned assembler builds passed setup/check/repeat on macOS arm64 with preinstalled host CLT/Homebrew/emulators. Intel/Rosetta and cold host-package installation remain untested; supplied .venv/cache were preserved.
- Deterministic16KiB Normal diagnostic SHA-256 `d46320aec4b148c3b885d54de051bc078539b65a7a8bf739bb4e9e956c2028ca`; primary and clean-clone builds match. No original Atari input is required.
- Isolated unexpanded C-BIOS MSX1/TMS9918A checks pass for enabled video/title/readouts, interrupts, keyboard edge/release and PSG register state. Rendered screenshot inspected; heartbeat-disabled runtime negative control rejected. Physical/human audio/PAL results pending.
- Current original-free suite:53 tests. Source/binary receipts, dirty/mismatch refusal, stale-result removal and release identity gate are covered.
- Release target: [v0.0.1-diagnostic](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.1-diagnostic), published from clean integrated commit `8363b3f391caeef03dcd08ab380d26280e227831` with exact tested ROM/checksums/metadata and human-test notes. All five assets were downloaded into a fresh directory; checksums and source identities passed.
- [PR #23](https://github.com/sandersouza/msxgp-frostbite/pull/23): independent review found one source-pin integrity gap; regression reproduced/fixed before compilation. No Critical or remaining Important findings.
- PR #23 is merged. Integrated source passed all53 tests and a fresh smoke before packaging. Release publication/download verification satisfies the remaining delivery gate. No native gameplay acceptance is claimed.

## Project metadata

Project: [MSX Game Ports #7](https://github.com/users/sandersouza/projects/7).
Type: Task (repository native issue types unavailable at planning inspection).
Priority: P2 (intended label priority:p2 is unavailable; recorded here and in project Priority).
Size: M. Estimate: 8 hours, including implementation and validation; exploratory estimate, not a deadline.
Milestone: none, following existing project convention; no milestone was created.

Target: standard-speed MSX1, 64 KiB RAM, 16 KiB VRAM, TMS9918-family VDP and built-in PSG, no expansions. The supplied Atari ROM is gameplay authority. Keep automated, manual-emulator and physical evidence distinct.

Design: [Frostbite approved design](https://github.com/sandersouza/msxgp-frostbite/blob/main/docs/superpowers/specs/2026-10-31-frostbite-design.md).
