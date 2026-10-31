# Benchmark worst-case SCREEN 2 rendering and sprite allocation

Planning ID: P08. Status: proposed backlog; implementation has not started.
GitHub: https://github.com/sandersouza/msxgp-frostbite/issues/8

## Goal

Decide a feasible Frostbite renderer before coupling mechanics to graphics.

## Scope

Prototype shore/igloo/floes with tiles and actors with sprites; measure crowded landings, row wrapping, transitions, VRAM access spacing and source-step catch-up; compare viable allocations and ROM/table costs.

## Dependencies and readiness

Dependencies: [P05 / #5](https://github.com/sandersouza/msxgp-frostbite/issues/5), [P07 / #7](https://github.com/sandersouza/msxgp-frostbite/issues/7).

Definition of Ready: review the proposed Frostbite design, confirm dependency delivery and relevant reference/tool inputs, and start in a dedicated forked Frostbite issue chat before editing implementation. Unresolved source behavior is a research task, never permission to guess gameplay.

## Acceptance / Definition of Done

A measured renderer decision stays within 16 KiB VRAM, 64 KiB RAM and standard CPU budgets with numeric margin; four-sprites-per-line behavior is addressed; collision coordinates remain source-owned; mapper selection is justified or deferred with bounds.

Link reproducible checks, exact source/target artifact identities, limitations and integration evidence before closing. A boot alone is not gameplay acceptance.

## Tracking

Project: [MSX Game Ports #7](https://github.com/users/sandersouza/projects/7).
Type: Task (repository native issue types unavailable at planning inspection).
Priority: P2 (intended label priority:p2 is unavailable; recorded here and in project Priority).
Size: L. Estimate: 12 hours, including implementation and validation; exploratory estimate, not a deadline.
Milestone: none, following existing project convention; no milestone was created.

Target: standard-speed MSX1, 64 KiB RAM, 16 KiB VRAM, TMS9918-family VDP and built-in PSG, no expansions. The supplied Atari ROM is gameplay authority. Keep automated, manual-emulator and physical evidence distinct.

Design: [Frostbite proposed design](https://github.com/sandersouza/msxgp-frostbite/blob/codex/docs/frostbite-planning/docs/superpowers/specs/2026-10-31-frostbite-design.md).
