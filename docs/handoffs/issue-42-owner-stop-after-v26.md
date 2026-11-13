# Issue42 — owner-requested stop after v0.0.26

The owner explicitly requested stopping after this round/release on2026-11-12.
Stop implementation, experiments and successor starts. Resume only when the
owner asks. This overrides earlier autonomous-continuation instructions.
Same root writer, Issue42 chat and `codex/feat/42-native-renderer`; no transfer,
merge, issue close or new ROM release. PR43 stays draft/stacked on41. Project7
returns to In review for the delivered v26 and pending owner feedback.

## Delivered control

v0.0.26-native-bands-diagnostic is published, six downloaded assets/API digests,
source tag, immutable documentation, unchanged v25 rollback and desktop WebMSX
launch verified independently. See references/native-bands-result.json,
references/native-bands-delivery.json and issue-42-v26-delivery.md.
Runtimeeaa441806da4bb8fa4bfff2b0a6e73b3976286fe,214 source files;
ROM7765bb9e1485a237c49abe0a95c621bea918b61989aae1fc4ad97b1d8b031c84.
Workbookb1c757747b5bd84b53d19ec2db675c8460cb0082b145cf308b91e55714982605.
Six AO evidence roots are now sealed by outputs/presentation/native-bands-ao-seals.json;
with61 earlier controls there are67 immutable roots. The independent final-review
manifest omits its nested downloaded SHA256SUMS, which the aggregate separately
binds under supplemental_files; verify those supplemental hashes too. Never
write into any of these controls. All reviewers and local task processes stopped.

NTSC regular31.59→31.83FPS; bear28.12→29.83. PALregular29.66→30.46;
bear24.69→25.08. Bear NTSC foreground70670→62257cycles (-11.90%), P95 gap
50.06→33.38ms, one50.06ms active gap remains. Regular longestNTSC66.75ms still
prevents uniform30FPS. Grounded landing snapshots20→22/26 NTSC and14→17/26 PAL;
no earlier grounded/endpoint flag lost. Source mechanics/input/PSG exact.
All-level30, original fluidity and owner/mobile/listening/hardware acceptance open.

## Preserved AP work, not published

Owned pending files: scripts/build_cache_default.py and
docs/superpowers/plans/2026-11-12-cache-default.md. Keep them intact. The ignored
AP roots cache-default-ap-research and cache-default-ap-review are paused WIP,
not part of the sealed v26 release and not human-test delivery.

Internal build01 ROM90d07dc661002f93fbaa7a8e93bcb3e74182abdbcb4838f19406d362d0111512,
215 dirty source fingerprints at docs HEAD454ad9a. Exactly one caller byte changes:
bank2/B0A6 9C→A0 skips a second default selection. The original public lookup is
untouched, with exact v26 rollback. The intervening inherited-L eligibility call
preserves the selected way/pointer/patternbase. Native trace RED observed two
defaults, GREEN observes one per lookup, with all5 passive buffers matched to
the corresponding natural run. Independent AP review
bf7ce619ed4bc516b42a56674ea6051e4968bbacfad0e24c120f3f531614ef87 covers82908
finite calls and14IRQs, complete P0/raster/source/ABI equivalence and a rejected
deliberate post-RETI corruption. All AP review writers stopped.

Whole bear NTSC remains29.830536FPS, essentially unchanged from v26; foreground
mean62257→61871cycles is a local gain, not a demonstrated cadence win.256matrix
scenes pass. Four complete routes/clean binding/CI/workbook/newrelease have NOT
been qualified for AP. Do not publish or describe it as v27 merely because its
native contract passes. Preserve this control if additional work is later resumed.

## New owner requests, pending resume

1. Remove the black left stripe and enlarge the visible playfield, fixing the
   edge alignment and object entry/exit rather than extending a full-height bar.
   The owner explicitly rejected the full-height-bar choice. No full-height
   stripe code was implemented. The v26 lower-only closure remains insufficient
   for the owner's preferred presentation; do not claim the new request is done.
2. Add the exact footer credit `Activision - Retroworks` beside the existing logo.
   This is not in v26 and has not yet been implemented.
3. Continue the earlier performance/fluency work together with these additions
   when the owner resumes. Preserve source mechanics/controls/colors, current
   rollback versions and whole-frame/landing evidence; release every qualified
   human-test ROM with exact bytes, hashes, workbook, WebMSX and concrete tests.

The owner's screenshot is preserved locally in the ignored AP research root as
owner-left-edge-v26.png. The task is stopped by explicit request, not cancelled.
