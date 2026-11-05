# Player palette and header reuse (Issue 42, W)

User authorized autonomous correction, whole-game measurement, workbook and
testable release on 2026-11-05. Keep V immutable; root owns source edits.

## Design and constraints

Use a player-only color adapter: Atari24 to TMS10 (hat),36/16 to11
(skin/legs),06 remains14. Apply only at EB=F0=0: terminal animation keeps its
original palette to retain the four-plane limit. Preserve every non-player pixel.
Compare the original raster against a separately tagged player compositor so
world colors cannot accidentally inherit the adaptation.

Reuse fixed physical header roles before constructing glyph keys. Identity per
inactive page: 12 raw glyph selectors, three mapped colors and level>=20.
Build a ten-bit changed-column mask before key packing; unchanged columns skip
packing and tile construction but restore their fixed NAME. Changed columns use
the original helpers. Publish validity only after successful header completion;
then execute the original igloo path. The original dirty-row gate already skips
fully unchanged headers, so a whole-header-only cache was rejected before coding.
Cache lives in unused initialized Q scratch below E880. Keep the source IRQ,
input, PSG, coherent snapshot and presentation commit policy unchanged.

Alternatives: repeated whole-world micro-optimizations have modest gains;
independent player-only presentation risks incoherent collision visuals. Select
exact retained header reuse, inspired by Seaquest's static-region approach.

## Execution

- [ ] Add failing host contracts for palette isolation, source tag stripping,
  and header identity including the level19/20 transition.
- [ ] Add a reproducible builder on exact V and a bounded RAM driver. Verify
  parent source hashes, expected patched bytes and untouched live allocations.
- [ ] Run the full source/density picture matrices, original CPU/RAM route in
  NTSC/PAL, IRQ/guard checks and host tests. Measure full pictures and gaps;
  never substitute routine savings for whole-game improvement.
- [ ] Update a new W workbook while retaining V. Independently review changes.
- [ ] Commit clean source, repeat final identity-bound checks, publish exact
  ROM/SHA/source/validation and human tests; update issue/PR/handoff.

Review focus: cold/blank transitions; level>=20 glyph override; player coarse
shift and color races; death/night colors; IRQ stack/mapper invariants. No
owner/physical acceptance is inferred from automated equivalence.
