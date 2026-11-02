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

- Tasks 1/2 are complete; Task 3 remains in progress. The latest verified template optimization is [fda58f0](https://github.com/sandersouza/msxgp-frostbite/commit/fda58f0), after [020710d](https://github.com/sandersouza/msxgp-frostbite/commit/020710d). Complete finite floe programs, cached NAME rows and direct raw-mask publication preserve the source-derived graphics. Standard MSX1/64KiB/16KiB/TMS9918/built-in hardware and the 4MiB ASCII16 cartridge remain the target.
- Private ROM SHA-256 `022f2c9dc65cbdcd11c9fe32fdf4b6e1c616d34afcf262f3fd0db1595a027deb` passes all 2115 original full-scene observations with zero mapped pixel differences: 1690 controlled fixtures, 31 cold-route frames and 394 input-only window frames. Complete source128/C6 ABI, heap/redzone/SP/IFF/slot/clock, 29-cycle VRAM spacing, VBlank commit, full sprite rectangles, every published six-byte key versus real PGT/CGT, both CPU/physical NAME pages and unchanged active-generation NAME/PGT/CGT/SAT/full SGT bytes pass. Normalized scene/dirty flags and row-list audits pass. These controlled observations are not a full natural game.
- Timing still FAILS. Controlled preparation reaches 707553 cycles. A fresh 120-frame real-keyboard/model-pixel run records maximum 732155 busy cycles, 24 overruns and 72 skipped VDP frames, against the unchanged 59736-cycle NTSC budget. Its last world component improves from 248291 to 184448 cycles; a component improvement is not a frame acceptance. The failed candidate remains private research, not a human ROM.
- Actual Z80 components: 7691 cached NAME rotations/invalid cases with all eight source-owner contexts for every root/page (maximum1248 cycles including RPC); 4306 stateful direct-mask publication operations checking the complete2304-byte metadata and16KiB VRAM (maximum2030), every raw mask, both pages/water banks, all15 foregrounds and invalid grammar; all15592 dictionary/raw-reader cases after refactoring (max1389 dictionary/603 raw). Existing template loader12816 and tag9 constructor61480 proofs remain separate. First publication/color changes define all CGT bytes; retention requires a prior matching published grammar. Original-derived artifacts remain ignored.
- The template layout retains all8960 row/bear grids, every original logical pattern ID and exact6400-byte contact directory; bank255:A700/B9C0 is selected explicitly without overwriting packed assets. Old fixed/default profiles retain their separate layouts. The fresh default control remains byte-identical `0b98f3cb89e99f6e79ad9f1a3fb237c2cbfadebcd5759025a123ce33e09fcf78`. Whole-suite checkpoint:445 original-free tests and staged public-source policy pass. [Template architecture and evidence boundaries](https://github.com/sandersouza/msxgp-frostbite/blob/codex/feat/14-hud-psg-attract/docs/presentation-floe-templates.md).
- The preceding template ROM `b8d78dfa4803b111b5fed9c84d957fac55210c055c94fe79e4543f742d5b20fb` separately passes all12 immutable original input-only routes/24820 complete CPU/all128RAM checkpoints, progression/turn/terminal milestones and real console/controller sampling with zero canonical injections, max26372 native-step cycles. That CPU-only replay does not render, play PSG or prove paced presentation; it is not relabeled as proof of newer ROMs.
- Pinned Stella7 captures full160×210 rasters, F019/F476/F019 CPU/all128RAM and every ordered TIA audio write. Independent repeats, input/restore journals, checkpoints/capsules and raw hashes pass. Source receipt producer5e82791; SHA-256 `874e8e309afa19ff0ba3bbf34532e3a8ed14887b7a53184d69410a5bd0ed0247`. All128 even Atari RGB codes were measured twice, with the original34 unchanged. Stella7 remains render authority; four earlier ALE left-edge bear disagreements and right-edge263-line frames remain documented. No physical Atari verdict or natural reachability of injected extremes is inferred.
- Remaining work: reduce complete live-renderer cost, optimize live P0 construction and meet NTSC/PAL deadlines in all four views; implement ordered built-in PSG preserving both controller GPIO ports and both PAL logical steps; then combined natural-route acceptance, one final review, clean-main rebuild and immutable prerelease. No runtime Atari interpreter, prerecorded route/frame playback, replacement mechanics or extra hardware is used.

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
