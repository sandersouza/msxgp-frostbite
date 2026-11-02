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

- Tasks 1/2 are complete; Task 3 remains in progress. Checkpoint [93afb2e](https://github.com/sandersouza/msxgp-frostbite/commit/93afb2e) integrates exact six-byte tile constructors, metadata-only live cache ownership, per-generation dirty rows and retained player/door/logo sprite templates into the private FAST profile. The default profile remains byte-identical to its previous control ROM.
- Actual native graphics match every mapped original pixel in all 2115 ordered observations: 1690 controlled fixtures, 31 cold-route frames and 394 input-only window frames. Source128 RAM/C6 ABI, heap/redzone/SP/IFF/slot, standard 3.579545MHz/64KiB, 29-cycle VRAM writes, unchanged visible preparation, VBlank commit and at most four FULL sprite rectangles/line pass. Independent audits also verify the complete normalized scene/dirty flags, both CPU-name reference histograms and both physical VRAM name pages. This is injected graphics proof, not natural MSX gameplay or frame acceptance.
- Private candidate SHA-256 `8711e904a4e8d3af5c0be70c898469c142a26f142b64e18e47061e5cc4abc7e3`; all-source receipt SHA-256 `c6b89d01a00fd371536f6d6cff103439378476e70a29858a4aeb90924ca6aa08`. A measured unchanged-image preparation improves from 54216 to 17910 cycles. Cold and changed-state preparations still reach 1217662 cycles: complete-frame deadlines are NOT accepted. No new human ROM is qualified.
- The independent actual-Z80 component proofs cover all 10112 geometry cases, 4705 whole typed tile/error cases, 1382 cache operations including forced CRC collisions and all reference/bucket/bitmap invariants, and 4679 normalized dirty-state/error cases. The last set includes 2115 original observations plus explicit diagnostic/arithmetic boundaries; those synthetic cases are not new original raster evidence. Whole-suite checkpoint: 398 original-free tests pass; staged public-source policy passes.
- Pinned Stella7 captures full 160×210 rasters, F019/F476/F019 CPU/all128 RAM and every ordered TIA audio write. Independent repeats, input/restore journals, complete checkpoints/capsules and raw artifact hashes pass. Source receipt producer5e82791; SHA-256 `874e8e309afa19ff0ba3bbf34532e3a8ed14887b7a53184d69410a5bd0ed0247`. [Compact source receipt](https://github.com/sandersouza/msxgp-frostbite/blob/codex/feat/14-hud-psg-attract/references/presentation-source-result.json). Windows can overlap and are not a whole-game verdict.
- All 128 even Atari RGB codes were measured twice; the original 34 calibrated codes remain identical. Stella7 is render authority. Four old-ALE controlled left-edge bear disagreements and right-edge263-line frames remain documented. No physical Atari verdict or natural reachability of injected extremes is inferred.
- No runtime Atari interpreter, prerecorded route/frame playback, replacement mechanics or extra hardware is used. Remaining work: profile and optimize the actual continuous native pipeline, meet NTSC/PAL deadlines in all four views, implement ordered built-in PSG output preserving both controller GPIO ports and both PAL logical steps, then combined natural-route acceptance, final review, clean-main rebuild and immutable prerelease.

The renderer/PSG integration and combined target acceptance are still pending.
Private incomplete candidates exist, but no new human-testable ROM has qualified or been offered. The published
[v0.0.6-progression](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.6-progression)
remains unchanged. Historical/offline success is not live Frostbite proof.

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
