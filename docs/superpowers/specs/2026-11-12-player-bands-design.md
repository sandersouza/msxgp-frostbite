# Player rectangle packing and exact three-sprite bear AO

Owner-authorized autonomous Issue42 continuation. Preserve v25 composed pixels,
source CPU/allRAM/mechanics/clock/controls/PSG and standard MSX1/64KiB/16KiB
hardware. No player recoloring, tile conversion, new visual adaptation or source
shortcut.191 parent source files and61 prior evidence roots remain immutable.

## Measured problem and selected design

The complete passive regular NTSC trace exactly reproduces v25's five natural
buffers. General P0 runs in only2 active pictures; optimizing its inner loops
cannot deliver the required average gain. Proposed suffix-key reuse has zero
hits across324NTSC/288PALrows. Reject both as the main architecture direction.

The current ordinary P0 uses two common16-line bands for every color. This
creates up to3 overlapping rectangles despite disjoint hat/shirt pixels. Offline
repacking all72 actual normal recipes preserves every pixel with3 rectangles,
maximum2 per scanline, versus264→216 total entries across recipes. New pattern
pool70 fits the existing137 slots; descriptor16-byte format is retained.

For each color, recover its exact expanded16-bit rows. If all color spans fit16
lines and there are at most3 colors, choose two vertically disjoint color ranges:
place the upper color at lastRow-15 and lower color at firstRow. Position the
remaining color legally. This makes two rectangles disjoint, limiting all3 to
maximum2 concurrent. Preserve original color priority and independently compare
complete source RGB. Unsupported recipes retain the old layout. Normal source
Y19..133, both supported coarse cases, reflection/parity/tail and grid translation
require exact proof, including logo separation. A new cut=max(rectangle starts)
retains the cache logo guard as the maximum hardware rectangle end.

## Cache and code placement

All cache publishers use p_player_cache_store. Change byte0 of each metadata
entry uniformly from upper/lower boolean to signed startY-cut, then change the
hit decoder to add that byte to the translated cut. Count/key/relativecut/color/
pattern allocation and static metadata22..26 retain their formats. Old general
and AK entries become0/-16; new normal entries may use other nonpositive offsets.
Count<=3 is globally safe with at most one overlapping static door;4..6 entries
must retain exactly0/-16 and at most3 per band. Reject positive DY. Cache misses
already invalidate the selected way; publish validity only after all patterns.

The signed hit decoder is shorter; pad before the existing miss label, retaining
all original external addresses. Rebuild the store in its existing113-byte
interval. A bounded upper-entry validation helper can use the23 unreachable bytes
B1ED..B203 after the existing unconditional JP at variant_lookup.replace B1EA.
Validate this actual retired gap with HALT poison before any runtime overwrite.
The helper uses (IX+8), the already-validated1..6 total count: bit2 distinguishes
1..3 from4..6, so it can validate foreign DY without a new RAM flag. No additional
RAM/VRAM region, mapper switch, kernel expansion or ROM resizing is needed.

## Complete bear after packed P0

Independent source geometry proves the full24x20 bear fits THREE16x16 sprites:
keep the exact v25 wideLEFT16 pair and add the thinRIGHT8 strip, whose occupied
height is at most14 rows for every pose/reflection. This avoids any left/right
mode collision with the existing prefix cache. Use22/23 and one extra slot58
PAGE0/59 PAGE1; retain static48..57 and63. These occupy64 previously unused
bytes inside the already reserved2048-byte SGT; no new VRAM region. All source Xphase/coarse/color/background
and viewport boundaries still need composed-frame verification.

Six unique96-byte triples plus512x2 directory,16 group IDs and16 thin DY values
occupy1632 of the existing132 tail's2048 bytes. The first64 bytes of every triple
are the original prefix pair. Low7 cache bits retain group+1; highbit marks the
third pattern valid. Group change clears highbit, and full publication sets it
only after the third upload. Hybrid requests accept either highbit value.

After final WORLD admission, require capacity beforeN<=28 for three entries and
exact scanline occupancy: the wide pair adds1 throughout32 lines, the thin strip
adds1 during its16-line span. Reuse the original prefix safety test, then bound
existing concurrency<=2 inside the thin span at every critical start. Preserve
all existing actor choices/priorities; append bear last. On failure retain v25
hybrid, then full native tile fallback. Restore/force original bear NAME rows
with v25's complete/partial/zero dirty history strategy before any mode decision.
A full-bear hit omits the9.8k-cycle suffix upload/key/NAME path entirely.

## Qualification and promotion

First prove packed P0/cache semantics in an internal source-identical candidate;
then add the full bear. Keep mode-original byte-identical v25 rollback. Root is
the sole tracked writer; independent reviewer writes only new own evidence.
Before promotion: source-derived finite geometry/ABI/negative controls, actual
native calls,2115source/2040density/54header/2115audio/IRQ/AF2, exact source CI,
four clean natural/passive profiles, all26 landing flags and full foreground/ISR
gaps. Adapt ownership/admission models explicitly for new geometry; do not weaken
source RGB, key, atlas, active-page, capacity or mapper guards. No local helper
saving alone qualifies. Publish only a useful qualified ROM, exact hashes/source,
updated historical workbook, rollback, direct WebMSX and concrete human tests.
Stable/all-level29.97/30 remains OPEN until measured; human testing is separate.

## Owner steering and measured continuation

The owner requested closing the small lower left sea-edge gap. This authorized
additional background masking only at X16..23/Y176..183, with original P0
foreground priority retained. The source playfield, physics, actors, header and
logo are unchanged. The independently reviewed correction is additive.

The approved temperature packet rewrite uses four exact streams1/1/1/24;
three extra bottom-padding writes are source-constructor-proven zeros. The
original54-byte gate and14-byte kernel helper stay exact. Native/IRQ review
confirms valid-state equivalence; invalid nonzero padding is a separate negative
domain and is never silently accepted.

For warm exact temperature updates, header NAME rows0..2 already match the
inactive physical page. Omit only that final private prefix publication when
hy_lo=14, the low three dirty bits are set and the first dirty byte is notFF.
The complete list is validated before terminal trimming, final list/count must
be its exact suffix, and all DIRTY flags remain complete. Never change the shared
public NAME uploader or exempt header pixels/ownership from comparison.
