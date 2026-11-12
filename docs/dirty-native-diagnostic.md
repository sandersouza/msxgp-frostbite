# Specialized dirty traversal diagnostic AJ

v22 keeps exact v21 graphics, palette, source mechanics/input/PSG and both
presentation histories. It specializes comparisons and unrolls four-object/
four-floe traversal; capture still runs unchanged in bank2. The goal remains
stable29.97/30NTSC across gameplay, not only a high average.

Source: `80b5a435a28f9009812a73aecfddaf679c690b49`.
ROM: `b0a3d2befe9c370bbec9ba9096df63143a5743949b1deeeeea63879fa843c1e2`.
4MiB ASCII16, standard-speed MSX1/64KiB RAM/16KiB VRAM/TMS9918/built-in PSG.

## Architecture and rollback

A16-byte bridge occupies EFC1..EFD0 within the existing reserved E900..F000
kernel (1,729 to1,745 of1,792 bytes occupied). It calls original capture before
mapping bank113; the898-byte body occupies its retired B800 tail, returning
through resident RAM to bank2. Lower14KiB contact data is unchanged. No extra
RAM region, VRAM allocation, hardware or new visual compromise.

Comparisons use absolute current-state/indexed history fields and constant
addresses. Four-lane traversal avoids repeated offset arithmetic. Effective
v21 floe spans are derived from the actual ROM table: both coarse tables must
agree, and each lane must have one nonzero byte. The exact64-byte history copy
uses unrolled LDI. Dirty union/full/blank/gradient/header/igloo/bear/actor gate/
footer rules, both histories, row/delta outputs and mapper restoration remain.
Return A becomes2 (mapper restore); the caller overwrites it before use.

The first prototype incorrectly used pre-grid24 spans from historical source.
Root dirty/pixel guards and independent review rejected it. Corrected code derives
actual v21 spans and has RED→GREEN guard tests. All failed and invalidated
producer attempts remain separate evidence. No rejected ROM is published.

174parent source files and37sealed predecessor roots remain unchanged; four
additive files give178bound sources. `scripts/build_dirty_native.py --mode
original` reproduces exact v21 SHA635876dc...ad15. Backup tag:
`codex/backup/42-before-dirty-native-20261112`.

## Whole-route results versus v21

| Active route / cost | v21 | v22 |
|---|---:|---:|
| Regular NTSC pictures/s |30.4355|31.2970 (+2.83%)|
| Regular PAL pictures/s |28.2288|29.4768 (+4.42%)|
| Bear NTSC pictures/s |24.1245|25.9404 (+7.53%)|
| Bear PAL pictures/s |22.8702|23.3900 (+2.27%)|
| Regular NTSC foreground mean, cycles |56,055|53,366|
| Regular PAL foreground mean, cycles |57,911|54,402|
| Bear NTSC foreground mean, cycles |81,308|78,082|
| Bear PAL foreground mean, cycles |82,702|79,737|
| Bear NTSC dirty-state mean, cycles |9,599|6,772|
| Regular NTSC longest gap, ms |83.44|66.78|
| Regular grounded landings /26 NTSC |21|20|
| Regular grounded landings /26 PAL |13|15|
| Regular endpoint Y /26 NTSC |23|23|
| Regular endpoint Y /26 PAL |23|24|

Regular NTSC P95 gap remains50.07ms, PAL59.81/max79.75ms. NTSC loses grounded
and endpoint arc8, gains endpoint6; PAL gains grounded1/15 and endpoint24.
Consecutive Y runs shown rise249→252NTSC/229→233PAL. Landed-state age P95 and
maximum remain3/5stepsNTSC,4/4PAL. Original source states/contacts remain exact;
short presented states can still disappear. Different picture populations mean
observed stage costs, not paired component savings. Inclusive helpers are not
added again to whole stages.

Bear scope is the unchanged620-step prefix, active195..425 at level4,122Xvalues/
all eight poses, bounded before the existing one-player guard630. Bear gap P95/
max remain50.10/66.75msNTSC and59.81/59.84PAL. **31.30NTSC regular-route mean does
not certify stable30FPS, original fluidity or all-level performance.**

Regular PAL sampled foreground maximum rises137,171→157,755cycles (about15.0%)
despite the improved mean/FPS. Picture populations differ; this is a sampled
maximum regression, not a paired per-picture cost claim.

## Verification and next work

589host tests,2,115source/2,040density/54header scenes,2,115ordered-audio intervals
pass.18generic+12new real hardware IRQ boundaries pass, including mid-history
copy and mapper restore; AF2negative rejected. All four clean final NTSC/PAL
regular+bear routes reproduce five natural/profile buffers, with exact source
CPU/allRAM, pixels, owners and active-page protection. Exact-source push/PR CI
passes. Independent rebuild/rollback,98,450actualZ80cases per ROM and8,192
contact fields pass. It covers every history byte/value, all33profile pairs,
actor gate combinations, source boundary values, pages/coarse states, registers
and return flags. Initial01 separately reproduces14/16floe-mask failures.

AJ workbook36tabs preserves35historicaltabs/784,619cells/native features; saved
XML/raw-route audit, zero formula errors, two mutation/restore checks and five
rendered regions pass. Native Excel was not exercised. Browser launch, manual
listening, owner fluidity, mobile controls and physical MSX acceptance are
separate from automation; no owner/physical acceptance is inferred.

Next target the remaining expensive bear/player preparation and long-frame
outliers, using complete-route/gap/landing results. No player-only updates that
desynchronize the scene. Issue42/39/15/16 remain open, PR43draft/stacked; root
continues as sole writer in the focused issue chat. Read
`references/dirty-native-result.json` and v22 release human tests.
