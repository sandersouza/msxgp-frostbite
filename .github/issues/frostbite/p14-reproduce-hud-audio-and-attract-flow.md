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

- Tasks 1/2 are complete; Task 3 remains in progress. Latest committed graphics optimization: [084b4c8](https://github.com/sandersouza/msxgp-frostbite/commit/084b4c8), after [0e68e16](https://github.com/sandersouza/msxgp-frostbite/commit/0e68e16) source-player shoreline streaming. Independent source-audio/PSG host policy: [3c5e38c](https://github.com/sandersouza/msxgp-frostbite/commit/3c5e38c). Task 4 host components have started while Task 3 timing remains open. Standard MSX1/64KiB/16KiB/TMS9918/built-in hardware and 4MiB ASCII16 remain unchanged. Private candidates are exploratory producer snapshots, not clean delivery seals.
- Current private ROM SHA-256 `a704108f49d7dd319427865b8f1a1fb8615554841bd87b7485a067e90d6c328c` passes all2115 original full-scene observations with zero mapped pixel differences:1690 controlled fixtures,31 cold-route frames and394 input-only window frames. Complete source128/C6 ABI, heap/redzone/SP/IFF/slot/clock,29-cycle VRAM spacing,VBlank commit, full sprite rectangles, every published six-byte key versus real PGT/CGT, both CPU/physical NAME pages and unchanged active NAME/PGT/CGT/SAT/full referenced SGT bytes pass. Normalized scene/dirty flags and row-list audits pass. Receipt SHA-256 `7e92f23d815a4e22f48cd1891a0d74bfaef9a94f9a73b0df6152855a92fe4862`. Controlled observations are not a full natural game.
- The earlier private ROM `0feceba65193bae2f3d8a169db94cdf31569b71e1cdbf444e19adf051e6685b5` passes all12 immutable original input-only CPU routes:24820 complete CPU/all128RAM checkpoints, progression/turn/terminal milestones, real console/controller sampling, zero canonical injections and maximum26372 native-step cycles. This CPU-only RPC does not execute graphics, PSG or paced presentation; it remains distinct from the graphics and timing evidence.
- Timing still FAILS. Controlled preparation reaches595103 cycles. A fresh120-frame real-keyboard/model-pixel run records maximum571692 busy cycles,22 overruns and48 skipped VDP frames against the unchanged59736-cycle NTSC limit. The last world component improved from248291 to141042 cycles. Four retained player variants reduce expensive sprite stages from12 to7 in the same input probe; the first variant/cold/header work remains too slow. These improvements are not real-time acceptance or human delivery.
- The source-player shoreline stream passes13,024 derived actual-Z80 body cases, reducing the measured worst body preparation36482→14133 cycles. Its observed table selectors come from source captures; the crossed Y/reflection/coarse/X cases are not new original rasters. Constant dirty-span masks pass6727 actual complete state/mask cases; all256 actor-change combinations are checked in both coarse positions and generations. The changed-span microbudget fails at14474 and passes at10532; last-frame dirty cost13944→10002. [Player evidence](https://github.com/sandersouza/msxgp-frostbite/blob/codex/feat/14-hud-psg-attract/docs/presentation-player-cache.md), [dirty-span evidence](https://github.com/sandersouza/msxgp-frostbite/blob/codex/feat/14-hud-psg-attract/docs/presentation-dirty-spans.md).
- Four exact player-key variants per generation fit the existing2KiB SGT, using59 of64 available16×16 pattern slots including static door/logo and the immutable mask. Source images, counts, priority and four FULL rectangles/line are preserved. Stateful actual Z80 selection passes883 cases. An eight-pattern synthetic emission test exposes active-pattern corruption in the earlier candidate; the corrected fallback invalidates all ways of the inactive generation before a large uncached draw and passes complete VRAM/metadata/eight SAT entries on both pages (max49886 cycles including RPC). The initial negative fixture was outside the emitter coordinate preconditions and is not the regression witness. [Player cache allocation and proof boundaries](https://github.com/sandersouza/msxgp-frostbite/blob/codex/feat/14-hud-psg-attract/docs/presentation-player-cache.md).
- Owned HUD publication passes78 footer and1212 resolver operations; packed header keys pass3295 cases, and consumed-glyph-span construction passes4718 typed cases with unchanged whole tiles. Complete contiguous NAME bursts pass1265 stateful whole-VRAM/CPU/list/IO operations; the observed last-frame NAME cost falls21927→14580 cycles while still sending every declared row byte. [HUD and NAME proof boundaries](https://github.com/sandersouza/msxgp-frostbite/blob/codex/feat/14-hud-psg-attract/docs/presentation-hud-publication.md).
- Floe components retain all8960 row/bear grids, original logical pattern IDs and exact6400-byte contact directory at bank255:A700/B9C0. Actual Z80 proofs include7691 cached NAME rotations,15592 dictionary/raw reads (max1389/442 cycles including RPC),61480 raw typed-constructor cases,2960 stateful owned-strip publications and40967 packed-NAME expansions. Original-derived data stays ignored. [Template architecture and measured failures](https://github.com/sandersouza/msxgp-frostbite/blob/codex/feat/14-hud-psg-attract/docs/presentation-floe-templates.md).
- The fresh original/default presentation control remains byte-identical `0b98f3cb89e99f6e79ad9f1a3fb237c2cbfadebcd5759025a123ce33e09fcf78`. Whole-suite checkpoint:477 original-free tests, diff checks and staged public-source policy pass. Pinned Stella7 full-raster/ordered-audio source observations remain unchanged: producer5e82791, source receipt SHA-256 `874e8e309afa19ff0ba3bbf34532e3a8ed14887b7a53184d69410a5bd0ed0247`. All128 even Atari RGB codes were measured twice with the original34 unchanged; Stella7 remains render authority. Earlier ALE disagreements and source-frame limitations remain documented. No physical Atari verdict is inferred.
- Audio source/host components pass:2116 original logical intervals,3499 ordered writes,1553 same-masked-value writes,1609 silent intervals and at most34 writes/interval. Initial latches come from actual structural full capsules; replay matches every independent after-capsule. All512 control/frequency repetition periods pass using compiled unchanged pinned Stella oscillator code. The finite AY projection preserves source latches and GPIO ownership in host checks; native PSG callbacks, physical histories, listening and combined timing remain pending. [Audio policy and limits](https://github.com/sandersouza/msxgp-frostbite/blob/codex/feat/14-hud-psg-attract/docs/presentation-audio.md).
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
