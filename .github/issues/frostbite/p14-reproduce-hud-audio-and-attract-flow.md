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

- Tasks 1/2 are complete; Task 3 remains in progress. Latest committed optimization: [0df7164](https://github.com/sandersouza/msxgp-frostbite/commit/0df7164), after cached floe names/direct mask publication and [dffe337](https://github.com/sandersouza/msxgp-frostbite/commit/dffe337). Standard MSX1/64KiB/16KiB/TMS9918/built-in hardware and 4MiB ASCII16 remain unchanged. Private candidates are exploratory producer snapshots, not clean delivery seals.
- Current private ROM SHA-256 `0feceba65193bae2f3d8a169db94cdf31569b71e1cdbf444e19adf051e6685b5` passes all2115 original full-scene observations with zero mapped pixel differences:1690 controlled fixtures,31 cold-route frames and394 input-only window frames. Complete source128/C6 ABI, heap/redzone/SP/IFF/slot/clock,29-cycle VRAM spacing,VBlank commit, full sprite rectangles, every published six-byte key versus real PGT/CGT, both CPU/physical NAME pages and unchanged active NAME/PGT/CGT/SAT/full referenced SGT bytes pass. Normalized scene/dirty flags and row-list audits pass. Receipt SHA-256 `6450b63fffe338f5d83b18c76640399a17f648a1b10e014baea771d975943424`. Controlled observations are not a full natural game.
- The SAME ROM freshly passes all12 immutable original input-only CPU routes:24820 complete CPU/all128RAM checkpoints, progression/turn/terminal milestones, real console/controller sampling, zero canonical injections and maximum26372 native-step cycles. This CPU-only RPC does not execute graphics, PSG or paced presentation; it remains distinct from the graphics and timing evidence.
- Timing still FAILS. Controlled preparation reaches669973 cycles. A fresh120-frame real-keyboard/model-pixel run records maximum691812 busy cycles,22 overruns and53 skipped VDP frames against the unchanged59736-cycle NTSC limit. The last world component improved from248291 to141042 cycles. Four retained player variants reduce expensive sprite stages from12 to7 in the same input probe; the first variant/cold/header work remains too slow. These improvements are not real-time acceptance or human delivery.
- Four exact player-key variants per generation fit the existing2KiB SGT, using59 of64 available16×16 pattern slots including static door/logo and the immutable mask. Source images, counts, priority and four FULL rectangles/line are preserved. Stateful actual Z80 selection passes883 cases. An eight-pattern synthetic emission test exposes active-pattern corruption in the earlier candidate; the corrected fallback invalidates all ways of the inactive generation before a large uncached draw and passes complete VRAM/metadata/eight SAT entries on both pages (max49886 cycles including RPC). The initial negative fixture was outside the emitter coordinate preconditions and is not the regression witness. [Player cache allocation and proof boundaries](https://github.com/sandersouza/msxgp-frostbite/blob/codex/feat/14-hud-psg-attract/docs/presentation-player-cache.md).
- Floe components retain all8960 row/bear grids, original logical pattern IDs and exact6400-byte contact directory at bank255:A700/B9C0. Actual Z80 proofs include7691 cached NAME rotations,15592 dictionary/raw reads (max1389/442 cycles including RPC),61480 raw typed-constructor cases,2960 stateful owned-strip publications and40967 packed-NAME expansions. Original-derived data stays ignored. [Template architecture and measured failures](https://github.com/sandersouza/msxgp-frostbite/blob/codex/feat/14-hud-psg-attract/docs/presentation-floe-templates.md).
- The fresh original/default presentation control remains byte-identical `0b98f3cb89e99f6e79ad9f1a3fb237c2cbfadebcd5759025a123ce33e09fcf78`. Whole-suite checkpoint:458 original-free tests, diff checks and staged public-source policy pass. Pinned Stella7 full-raster/ordered-audio source observations remain unchanged: producer5e82791, source receipt SHA-256 `874e8e309afa19ff0ba3bbf34532e3a8ed14887b7a53184d69410a5bd0ed0247`. All128 even Atari RGB codes were measured twice with the original34 unchanged; Stella7 remains render authority. Earlier ALE disagreements and source-frame limitations remain documented. No physical Atari verdict is inferred.
- Remaining work: reduce complete live-renderer/UI/player MISS costs and meet NTSC/PAL deadlines in all four views; implement ordered built-in PSG preserving both controller GPIO ports and both PAL logical steps; then combined natural-route acceptance, one final review, clean-main rebuild and immutable prerelease. No runtime Atari interpreter, prerecorded route/frame playback, replacement mechanics or additional hardware is used.

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
