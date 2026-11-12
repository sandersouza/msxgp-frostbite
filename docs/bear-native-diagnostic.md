# Native bear composition diagnostic AI

v21 preserves v20 artwork, colors, source simulation, contacts, input and PSG.
It replaces repeated bear tile construction with exact prepared tiles and
certified row transfers. The earlier rejected bear-sprite experiment is not
promoted. No character recoloring or P0 cache-layout change is included.

Runtime source: `851aa41466d7b9ea86c753a5228337c688d40a88`.
ROM SHA256: `635876dcf352bfc2eafee908757045c7387a11653c21f4dce266fd765dd5ad15`.
4 MiB ASCII16; standard-speed MSX1, 64 KiB RAM, 16 KiB VRAM, TMS9918 and PSG.

## Representation and safety

512 descriptor variants share 96 geometry records, 470 logical patterns,
2,860 exact 16-byte pattern/color tiles and 210 deduplicated 64-byte row strips.
Nine certified background/clip/color contexts use prepared tiles. Other contexts
retain the original per-cell constructor. Interior white-bear day/night rows
can use bulk transfers after validating the original background fill invariant.
All dirty-row contexts are checked before writes. Logical-zero or fully clipped
cells preserve the original skip behavior.

Directory bank66, records67..78, tiles79..101, cell body102, strips103..111 and
bulk body112 occupy retired B800..BFFF packet tails. Lower14KiB contact payloads
are unchanged. Mapper-safe helpers occupy142 additional bytes of existing
reserved E900..F000 kernel space (1,587 to1,729 of1,792 bytes). No new RAM region,
VRAM allocation, additional hardware or clock acceleration is required.

Only inactive roles whose old references were retired by the certified complete
background fill are reused. Pattern/color transfers precede metadata and NAME
publication. Unused roles become FF; active-page references remain protected.
Scratch uses proven-dead staging fields, not persistent owner tuples. Later
actors invalidate/reload geometry. IRQ restoration retains the existing ABI.

All170 v20 bound sources are unchanged; four additive files bring the closure
to174. `scripts/build_bear_native.py --mode original` reproduces exact v20 ROM
`c036c3d960da3be4331df6afbb168bc5037777d47be9f4892a16ff6f5d4e43ac`.
Backup tag: `codex/backup/42-before-bear-native-20261112`.
32 predecessor evidence roots were reverified unchanged. Private A/B and two P0
cache-layout variants are retained locally. D was rejected without measurement
because its three-slot ways cannot hold an existing four-sprite pose; measured E
showed no useful whole-route gain. Both were reverted before qualifying C.

## Whole-route measurements

| Active route / cost | v20 | v21 |
|---|---:|---:|
| Bear NTSC complete pictures/s |15.0453|24.1245 (+60.35%)|
| Bear PAL complete pictures/s |15.3333|22.8702 (+49.15%)|
| Bear NTSC foreground mean, cycles |138,852|81,308|
| Bear PAL foreground mean, cycles |134,078|82,702|
| Bear NTSC picture gap P95 / maximum, ms |83.44 /83.47|50.10 /66.75|
| Bear PAL picture gap P95 / maximum, ms |79.75 /79.78|59.81 /59.84|
| Regular NTSC pictures/s |30.4355|30.4355|
| Regular PAL pictures/s |28.0505|28.2288|
| Regular grounded landings /26 NTSC |20|21|
| Regular grounded landings /26 PAL |14|13|
| Regular endpoint Y /26 NTSC |23|23|
| Regular endpoint Y /26 PAL |24|23|

The bear measurement uses the unchanged clean-start620-step prefix, active
source195..425 at level4,122 bear X positions and all eight poses. The existing
one-player guard prevents broader coverage beyond630; no all-level claim.
Regular level0 NTSC mean remains30.44, with50.07ms P95/83.44ms maximum gaps.
NTSC gains grounded arc3; PAL loses grounded arc15 and endpoint arc24. Mechanics
remain exact while brief visual states can still be missed. Stage picture
populations differ; inclusive bear cost is already inside WORLD, not additive.
**Stable30FPS across gameplay and original fluidity remain open.**

## Verification and remaining work

586 host tests;2,115 original-source/2,040 density/54 header scenes;
2,115 ordered-audio intervals pass. All four clean final routes reproduce five
measured buffers each. Original CPU/allRAM, exact v20 pixels/owners and active
page checks pass.18 generic plus14 new real hardware IRQ boundaries pass; the
negative AF2 control is rejected. Exact runtime-source push/PR CI passes.

Independent review rebuilds exact C and rollback, then compares38,144 actual
Z80 calls per ROM, all512 variants/pages/phases/coarse offsets/nine contexts,
all dirty subsets, wrap/clipping, cold/cache and mixed-material fallback.
310,224 live keys agree; unused retired-role differences are separately
classified, not hidden.10,044 prepared context cells and385,024 contact fields
agree. Protected static/active-page data, source RAM, ABI, stack and mapper
restoration pass. Initial invalid review fixtures and incomplete IRQ coverage
attempts are preserved separately from corrected positive evidence.

The35-tab AI workbook preserves all34 AH tabs/782,639 cells and native features.
Saved-file/raw-route audit, zero formula errors, two mutation/restore checks and
five rendered regions pass. Native Excel was not exercised. Automated checks,
browser launch, owner perception, manual listening and physical hardware are
separate evidence classes; the latter acceptance remains pending.

Next investigate remaining dirty-state bookkeeping and source/renderer overhead
using whole-route results. No player-only updates that desynchronize the scene.
Issue42/39/15/16 remain open and PR43 draft; same focused chat/root sole writer.
Read `references/bear-native-result.json` and the v21 human-test release notes.
