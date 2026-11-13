# Prepared temperature-unit updates AL

v24 preserves v23 graphics, colors, source CPU/RAM, mechanics, controls and PSG.
It replaces generic header traversal only when the temperature units glyph is
its only changed element: first=0, color=0, upper=0, lower=14. Other updates and
unsupported font values keep the original path. No new visual adaptation.

Source: `48be6de16c8862580b8add5fd32937d802a7feb3`.
ROM: `4686698ca7c19cf6db27a8393d70a15297fe982b0f9a68274964233f2355c5be`.
4 MiB ASCII16; standard-speed MSX1, 64 KiB RAM, 16 KiB VRAM, TMS9918 and PSG.

## Architecture and safety

The passive v23 bear trace reproduced all five natural buffers and isolated four
active header bursts of 18,868..18,996 cycles. Generic header work alone consumed
17,142..17,270; the igloo consumed only 594..722. Each burst changed just the
lower units digit, yet traversed the general glyph/column machinery.

256 exact 32-byte programs cover 16x16 lower font pairs, with 24 original PGT
bytes, six key bytes and padding. Three columns update only their middle last
PGT byte and bottom first seven bytes; all upper pixels and key nibbles remain.
CGT is untouched. Data occupy retired tails 127..130, body 131 (199 bytes).
A 54-byte gate at 69FC..6A31 follows the existing NAME fill. Fourteen bytes at
EFE3..EFF0 occupy reserved kernel padding, increasing use from 1,763 to 1,777 of
1,792 bytes; no new RAM/VRAM region. Dead P0 scratch C480..C49F stages programs.
Live header codes C4C0 remain protected. Success restores the original final
lookup bank 118; fallback restores the incoming mapper and original continuation.

The initially proposed 60B6 gap was rejected before writes: it contains live
AA publication used by non-atlas/blue floes. World palette 6100, uploader 6A46,
header banks 116..118, igloo/player 119 and shore recipes 120..126 are untouched.
Independent HALT poison of the actual reclaimed areas passes 2,115 scenes;
49,152 contact fields in a six-tail retirement superset match, while all five
actual rewritten lower-14-KiB contact prefixes (71,680 bytes) remain unchanged.
All 182 parent sources and 47 sealed evidence roots remain unchanged. Four
additive source files produce the 186-file closure. `--mode original` reproduces
v23 byte-for-byte; no historical release is replaced.

## Whole-route results versus v23

| Active route / cost | v23 | v24 |
|---|---:|---:|
| Regular NTSC complete pictures/s |31.3564|31.5939 (+0.76%)|
| Regular PAL complete pictures/s |29.5956|29.7739 (+0.60%)|
| Bear NTSC complete pictures/s |27.0953|27.0953 (unchanged)|
| Bear PAL complete pictures/s |24.2955|24.6899 (+1.62%)|
| Bear NTSC foreground maximum, cycles |104,256|97,481|
| Bear PAL foreground maximum, cycles |104,394|97,619|
| Bear NTSC header maximum, cycles |18,996|12,221|
| Bear PAL header maximum, cycles |18,972|12,197|
| Bear PAL foreground P95, cycles |86,162|88,004 (worse)|
| Regular NTSC foreground maximum, cycles |127,789|127,909 (worse)|
| Regular PAL foreground maximum, cycles |138,161|138,062|

Bear foreground means: 74,384→74,126 NTSC / 76,148→76,038 PAL. Regular means:
52,904→52,449 NTSC / 53,835→53,373 PAL. These are different sampled picture
populations; inclusive helpers are already inside stage costs. Gains are small.
The NTSC bear gap maximum remains about 50.10 ms. PAL bear gap P95 falls
59.81→39.91 ms, maximum 59.84→59.81 ms. Regular gap P95/max remain about
50.07/66.78 ms NTSC and 59.81/79.75 ms PAL. No universal smoothness claim.

All 26 NTSC grounded/end-Y landing flags remain unchanged (20/26 and 23/26).
Consecutive Y runs shown improve 252→254 NTSC and 233→234 PAL, out of 286.
**PAL arc 4 loses its grounded and endpoint snapshot:** grounded 15→14/26,
endpoint 24→23/26. Exact source trajectories, contacts and input remain equal;
this is a presentation sampling regression, explicitly retained in this diagnostic.
Shown grounded-landing age P95/max remain 2/3 source steps NTSC and 2/4 PAL. Human comparison
should check landings, especially PAL; rollback stays available.

Bear scope is the unchanged 620-step prefix, active source 195..425, level 4,
122 X values/all eight poses, bounded before guard 630. **Stable/all-level
29.97/30 FPS and original fluidity remain open.** The regular mean above 30
is not a stable minimum or a source/game-speed change.

## Validation and next work

593 host tests; 2,115 source/2,040 density/54 header scenes; 2,115 ordered audio
intervals (3,499 source writes/2,472 physical PSG writes); 18 generic plus 14
new directed hardware IRQ boundaries; AF2 negative; two exact-source CI runs.
Four clean-source passive replays match all five uninstrumented natural buffers.
Source CPU/all RAM, exact coherent pixels, physical owners and active page pass.
An accidentally selected audio-negative flag deliberately inserted an extra
write and was rejected; the separate positive audio run passes unchanged ROM.

Independent 38,320 calls per ROM (76,640 total) cover all 256 pairs, both pages,
32 upper fonts, all eight low-bit combinations, six incoming banks, repeats, stable levels,
15 matching colors and nine guard/fallback classes. There are 21,552 body
entries and 21,504 program copies. PGT/CGT/180 keys/owners/NAME, all other VRAM,
source/P0/SP/IFF/slot/mapper guards pass; directed hardware IRQ tests also
check complete register restoration. Retirement and clean source
rebuild are bound in `references/temperature-programs-result.json`.

The AL workbook appends one comparison tab, preserving all 37 historical tabs
and native features. Exported XML/raw-route audit, zero formula errors, two
mutation/restore checks and five rendered regions are required before release.
Native Excel, listening, mobile controls, owner and physical MSX acceptance are
separate and pending; browser launch alone proves none of these.

Next: the remaining roughly 35k-cycle bear WORLD phase, its row metadata and
uploads, followed by the residual player/preflight costs. Any sprite reconsideration
must first show a benefit under the current grid/mask budget; the old AE sprite
experiment remains rejected. No new visual compromise or source/frame shortcut.
Issue 42/39/15/16 remain open; PR43 remains draft/stacked on41. See the v24 release
for exact attached bytes, rollback and human tests.
