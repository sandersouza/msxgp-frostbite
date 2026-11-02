# Reproduce Frostbite HUD, PSG event timing and attract flow

Planning ID: P14. Status: In progress in the dedicated Frostbite — ISSUE #14 fork.
GitHub: https://github.com/sandersouza/msxgp-frostbite/issues/14

## Goal and scope

Complete source-faithful presentation around the validated mechanics: score,
temperature, reserves, igloo, transitions and attract flow; source-derived live
graphics; ordered original audio events approximated on the built-in PSG.
Preserve channel/input ownership and document presentation differences.

## Dependencies and execution

Dependencies: [#9](https://github.com/sandersouza/msxgp-frostbite/issues/9) and
[#13](https://github.com/sandersouza/msxgp-frostbite/issues/13), both delivered/closed.
Approved native design; exclusive branch `codex/feat/14-hud-psg-attract` from
main `f516b9e22b44644bafac222a5565287f8e80a949`.
[Implementation plan](https://github.com/sandersouza/msxgp-frostbite/blob/codex/feat/14-hud-psg-attract/docs/superpowers/plans/2026-11-01-issue-14-presentation.md).

## Verified checkpoint, not issue acceptance

- Tasks 1/2 are complete; Task 3 remains in progress. Native fixed-role integration is committed in [2069310](https://github.com/sandersouza/msxgp-frostbite/commit/2069310), following component proofs in [e3cce2e](https://github.com/sandersouza/msxgp-frostbite/commit/e3cce2e). The default presentation control remains byte-identical (`0b98f3cb89e99f6e79ad9f1a3fb237c2cbfadebcd5759025a123ce33e09fcf78`).
- The explicit fixed profile matches every mapped original pixel in all 2115 ordered observations: 1690 controlled fixtures, 31 cold-route frames and 394 input-only window frames. Source128 RAM/C6 ABI, heap/redzone/SP/IFF/slot, standard 3.579545MHz/64KiB, 29-cycle VRAM writes, VBlank commit and at most four FULL sprite rectangles/line pass. New audits compare every published six-byte role key with real PGT/CGT bytes, both CPU/physical NAME pages and unchanged active NAME/PGT/CGT/SAT/full SGT bytes during preparation. Normalized scene/dirty flags and dirty-row lists also pass. Fixed lifetimes eliminate evictions; the old allocator reference-count proof is not claimed for this profile.
- Latest private ROM SHA-256 `4fd3d2d639def011c3965c819dd7db79ed9ed1ba96333cde12ac59774e0f4f16`; full-source receipt SHA-256 `76f3462de5b2e0af9fae251043a09365ad14528d5a50cb4744bfa35d96f2915e`. Injected preparation still reaches 880271 cycles. A fresh continuous 600-frame keyboard/model-pixel run records 254 over-budget frames, maximum 912884 busy cycles and 1326 skipped VDP frames. These failures are retained. No human ROM or real-time game delivery is qualified.
- The same ROM separately passes all12 immutable original input-only routes: 24820 complete CPU/all128RAM checkpoints and their progression/turn/terminal milestones, real controller/console sampling and zero canonical state injections; maximum native logical step26372 cycles. This new CPU-only replay executes native mechanics/contact acquisition, not paced presentation or PSG. Its success does not replace combined game acceptance.
- Fixed roles reserve56/60/50 dynamic slots per generation and22 footer cells. The complete floe-strip native component passes39680 algebra combinations (all160 roots × signed delta-11..19 × eight Y phases), eight Y boundaries and eight invalid parameter cases. Whole count/ID arrays and unused bytes are checked. These39696 cases are not additional original rasters or a whole-frame budget verdict.
- Actual fixed publication/earlier-copy tests pass1176 cases with a deterministic constructor stub, full metadata,16KiB VRAM, both CPU NAME pages and copy-specific fusion ordinals. A missing ordinal on the memo fast path was reproduced at original case318, captured by a failing native regression and corrected. Separate actual-Z80 proofs cover10112 geometry cases,4705 current whole typed tile/error cases,1382 old allocator operations and4679 normalized dirty-state cases. Water normalization passes7680 mask/foreground/clip pixel combinations. Whole-suite checkpoint:427 original-free tests and staged public-source policy pass.
- To make resident code space available, the fixed profile moves the exact6400-byte floe root/base directory to free cartridge bank255. Record/block/tree contents and IDs are unchanged; every far read selects its declared bank. All12 fresh CPU routes above exercise this ROM. No extra RAM or hardware is required.
- Pinned Stella7 captures full160×210 rasters, F019/F476/F019 CPU/all128RAM and every ordered TIA audio write. Independent repeats, input/restore journals, checkpoints/capsules and raw hashes pass. Source receipt producer5e82791; SHA-256 `874e8e309afa19ff0ba3bbf34532e3a8ed14887b7a53184d69410a5bd0ed0247`. [Compact source receipt](https://github.com/sandersouza/msxgp-frostbite/blob/codex/feat/14-hud-psg-attract/references/presentation-source-result.json). Overlapping observation windows do not establish whole-game acceptance.
- All128 even Atari RGB codes were measured twice; the original34 calibrated codes remain identical. Stella7 is render authority. Four old-ALE controlled left-edge bear disagreements and right-edge263-line frames remain documented. No physical Atari verdict or natural reachability of injected extremes is inferred.
- Remaining work: reduce complete live renderer cost, optimize live P0 construction and meet NTSC/PAL deadlines in all four views; implement ordered built-in PSG preserving both controller GPIO ports and both PAL logical steps; then combined natural-route acceptance, one final review, clean-main rebuild and immutable prerelease. No runtime Atari interpreter, prerecorded route/frame playback, replacement mechanics or extra hardware is used.

Private incomplete candidates remain research artifacts. No new human-testable ROM has qualified or been offered. The published [v0.0.6-progression](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.6-progression) remains unchanged. Historical/offline success is not current combined-game proof.

## Acceptance / Definition of Done

HUD, graphics and sound events agree with source state/time; automated checks
pass and visual/listening review is recorded separately. No presentation-induced
mechanic changes or extra hardware. Link exact source/target identities,
reproducible checks, limitations and integrated delivery evidence before closing.
A boot alone is not gameplay acceptance.

Every newly testable ROM, including a useful diagnostic, requires a versioned
GitHub prerelease with the exact tested ROM, SHA-256 and source commit attached.
Notes state current implementation/checks/limitations, next issues and concrete
human tests: setup/mapper/controls, actions, expected results and feedback.
Relevant automated checks precede publication. Changed bytes require a new
version; automated, manual-emulator and physical evidence stay separate.

## Tracking and target

[MSX Game Ports #7](https://github.com/users/sandersouza/projects/7): In progress.
Type Task; Priority P2; Size L; exploratory estimate12 hours, not a deadline.
Native issue types/priority labels unavailable at planning; project fields and
this body retain those values. No milestone, following repository convention.

Standard-speed MSX1,64KiB RAM,16KiB VRAM,TMS9918-family and built-in PSG;
no expansions/turbo/disk/additional sound chip. Supplied original ROM is gameplay
authority. English repository/GitHub content; Brazilian Portuguese owner updates.
[Approved design](https://github.com/sandersouza/msxgp-frostbite/blob/main/docs/superpowers/specs/2026-10-31-frostbite-design.md).
