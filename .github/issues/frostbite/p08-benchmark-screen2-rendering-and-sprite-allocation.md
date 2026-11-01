# Benchmark worst-case SCREEN 2 rendering and sprite allocation

Planning ID: P08. Status: implemented; review, integration and release verification pending.
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

## Delivery evidence

- [Measured renderer decision](https://github.com/sandersouza/msxgp-frostbite/blob/codex/feat/8-screen2-renderer-benchmark/docs/renderer-feasibility.md), [compact report](https://github.com/sandersouza/msxgp-frostbite/blob/codex/feat/8-screen2-renderer-benchmark/references/renderer-result.json) and [handoff](https://github.com/sandersouza/msxgp-frostbite/blob/codex/feat/8-screen2-renderer-benchmark/docs/handoffs/issue-8.md).
- Original-free32KiB ROM source dd7c46563252b6c3910777458bae5e9ca87eef75, SHA-256 f311480240f5f6f52a1baea835264e4cb06e5aeb05795174564c059ea15155d4. Uses16000VRAM bytes and30674ROM bytes; no mapper/expansion.
- 643 independent pixel/SAT cases, allX/phases, clipping/wrap/crowded landings/color/igloo and bank-crossing cases; actual maximum4sprites/line and29cycleminimum data spacing. Five deliberate fault classes fail for the intended reason.
- 240NTSC consecutive frames max55455/59736cycles;240PAL max65426/71364,286source reservations. Worst crossingRPC58409leaves1327cycles including the10018cycle surrogate. Native gameplay/input/audio costs remain unmeasured and must fit later.
- Canonical RAM/input/heap/stack guards and actual keyboard direction/SPACE edge/held/repress checks pass. Grid presentation quantization is explicit; original mapping/assets are9. VRAM preview is a reconstruction, not an accepted live framebuffer/manual/hardware result.
- [v0.0.2-renderer release notes and human tests](https://github.com/sandersouza/msxgp-frostbite/blob/codex/feat/8-screen2-renderer-benchmark/docs/releases/v0.0.2-renderer.md). Publish/verify the actual prerelease and attached exact ROM before closing; previous diagnostic stays unchanged.

If this issue delivers a new testable MSX ROM version, publish a versioned GitHub prerelease with the exact ROM attached, SHA-256/source commit, current state and limitations, next steps, and a concrete human test checklist (setup, controls, actions, expected results and feedback requested). Appropriate automated checks precede publication; manual/physical results remain separate. This requirement applies from diagnostic builds onward.

## Tracking

Project: [MSX Game Ports #7](https://github.com/users/sandersouza/projects/7).
Type: Task (repository native issue types unavailable at planning inspection).
Priority: P2 (intended label priority:p2 is unavailable; recorded here and in project Priority).
Size: L. Estimate: 12 hours, including implementation and validation; exploratory estimate, not a deadline.
Milestone: none, following existing project convention; no milestone was created.

Target: standard-speed MSX1, 64 KiB RAM, 16 KiB VRAM, TMS9918-family VDP and built-in PSG, no expansions. The supplied Atari ROM is gameplay authority. Keep automated, manual-emulator and physical evidence distinct.

Design: [Frostbite approved design](https://github.com/sandersouza/msxgp-frostbite/blob/main/docs/superpowers/specs/2026-10-31-frostbite-design.md).
