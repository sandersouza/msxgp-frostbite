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

## Published limited diagnostic, not issue acceptance

[v0.0.7-presentation-preview](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.7-presentation-preview) is published as a prerelease, with the exact ROM plus build.json/validation.json/SHA256SUMS. Allfour fresh downloads compare byte for byte with the seal. This is a **visual/audio/input preview with severe slowdown and possible tearing**, not real-time game acceptance. Issue14 and project7 remain In progress; the tested feature source is unmerged. The owner explicitly requires useful diagnostic releases before the final game.

- Exact tested/tagged source: `e12adf478a9cd713280c6edafe819e78b8de5537`. ROM4194304 bytes,ASCII16,SHA-256 `d3017f7cb01c71d50639fd4aac67cd3b12611fb9508c59f30cfe2a1b873752c9`. Standard-speed MSX1/64KiB/16KiB/TMS9918/built-in PSG; no hardware expansion or quality/source-step/VRAM-data reduction.
- All2115 controlled original full-scene/physical ownership cases pass with zero different images. Source128/C6 ABI, heap/SP/IFF/slot/clock,29-cycle VRAM spacing, controlled VBlank, full sprite rectangles, exact published keys/PGT/CGT, physical/CPU NAME and active referenced bytes remain guarded. Controlled preparation peaks579001 cycles. This is separate from natural game cadence.
- The SAME current ROM passes all12 immutable input-only CPU routes:24820 whole CPU/all128RAM checkpoints,zero canonical injections and maximum27047 native-step cycles. This RPC executes native audio side effects but does not validate paced graphics/PSG histories.
- Integrated audio on that ROM passes2115 controlled post-visible intervals: ALL3499 ordered raw original writes and2472 expected physical PSG writes,plus whole CPU/all128RAM. One impossible graphics-only player2 fixture has ZERO audio writes and is explicitly excluded; source host auditing retains all2116 intervals. Raw I/O distinguishes legitimate joystick14/15 sampler access from audio-owned0..3,6..10, and checks GPIO7upper/unowned latches and ABI/heap/VRAM. An intentional extra-event negative on this exact ROM fails the ordered-stream check.
- Timing FAILS in both120-frame real-input probes. NTSC:537515 peak busy cycles/59736 budget,22 overruns,48 skipped VDP frames,20 visible commits. PAL:537515/71364,27 overruns,51 skips,13 visible commits. runtime_qualified/frame_deadline_accepted remainfalse. Static appearance/sound presence/input feedback is useful now; do not judge original rhythm,difficulty or collision timing from this preview.
- New optimizations retain complete output: ordered source hooks and pre-clear audio events;4096-byte fixed-owner NAME lookup in existing bank255 space;160-byte per-column upper/lower font-mask batch reused by all three bands. Actual component checks include31252 PSG calls/11776 writes/four strict GPIO states,256 independent6502 clear entries+512 actual emitter/wrapper cases,40967 complete NAME expansions (2048 optimized cases/max2749<3000 microbudget), and17340 independent synthetic full font-mask/tile cases. Source epoch, same-value events and both TIA mirror passes are retained. The header stage improves170027→139007 and complete peak567804→537515; both still fail real-time qualification.
- 493 original-free host tests, source policy and [exact-source CI41564113818](https://github.com/sandersouza/msxgp-frostbite/actions/runs/41564113818) pass. Fresh default control stays `0b98f3cb89e99f6e79ad9f1a3fb237c2cbfadebcd5759025a123ce33e09fcf78`; freshly recompiled progression control with verified rebuilt contacts and fresh public v0.0.6 download both retain `1223931972bd7e0ec02a8c66805cb30ac0defaad1abd71dd67c9c8a7746be5f6`. Existing public binaries and original/legacy evidence are unchanged.

[Human tests/limitations](https://github.com/sandersouza/msxgp-frostbite/blob/codex/feat/14-hud-psg-attract/docs/releases/v0.0.7-presentation-preview.md), [public validation](https://github.com/sandersouza/msxgp-frostbite/blob/codex/feat/14-hud-psg-attract/references/presentation-preview-result.json), [publication receipt](https://github.com/sandersouza/msxgp-frostbite/blob/codex/feat/14-hud-psg-attract/references/presentation-preview-delivery.json) and [continuing-work checkpoint/sole-owner state](https://github.com/sandersouza/msxgp-frostbite/blob/codex/feat/14-hud-psg-attract/docs/presentation-preview-checkpoint.md) identify evidence and next actions. No manual listening/emulator or physical-hardware acceptance is inferred.

Tasks1/2 complete; Tasks3/4 remain open. Continue renderer/world/header/igloo/player MISS optimizations to meet NTSC/PAL deadlines with unchanged source mechanics/quality; qualify both PAL audio updates and full combined natural-route/view/controller coverage. Task5 full acceptance and the one final Task6 whole-branch review/main integration remain pending. Only then close14/Done and fork15. No runtime Atari interpreter or prerecorded route/frame playback is used. Cleanup of preserved Seaquest material remains issue17.

## Owner feedback and contrast regression —2026-11-03

The owner reports v0.0.7 feels about half original speed. Graphics otherwise
appear correct, except landed ice becomes the same blue as the sea. A screenshot
is preserved locally; machine/VDP/emulator and listening/physical verdicts were
not supplied. Keep this subjective feedback separate from measured timing.

Root cause confirmed: original source floes change0C→98 while the sea stays90,
but independent nearest-RGB choices map both to TMS blue4. The mapped-image
oracle shared that policy and therefore missed loss of gameplay contrast.
The fix preserves sea4 versus light-blue ice5 without changing source RAM,
collisions or game cadence. A new independent physical-VDP/source-color check
rejects the published capture at case6/source(65,88), expected5/actual4.
497 host tests pass, including the new contrast and grayscale regressions.
Fresh full-target/CPU/audio/NTSC/PAL checks and a NEW immutable0.0.8 diagnostic
are being prepared. More floes now remain visible, so remeasure their full cost;
the real-time performance issue is still open. [Root cause and proof boundaries](https://github.com/sandersouza/msxgp-frostbite/blob/codex/feat/14-hud-psg-attract/docs/presentation-ice-contrast.md).

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
