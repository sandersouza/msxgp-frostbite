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

Current target build/whole-image/contrast/audio/native/timing checks and any new
release must be recorded before claiming that the game-level regression is fixed.
Never replace the0.0.7 binary; changed ROM bytes require a new version. Issue14
remains In progress for color validation and the original real-time cadence.
