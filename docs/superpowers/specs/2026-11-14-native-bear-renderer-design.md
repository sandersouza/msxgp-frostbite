# Native bear bitmap renderer within Issue44

Parent authority: [approved compact/native design](2026-11-13-compact-native-formats-design.md).
This is an agent-selected implementation decision under the owner's repeated
authorization to complete Issue44 autonomously. The accepted v0.0.30 remains
immutable. No new visual adaptation or source-mechanics change is authorized here.

The current native fallback still requires expanded records, a mask dictionary,
context tiles and strip recipes. Packing96 records from6144 to4108 bytes works
but loses cadence in the PAL bear route. Keep that experiment and its evidence;
use the preceding resident-enemy build as the control for this renderer.

Generate the bear's tile grid from the same six monochrome source pictures
already represented by its576-byte three-sprite pattern pool. Preserve the
complete-sprite admission and all native edge/budget fallbacks. A24x20 picture
requires at most4x3 tiles. Produce a fixed96-byte four-column grid atC480..C4DF,
using existingC500 scratch; no canonical state or source clock is written.
Keep the established bank0 rows6/7 and bank1 row8 physical roles and both
generations. Horizontal wrap, column1 suppression, original background merges
and empty-tile behavior must match the independently decoded original graphics.

The existing raw-pattern-ID metadata is a renderer implementation detail.
Replace it for this backend with an explicit kind10 key. The word encodes
group0..15, source phase0..15, coarse0/1 and fixed row/column cell0..11;
remaining bytes retain background, clip and foreground color. Validate the key
against the physical bank/slot and independently regenerate its mask from the
original Atari glyphs. Do not reinterpret arbitrary old keys or exempt any
pixels, active-page bytes, capacity checks or source-state comparisons.

Alternatives considered: retain all expanded native tables (fails the purpose
of the flat migration); pack records with a persistent64-byte cache (only2036
data bytes saved, measured PAL loss); generate fixed-size masks from the six
shared sprite pictures (chosen: removes an entire expanded representation).
The chosen path must earn its place through whole-frame measurements.

Required evidence: all512 group/phase/coarse native mask grids, every relevant
palette/background merge and declared key/role failure mode; four natural
NTSC/PAL regular/bear routes,2115 original scenes and dense/boundary checks.
Retired tables receive cold CPU-read guards only after their readers are gone.
Keep rollback to the exact input build. A fixture or size estimate is not a
native game, performance acceptance, COM/BIN delivery or physical-hardware test.

Measured implementation choice: direct shifting of the576-byte sprite pictures
passes all512 grids but costs13200 cycles on average. The same pictures have
only22 distinct24-bit rows. Their eight literal shifted four-byte forms use704
bytes, plus120 picture selectors, and produce the same512 grids in8852.5 mean
cycles. Use this bounded row grammar; keep the direct generator as research.

For the native kind10 tile, certify that each background row is solid: PGT=FF
and equal CGT nibbles. Store the generated mask directly as PGT and encode CGT
as(foreground<<4)|background. This is pixel-equivalent even on empty masks or
when foreground equals background, and avoids per-pixel composition. It is a
new explicit byte representation, not a promise to retain the old redundant
PGT/CGT encoding. Reject nonuniform backgrounds. The current bear roles use five
eight-byte solid-per-row backgrounds; keep the independent original RGB oracle
and physical-slot/key checks. No additional visual compromise is introduced.
