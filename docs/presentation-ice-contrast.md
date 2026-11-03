# Landed ice contrast regression — issue14

Owner feedback on2026-11-03 for v0.0.7-presentation-preview: speed feels about
half of the original; graphics otherwise appear correct, except landed floes
turn the same blue as the sea. The screenshot is retained locally/ignored with
SHA-2567bfbd7345236ce12d9ea13614d5d8b48e7a8dad7baba1a5e6b531002975901ce.
No machine/VDP/emulator configuration, listening or physical-hardware verdict
was supplied. This is human feedback, not a measured universal50% speed ratio.

## Cause and presentation adaptation

An independent original input-only trace changes floe color0C→98 at checkpoint143,
row3 of route-progression-v0-a. Original water remains90. The measured original
RGB is84/138/210 for98 and0/28/136 for90. Unconstrained chromatic nearest-color
mapping selects TMS dark blue4 for BOTH. The template renderer then legitimately
omits a floe whose mapped foreground equals the sea. The underlying source state,
collision and scoring are unchanged; contrast was lost before tile publication.

The mapping now preserves these two gameplay blues as distinct when their
nearest choices collide: keep sea90→4 and choose the nearest other chromatic
TMS color for touched ice98→5 (light blue). Grayscale palettes are not forced
into chromatic colors. This is an explicit presentation adaptation extending
the earlier nearest-RGB policy; original ROM/palette captures remain immutable.
It adds no per-frame CPU routine and changes no canonical RAM or source timing.
Rendering previously invisible floes can increase work, so performance must be
measured again at full visibility; the original hard timing goal still applies.

## Regression evidence

The new host test first failed98→4 and now requires sea4/touched-ice5, including
the complete horizontally scaled pixel span. A grayscale negative first exposed
an overbroad rule; the corrected condition applies only to the two original blue
colors. The original-free suite passes497 tests.

The independent target checker reads frozen original source rasters and actual
physical VDP captures. Its fixed sea4/ice5 expectations never call palette_map.
It rejects the published0.0.7 capture at case6/source(65,88), expected light blue5,
actual dark blue4. This matters because the previous whole-image comparison used
the same deficient palette policy for expected and actual output, so it passed
while the gameplay distinction disappeared. The preview sealer now requires this
independent contrast receipt, bound to the exact ROM, matrix and captured bytes.

The new ROM passes all2,115 complete source-backed images,164,511 source98 and
31,412,979 source90 pixel checks on physical VDP data,24,820 original CPU/all128RAM
checkpoints and all3,499 source/2,472 physical PSG writes. Counts for98 include
other original uses of that same color. Independent natural-window floe-band
coverage includes128,569 source98 pixels; a specific old-ROM landed-floe witness
is matrix case1721/source(46,148), row1, original floe latch98 versus actual TMS4.

[v0.0.8-ice-contrast-preview](releases/v0.0.8-ice-contrast-preview.md) is published
from clean source2cffac7de2f726c1c380914ad5d04372e431fd75. ROM SHA-256:
141044d3c1d4db7544a2f1357bef90e7cc251b85de7cdd41e3378b4776adb88a.
All four fresh public downloads match the seal;0.0.7 remains unchanged.
[Validation](../references/presentation-ice-contrast-result.json) and
[publication receipt](../references/presentation-ice-contrast-delivery.json)
preserve failed timing and pending final game/manual/hardware acceptance.

The original600-frame scripted keyboard probe stays on white floes. To avoid
calling it a blue-floe performance test, a separate private adapter applies
only immutable original one-player route inputs at each native step and checks
every actual CPU/all128RAM checkpoint. Its600-frame prefix reaches430 NTSC and
390 PAL frames with blue floes, matching601/717 source checkpoints. Measured
source updates are37.91/39.20 per second, about63%/65% of original in that
particular prefix. These are bounded research observations, not a universal
speed ratio or complete route/view qualification. Its adapter/scripts/raws are
ignored under outputs/presentation/ice-contrast-route-*-private-b.

The local nominal-TMS-RGB reconstruction of actual native frame202 was inspected:
three blue rows remain visible above the white bottom row. This is decoded VDP
data, not physical hardware or owner acceptance. Request fresh owner feedback
on the corrected contrast. Issue14 remains In progress for original cadence.

The next measured performance investigation can start at the original-input
NTSC prefix's blue-floe frame263:367340 busy cycles, including180862 world,
102269 header/igloo,17984 background and19540 final NAME preparation cycles.
Its raw phase/cost/source checkpoints are retained locally. This identifies
expensive equivalent work; it does not authorize reducing visibility, source
updates, quality or required VDP transfers to meet the budget.
