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

- Tasks1/2 are complete; Tasks3/4 remain in progress. Ordered native source audio is integrated in [9e8c3e5](https://github.com/sandersouza/msxgp-frostbite/commit/9e8c3e5); fixed-owner ROM name expansion is committed in [1a602e2](https://github.com/sandersouza/msxgp-frostbite/commit/1a602e2). Standard MSX1/64KiB/16KiB/TMS9918/built-in PSG and4MiB ASCII16 remain unchanged. These private producer snapshots are exploratory, not clean delivery seals.
- Current combined private ROM SHA-256 `e8661659cf383827d70a031e960db8c0b83a42a79d518535d742f3257715649d` passes all2115 original full-scene/physical ownership cases with zero different images. Source128/C6 ABI, heap/SP/IFF/slot/clock,29-cycle VRAM spacing,VBlank, full sprite rectangles, every published six-byte key against real PGT/CGT, CPU/physical NAME and active referenced bytes remain guarded. Controlled preparation peaks592187 cycles. Graphics receipt SHA-256 `59f4adc1210e3398c3ab216eb7b6aaaa343583d2a58112ec48230695d6c07412`.
- The SAME current ROM passes all12 immutable input-only CPU routes:24820 whole CPU/all128RAM checkpoints, zero canonical injections and maximum27047 native-step cycles. This RPC executes native audio side effects but does not validate graphics, PSG histories or frame cadence.
- Actual integrated source-audio proof on that ROM passes2115 controlled post-visible intervals: ALL3499 ordered raw original writes and2472 expected physical PSG writes, plus whole CPU/all128RAM after-states. The single excluded source interval is an explicitly impossible graphics-only player2 fixture with ZERO audio writes. Independent host source auditing still covers all2116 intervals. The trace separates legitimate real joystick-sampler14/15 access from audio-owned0..3,6..10, checks GPIO7upper and unowned latches/heap/VRAM/ABI. Audio receipt SHA-256 `62b83c4e9eb7d34d3b3226a10700864c47004aa158579b66f5d132a1c69a7c67`. Extra-event negative fails exact stream comparison.
- Native PSG components pass31252 synthetic callbacks/11776 physical writes, all16 controls×32 frequencies, all raw register bytes and four strict GPIO-direction states; maximum1176 callback cycles including RPC. Clear-loop observers preserve both TIA mirror passes BEFORE canonical RAM clearing:256 independent original6502 entries and512 actual Z80 emitter/fullwrapper cases pass; a deliberately late emitter fails the source-epoch witness. Default source generation remains byte-identical. [Audio evidence/adaptations](https://github.com/sandersouza/msxgp-frostbite/blob/codex/feat/14-hud-psg-attract/docs/presentation-audio.md).
- Timing still FAILS. The fresh120-frame combined keyboard/model-pixel probe reaches567804 busy cycles against59736 NTSC:22 overruns and47 skipped VDP frames. Source/scheduler maximum23813 cycles. Fixed-owner name expansion saves3888 cycles in the last world stage (141042→137154), retaining every table byte and complete strip. Its40967 actual operations include2048 optimized cases under3000-cycle microbudget (max2749); generic cases remain separately bounded. The4096-byte ROM table uses existing bank255 space, leaving768 bytes before the unchanged6400-byte contact shadow. [Floe architecture/proof boundaries](https://github.com/sandersouza/msxgp-frostbite/blob/codex/feat/14-hud-psg-attract/docs/presentation-floe-templates.md).
- Retained component checks include player variants883, large-eight-pattern fallback,13024 shoreline-stream cases,6727 dirty-span cases,78 owned footer/1212 resolver cases,3295 packed-header/4718 typed-span cases,1265 complete NAME bursts and raw/template publication matrices. Historical component results remain separate from current combined timing. [Player](https://github.com/sandersouza/msxgp-frostbite/blob/codex/feat/14-hud-psg-attract/docs/presentation-player-cache.md), [dirty spans](https://github.com/sandersouza/msxgp-frostbite/blob/codex/feat/14-hud-psg-attract/docs/presentation-dirty-spans.md), [HUD/NAME](https://github.com/sandersouza/msxgp-frostbite/blob/codex/feat/14-hud-psg-attract/docs/presentation-hud-publication.md).
- Fresh default presentation control remains byte-identical `0b98f3cb89e99f6e79ad9f1a3fb237c2cbfadebcd5759025a123ce33e09fcf78`. Whole489 original-free host tests, diff checks and staged public-source policy pass. Pinned Stella source receipt remains `874e8e309afa19ff0ba3bbf34532e3a8ed14887b7a53184d69410a5bd0ed0247`; no original/source data or legacy evidence changed.
- Remaining work: reduce complete renderer/header/player MISS costs; meet NTSC/PAL hard deadlines in every view; verify both PAL logical updates' audio and complete combined natural-route matrices; record visual/listening evidence separately; then one final review, clean-main rebuild and immutable prerelease. No runtime Atari interpreter, prerecorded route/frame playback, replacement mechanics or extra hardware.

Private timing-failed candidates remain research artifacts. No new human-testable ROM has qualified or been offered. The published [v0.0.6-progression](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.6-progression) remains unchanged. Manual listening and physical hardware are not accepted by these automated checks.

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
