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

## Latest diagnostic and owner feedback

[v0.0.8-ice-contrast-preview](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.8-ice-contrast-preview) is published with the exact ROM/build.json/validation.json/SHA256SUMS; allfour fresh downloads are byte-identical to the seal. Source `2cffac7de2f726c1c380914ad5d04372e431fd75`; ROM4194304B,ASCII16,SHA-256 `141044d3c1d4db7544a2f1357bef90e7cc251b85de7cdd41e3378b4776adb88a`. Source remains unmerged; issue14/project7 remain In progress.

The owner reports0.0.7 feels about half original speed and graphics otherwise appear correct, except landed ice disappears into the same blue as the sea. The screenshot is local-only; machine/VDP/emulator, listening and physical-hardware acceptance were not supplied. Treat that speed estimate as subjective feedback.

- Root cause: original floe0C→98 and fixed sea90 both mapped to TMS4. The old expected-image mapper shared this policy, so zero mapped-image differences did not detect lost gameplay contrast. Preserve sea4 versus nearest other blue5 for98 when their blue RGB choices collide; grayscale input is unchanged. This changes presentation only, not canonical state, collision/scoring/audio logic or game cadence.
- Independent regression: the old published capture fails fixed sea4/ice5 expectations. A natural original landed-floe witness is case1721/source(46,148), row1/latch98, old target4. The NEW ROM passes all2115 complete source-backed images/physical ownership cases and independently checks164511 source98/31412979 source90 pixels against physical VDP data. Counts98 include other original uses of that color; natural landed-floe scanline coverage includes128569 source98 pixels. Controlled preparation peaks599614 cycles.
- The same exact ROM passes24820 full CPU/all128RAM checkpoints across all12 original input-only routes, zero canonical injections/max27047 native cycles; all3499 ordered original audio writes and2472 physical PSG writes also pass. One impossible graphics-only player2 fixture has zero audio writes and is explicitly accounted for. An extra-event negative fails exact event ordering on this ROM.
- Original-speed gameplay remains UNFINISHED. The standard600-frame keyboard probes reach537515 busy cycles: NTSC59736 budget/252 overruns/580 skipped VDP frames/259 visible commits; PAL71364/300/584/203. Those scripted inputs stay on white ice and are not blue-floe performance coverage.
- Additional PRIVATE original-input-only continuous research reaches430 NTSC/390 PAL blue-floe frames in600 outputs, matching every one of601/717 original CPU/all128RAM prefix checkpoints, with no state injection. It measures37.91/39.20 source updates per second (~63%/65% original in that sequence). This is not a universal speed ratio, an improvement claim, completed game or all-view qualification. Both PAL logical updates remain ordered. The actual native decoded frame202 shows three blue rows above a white bottom row; physical/owner acceptance still needs fresh feedback.
- 497 original-free host tests/source policy and [exact-source CI41634782194](https://github.com/sandersouza/msxgp-frostbite/actions/runs/41634782194) pass. The seal now requires independent semantic contrast bound to the same ROM/matrix/capture, not only shared mapped-image agreement. Standard-speed MSX1/64KiB/16KiB/TMS9918/built-in PSG and4MiB ASCII16 remain unchanged. No source/quality/actor/VRAM-data reduction was used.
- The0.0.7 public ROM is freshly downloaded and unchanged at `d3017f7cb01c71d50639fd4aac67cd3b12611fb9508c59f30cfe2a1b873752c9`; the fresh0.0.6 source regression control remains `1223931972bd7e0ec02a8c66805cb30ac0defaad1abd71dd67c9c8a7746be5f6`. Earlier release assets, original captures and preserved legacy are unchanged.

[New human tests](https://github.com/sandersouza/msxgp-frostbite/blob/codex/feat/14-hud-psg-attract/docs/releases/v0.0.8-ice-contrast-preview.md), [root cause/evidence](https://github.com/sandersouza/msxgp-frostbite/blob/codex/feat/14-hud-psg-attract/docs/presentation-ice-contrast.md), [public validation](https://github.com/sandersouza/msxgp-frostbite/blob/codex/feat/14-hud-psg-attract/references/presentation-ice-contrast-result.json) and [publication receipt](https://github.com/sandersouza/msxgp-frostbite/blob/codex/feat/14-hud-psg-attract/references/presentation-ice-contrast-delivery.json) retain limits and artifact identities. Test landing on several rows: they should stay light blue against dark water; report screenshots/video and setup. Do not use this preview to approve authentic rhythm/difficulty/collision timing.

Tasks1/2 complete; Tasks3/4 remain open. Continue world/floe/header/igloo/player performance work at full visibility, qualify all combined original-route/view/NTSC/PAL/controller/PSG paths, then Task5 acceptance and the single final Task6 independent review/main integration. Only then close14/Done and fork15. No runtime Atari interpreter or prerecorded route/frame playback is used; research replays controller inputs only and compares source state. Cleanup of preserved Seaquest material remains issue17.

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
