# Benchmark worst-case SCREEN 2 rendering and sprite allocation

Planning ID: P08. Status: implementation integrated; prerelease and downloaded exact-ROM assets verified; final handoff receipt integration pending.
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

- [Measured renderer decision](https://github.com/sandersouza/msxgp-frostbite/blob/main/docs/renderer-feasibility.md), [compact report](https://github.com/sandersouza/msxgp-frostbite/blob/main/references/renderer-result.json) and [handoff](https://github.com/sandersouza/msxgp-frostbite/blob/main/docs/handoffs/issue-8.md).
- Original-free32KiB ROM source b249373be1cc2382f87b5bb97caa865ae0c6641c, SHA-256 111ded95de3c91ff92093abe5fcee4b436150a99ee96a5a9634dfc9ebeffd4c7. Uses16000VRAM bytes and30848ROM bytes; no mapper/expansion.
- 643 independent pixel/SAT cases, allX/phases, clipping/wrap/crowded landings/color/igloo and bank-crossing cases; actual maximum4sprites/line and29cycleminimum data spacing. Five deliberate fault classes fail for the intended reason.
- 129 host tests; ten streams of240consecutiveframes cover all fixed layouts/widths and actual SPACE transitions on NTSC/PAL. CrossingNTSC58989/59736(margin747);PAL68995/71364(margin2369). RPC57139(margin2597). PAL preserves286source reservations/stream, with10018cycle surrogate calls. Native gameplay/input/audio costs remain unmeasured and must fit later.
- One fresh independent review found a SPACE-mode NTSC overrun in the unpublished candidate. Owned RED reproduction, one bulk-upload fix and the expanded strict all-mode/transition gates pass on clean b249373. Stack transcription corrected to F372. No second review.
- Canonical RAM/input/heap/stack guards and actual keyboard direction/SPACE edge/held/repress checks pass. Grid presentation quantization is explicit; original mapping/assets are9. VRAM preview is a reconstruction, not an accepted live framebuffer/manual/hardware result.
- [v0.0.2-renderer release notes and human tests](https://github.com/sandersouza/msxgp-frostbite/blob/main/docs/releases/v0.0.2-renderer.md). [Published prerelease](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.2-renderer) has six downloaded, byte-verified assets; previous diagnostic stays unchanged.

If this issue delivers a new testable MSX ROM version, publish a versioned GitHub prerelease with the exact ROM attached, SHA-256/source commit, current state and limitations, next steps, and a concrete human test checklist (setup, controls, actions, expected results and feedback requested). Appropriate automated checks precede publication; manual/physical results remain separate. This requirement applies from diagnostic builds onward.

Implementation PR [#27](https://github.com/sandersouza/msxgp-frostbite/pull/27) merged as0e17316b2c98898cf13d0b05ff9afe996d65bda8. Exact-head CI41257975158 and merged CI41258059183 pass;129host tests, zero skipped results. Build/helper blobs match frozen b249373. Tag targets integrated0e17316 with later docs/report; ROM/capture source staysb249373. Downloaded all six release assets and verifiedSHA256SUMS/exact bytes. Prepared dedicated successor `Frostbite — ISSUE #9`; close/Done8 only after the final documentation receipt integrates.

## Tracking

Project: [MSX Game Ports #7](https://github.com/users/sandersouza/projects/7).
Type: Task (repository native issue types unavailable at planning inspection).
Priority: P2 (intended label priority:p2 is unavailable; recorded here and in project Priority).
Size: L. Estimate: 12 hours, including implementation and validation; exploratory estimate, not a deadline.
Milestone: none, following existing project convention; no milestone was created.

Target: standard-speed MSX1, 64 KiB RAM, 16 KiB VRAM, TMS9918-family VDP and built-in PSG, no expansions. The supplied Atari ROM is gameplay authority. Keep automated, manual-emulator and physical evidence distinct.

Design: [Frostbite approved design](https://github.com/sandersouza/msxgp-frostbite/blob/main/docs/superpowers/specs/2026-10-31-frostbite-design.md).
