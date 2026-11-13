# Viewport edge corrections

> Execute inline, with independent review of the additive native patch.

**Goal:** Align player clipping with the expanded X16 edge and prevent enemy
glyph overflow at the right edge from appearing at the left. Keep original
mechanics, source coordinates, colors, controls and PSG unchanged.

**Baseline:** Sealed v27, ROM78090dde8429a5bc6097e02cfaf278539e05ff68b9582d65e16d430d04334c8a.
Same Issue42 writer and branch; all73 prior evidence roots are read-only.

- [ ] Reproduce both defects with synthetic pixel cases and actual native calls.
- [ ] Add a guarded builder, native helper and independent view oracle. Reuse
  only the verified ECC0..ECFF alignment padding. Preserve all220 parent sources.
  Bypass old left-edge player recipes/cache entries whose clipping differs.
- [ ] Verify finite edge/copy/palette/cache/IRQ cases, complete scene matrices
  and whole regular/bear NTSC/PAL routes. Compare full-frame timing and landings.
- [ ] Update the existing performance workbook, clean rebuild/CI and review;
  publish an immutable diagnostic release with exact ROM, hashes and human tests.
