# Viewport edge corrections

> Execute inline, with independent review of the additive native patch.

**Goal:** Align player clipping with the expanded X16 edge and prevent enemy
glyph overflow at the right edge from appearing at the left. Keep original
mechanics, source coordinates, colors, controls and PSG unchanged.

**Baseline:** Sealed v27, ROM78090dde8429a5bc6097e02cfaf278539e05ff68b9582d65e16d430d04334c8a.
Same Issue42 writer and branch; all73 prior evidence roots are read-only.

- [x] Reproduce both defects with synthetic pixel cases and actual native calls.
- [x] Add a guarded builder, native helper and independent view oracle. Reuse
  only the verified ECC0..ECFF alignment padding. Preserve all220 parent sources.
  Recompile the existing standing-shore reservation for X16 and distinguish
  partial cache keys160..167. Keep the original cache eligibility and fast path.
- [x] Verify finite edge/copy/palette/cache/IRQ cases, complete scene matrices
  and whole regular/bear NTSC/PAL routes. Compare full-frame timing and landings.
- [x] Update the existing performance workbook, clean rebuild/CI and review;
  publish an immutable diagnostic release with exact ROM, hashes and human tests.

The initial fallback-only prototype at31f16d8 passed pixels but caused75k-cycle
sprite preparation when the bear dragged P0 through X7/4/1. It is retained as a
rejected local control. Prepared576-case shore programs fit the same reservation
with239 patterns/134 records/max4 entries; no source mechanics or graphics change.
