# Issue14 presentation/audio preview checkpoint

Current continuation2026-11-03: [0.0.9 performance preview](releases/v0.0.9-performance-preview.md)
is published and all four downloads match the exact tested source/ROM.
[Current evidence/ownership/next work](presentation-performance.md) supersedes the
earlier measurements below. The measured gain is only 2–3% in the bounded blue-ice
sequence; original cadence, full combined acceptance and main integration remain
unfinished. Issue14 keeps exclusive checkout ownership and In progress status.

Update2026-11-03: owner feedback exposed landed-ice/sea color collapse. The
separately tagged [0.0.8 contrast correction](releases/v0.0.8-ice-contrast-preview.md)
is published and its four downloads verified; see
[root cause/current evidence](presentation-ice-contrast.md). The0.0.7 checkpoint
below is preserved historically. Issue14 still owns this checkout; no transfer
or main integration occurred, and original-speed gameplay remains unfinished.

Issue: https://github.com/sandersouza/msxgp-frostbite/issues/14

This is a continuing-work checkpoint, not an issue or checkout-ownership handoff.
The dedicated `Frostbite — ISSUE #14` chat retains sole ownership of the shared
checkout and branch `codex/feat/14-hud-psg-attract`. Do not start issue15 or transfer
the checkout while14 remains unfinished. Project7 status remains In progress.

## Published limited diagnostic

- [v0.0.7-presentation-preview](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.7-presentation-preview), prerelease.
- Exact tested/tagged source: e12adf478a9cd713280c6edafe819e78b8de5537; unmerged.
- ROM: frostbite-0.0.7-presentation-preview.rom,4194304 bytes,ASCII16.
- SHA-256: d3017f7cb01c71d50639fd4aac67cd3b12611fb9508c59f30cfe2a1b873752c9.
- [Human instructions and known limitations](releases/v0.0.7-presentation-preview.md).
- [Byte-identical public validation](../references/presentation-preview-result.json)
  and [verified publication/assets/CI](../references/presentation-preview-delivery.json).

The owner requires every useful human-testable diagnostic to have a release;
the project workflow explicitly says not to wait for the final game. This
standalone preview is qualified only for appearance, sound and input feedback.
It does not meet the original cadence, close14, waive hard game gates or qualify
full combined natural play. runtime_qualified/frame_deadline_accepted remainfalse.
No source steps, actors, visibility, graphics quality or required VRAM data were
removed to obtain a faster measurement. Failed research candidates remain private.
The one final whole-branch review remains pending before final integration.

## Current evidence

- Clean canonical build: outputs/presentation/preview-canonical-a. No cached
  contact substitution; source/evidence identities rechecked before sealing.
- Whole-source matrix: outputs/presentation/preview-matrix-a/check.json,
  2115 images/physical ownership cases,zero differences,579001 maximum controlled
  preparation cycles. Controlled phase/state injection, not natural-game proof.
- Audio: outputs/presentation/preview-audio-a/check.json,2115 post-visible
  intervals,3499 ordered raw writes,2472 physical PSG writes, whole CPU/all128RAM.
  One graphics-only impossible-player2 fixture has zero audio writes and is
  explicitly excluded; the original host audit retains all2116 intervals.
- Fresh twelve input-only native routes: outputs/presentation/preview-native-a,
  24820 full CPU/all128RAM checkpoints,zero canonical injections,max27047 cycles.
- Real keyboard/scheduler probes: outputs/presentation/preview-pace-ntsc-a and
  preview-pace-pal-a,120 frames each. Both peak537515 busy cycles. NTSC22 overruns,
  48 skipped VDP frames,20 visible commits; PAL27 overruns,51 skips,13 visible
  commits. Cadence and tear-free gameplay FAIL; retain every failure in public notes.
- Extra-event negative on the exact ROM: preview-audio-event-negative-a fails
  exact ordered-source-stream comparison. Negative logs are never positive proof.
- Independent synthetic header batch: header-batch-preview-current-a,17340
  actual Z80 cases/max3954 including mask construction and tile/RPC. Full493
  original-free tests/source policy and exact-source GitHub CI41564113818 pass.
- Fresh default control remains0b98f3cb89e99f6e79ad9f1a3fb237c2cbfadebcd5759025a123ce33e09fcf78.
  Fresh progression source control, using only independently verified freshly
  generated contact tables, and fresh public v0.0.6 download both remain
  1223931972bd7e0ec02a8c66805cb30ac0defaad1abd71dd67c9c8a7746be5f6.
- Standalone preview seal: outputs/presentation/preview-seal-a/seal.json.
  The sealer rechecks raw complete images/native checkpoints/timing, producer
  and artifact identities, fatal-positive logs, exact ROM and diagnostic-only
  scope. Only ROM/build.json/validation.json/SHA256SUMS are public. Fresh downloads
  of allfour compare byte for byte with the seal. Original raw data stays ignored.

## Next actions and ownership

Continue issue14's renderer/native performance work, then prove original cadence
and exact combined source state/pixels/PSG on all routes, views and NTSC/PAL,
including both PAL updates and both physical controller paths. The current
dominant costs are world/floe/object publication, cold header/igloo and player
misses. Keep source-ROM mechanics and all hardware/quality gates binding.
Human visual/listening/physical feedback is pending; never infer it from a boot
or these automated captures. After final acceptance, perform the single final
review, integration/rebuild, a new immutable version and then the dedicated15 fork.
The preserved Seaquest copy and external snapshot remain untouched; cleanup17 only.
