# Exact hybrid bear AN

v25 retains v24 composed graphics, player colors, original source CPU/RAM,
mechanics, controls, simulation clock and PSG. It renders the bear's left16
pixels with two vertically adjacent sprites and its right suffix with tiles.
Unsupported states keep the complete native tile renderer. No new visual
adaptation or player recoloring is introduced.

Source: `13bf76ed540b968a6a6746385a396f6e4feeba71`.
ROM: `bf5c703d1e607a47bec037a1e5bac0ce32d34539f14e051f69134470d78dae41`.
4 MiB ASCII16; standard-speed MSX1,64KiB RAM,16KiB VRAM,TMS9918 and built-in PSG.

## Architecture

Full-sprite bear admission fails nearly every sampled picture because two bear
rectangles per scanline plus three player rectangles exceed the hardware limit.
A single bear rectangle per line fits. Its two16x16 patterns occupy inactive
slots22/23 or46/47. Bear pixels still occupy exactly the original24x20 raster;
the suffix begins at the precise pixel boundary, with no shape/color change.

Admission runs after all existing WORLD choices, against the complete final
SAT, counting transparent rectangle portions. The bear is appended last, keeping
all existing sprite choices/priorities. At most31 sprites plus the terminator
are emitted. The normalized X range11..144 prevents sprites exposing pixels
over the existing black NAME column. Edges, unsupported colors, hidden/death
states, capacity and unsafe scanlines retain the full original tile path.

The overlap list is filtered to the bear's32-line span. At most3 rectangles are
always safe; exactly4 are safe if their relative starts span at least16 lines.
Other cases keep the exact critical-scanline test. Relative coordinates preserve
Y-wrap correctness. Neither flickering nor missing player colors is accepted.

512 source descriptors map to96 records. Six precomputed far pointers in each
22-byte record select352 exact44-byte transactions:16 PGT bytes,16 CGT bytes,
then12 owner-key bytes. First93 records occupy133:B800; the final3 share body114.
Programs use retired tails134..141; directory/SGT share132. Actual level>=3
palettes are day1/night15.80 bounded masks13539..13618 retain kind0 keys only in
the exact suffix boundary roles. The independent owner oracle derives them from
original masks/cuts; every other owner/atlas/active-page guard remains enabled.

The deferred wrapper restores registers, flags, mapper, original coarse state
and igloo activity before continuing HUD. It reuses the already restored
background only when all3 ORIGINAL dirty bits for rows6..8 were set. Otherwise
it unions those rows, updates the sorted list/FC00 flags and restores them fully.
Zero/partial dirty and sprite/tile eligibility changes therefore remain safe.

Retired header RAM supplies105 of110 bytes; existing kernel occupation stays
1777/1792. E8B9/BA hold the two inactive SGT cache keys, after four read/write
watchpoint routes found no prior access. HALT poison of reclaimed header/body/
directory padding passes2115 source and54 header scenes. No new RAM/VRAM region,
mapper size, clock change or expansion. All186 v24 source files and56 sealed
evidence roots remain unchanged. `--mode original` gives byte-identical v24.

## Whole-route comparison with v24

| Active route / foreground cost | v24 | v25 |
|---|---:|---:|
| Bear NTSC complete pictures/s |27.0953|28.1214 (+3.79%)|
| Bear PAL complete pictures/s |24.6899|24.6899 (unchanged)|
| Regular NTSC complete pictures/s |31.5939|31.5939 (unchanged)|
| Regular PAL complete pictures/s |29.7739|29.6550 (-0.40%)|
| Bear NTSC mean cycles |74,126|70,670|
| Bear NTSC P95 / maximum cycles |85,694 /97,481|82,663 /93,939|
| Bear PAL mean cycles |76,038|72,824|
| Bear PAL P95 / maximum cycles |88,004 /97,619|84,976 /93,792|
| Regular NTSC mean / maximum cycles |52,449 /127,909|52,551 /128,020|
| Regular PAL mean / maximum cycles |53,373 /138,062|53,582 /138,173|

The deferred bear body averages15,815 NTSC/16,376 PAL cycles, now inside HEADER;
the old bear was inside WORLD. Do not count that stage migration as HUD work or
add inclusive calls to full-frame costs. Picture populations differ. Worst bear
gaps remain about50.10ms NTSC/59.81ms PAL; regular maxima66.78ms/79.75ms remain.
**Stable/all-level29.97/30FPS and original fluidity are still open.**

All26 regular landing/end flags match v24:20/23 NTSC and14/23 PAL. Consecutive
Y runs shown stay254/286 NTSC and improve234→235 PAL. Existing missed landing
snapshots remain; shown grounded ages P95/max2/3 NTSC and2/4 PAL are unchanged.
Bear scope is the unchanged620-step level4 prefix, active source195..425, before
the existing guard630. This does not establish every level's performance.

Internal iterations01/02 were rejected at20.8429/26.4290 bearNTSC FPS despite
correct pixels.03 reached27.7374;04 gave no additional cadence. All are archived
with exact source closures. Only the useful, qualified05 bytes become v25.

## Validation and next work

598 host tests;2115 source/2040 density/54 header scenes;2115 audio intervals
with3499 source writes and2472 physical PSG writes;18 generic+18 new hardware
IRQ boundaries and AF2 negative control; two exact-source CI passes. Four clean
passive profiles reproduce all5 corresponding natural buffers. Source CPU/all
RAM, coherent pixels, ownership and inactive-page protection pass throughout.

Independent native review covers5440 wrapper calls (4672 coherent-source cases
and768 explicitly isolated coarse-override ABI cases),5436 rasters, all96
records/all352 physical programs/80 masks, all8 dirty histories and36,436 valid
keys.6274 additional admission calls compare with all32 exact scanlines, including
span15/16/17, raw-Y wrap and capacity boundaries.03/05 wrapper outputs are byte
identical. ABI cases are not natural gameplay or reachable-source acceptance.

The40-tab AN workbook preserves39 historical tabs/native features, with complete
raw/XML/formula audit,2 mutation/restore checks and5 rendered regions. Native
Excel, mobile controls, human listening/gameplay and physical hardware remain
separate and pending. Browser launch proves only cartridge loading/game picture.

Next: the remaining player/preflight long frames and NAME uploads, using complete
route measurements and unchanged source cadence. No player-only scene update or
simulation shortcut. Issue42/39/15/16 remain open; PR43 stays draft/stacked on41.
