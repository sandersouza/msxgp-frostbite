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

- Tasks1/2 are complete; Task3 remains in progress. Actual native graphics now match EVERY mapped original pixel in all2115 ordered observations:1690 controlled fixtures,31 cold-route frames and394 input-only window frames. Source128RAM/C6ABI, heap/redzone/SP/IFF/slot, standard3.579545MHz/64KiB,29-cycle VRAM writes, unchanged visible preparation, VBlank commit and at most4 FULL sprite rectangles/line pass. This is injected graphics proof, not natural MSX gameplay or frame acceptance.
- Checkpoint [a114bb9](https://github.com/sandersouza/msxgp-frostbite/commit/a114bb9) reduces the first measured P0 sprite component from79021 to48128cycles without losing pixels. Private candidate SHA-256 `b4170a6b86fe035bddd8fa9f4f785de2cba99e2c8a901a765644a9ef15647cbe`; all2115 native receipt SHA-256 `0ff47fa954189bbb252ba503faf7f7c6e619e7aaa1ad49d16d81becd4240c2d5`. Complete preparation still reaches2425014cycles: frame deadlines FAIL. No new human ROM is qualified.
- Sparse exact six-byte typed tile constructors reproduce all2115 source images in the host, using at most45/26/32 of64 slots per bank. Host receipt SHA-256 `6fe9c841c2b23f6d25827bb5666fe6d44e6e5ff50dca8538ad23bc02615454ae`. The independent actual-Z80 constructor microproof at checkpoint [3a5d05e](https://github.com/sandersouza/msxgp-frostbite/commit/3a5d05e) passes4705 whole-tile/error cases, including2302 observed unique keys plus explicit algebra boundaries and invalid bank/type rejection. Maximum4663cycles including RPC. These constructors are not integrated into the game yet.
- The metadata-only exact-six-byte cache microproof passes1382 operations, deliberate32-key CRC collisions, full reference counts/bucket graphs/free bitmap and guards. Canonical producer9283a8b; receipt SHA-256 `39380704f3bc42fe6a110b9a1a506ab222246ee55395d0e3e5b37eb555058eeb`. The allocator remains separate from the production full-tile cache; integration and actual frame measurements are pending.
- All10112 finite row/floe/bear geometry cases pass actual-Z80 full descriptor/ID/pattern comparison. Canonical producer687b224; receipt SHA-256 `368636c14ad5dff752a028c2e86bebfb2bf1bbbccb1fd665e44a315242d1f72a`. Current host suite:381 original-free tests pass; staged public-source policy passes.
- Pinned Stella7 captures full160×210 rasters, F019/F476/F019 CPU/all128RAM and every ordered TIA audio write. Independent repeats, input/restore journals, complete checkpoints/capsules and raw artifact hashes pass. Source receipt producer5e82791; SHA-256 `874e8e309afa19ff0ba3bbf34532e3a8ed14887b7a53184d69410a5bd0ed0247`. [Compact source receipt](https://github.com/sandersouza/msxgp-frostbite/blob/codex/feat/14-hud-psg-attract/references/presentation-source-result.json). Windows can overlap and are not a whole-game verdict.
- All128 even Atari RGB codes were measured twice with unchanged indexed/RGB/state evidence; the original34 calibrated codes remain identical. Stella7 is render authority. Four old-ALE controlled left-edge bear disagreements and right-edge263-line frames remain documented; no physical Atari verdict or natural reachability of injected extremes is inferred.
- No runtime Atari interpreter, prerecorded route/frame playback, replacement mechanics or extra hardware is used. Remaining work: integrate sparse dirty rendering/cache/template reuse, meet paced NTSC/PAL deadlines in all four views, implement ordered built-in PSG output preserving both controller GPIO ports and both PAL logical steps, then combined natural-route acceptance, final review, clean-main rebuild and immutable prerelease.

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
