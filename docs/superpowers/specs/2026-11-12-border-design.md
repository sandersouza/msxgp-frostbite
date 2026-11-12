# Reversible sprite-mask replacement

The owner accepted v0.0.18 gameplay as stable and selected visual option3,
authorizing autonomous, non-destructive work toward29.97/30NTSC pictures/s.
Use v18 as immutable control; keep its160sources and all sealed roots intact.
Same Issue42 chat/branch, root sole tracked writer. No two-color player change.

## Approach and builder decisions

1. Keep an exact20-pixel edge by composing partial boundary tiles: rejected for
   this test because black/water/foreground may need three colors on one line.
2. Use a24-pixel tile-aligned edge over the former mask region: selected for
   the authorized item3 test. Crop four extra target pixels on y64..175 only;
   keep header/bear rows0..7 and the footer unchanged. These exact dimensions
   are the builder's presentation choice, not a claimed owner-specified layout.
3. Remove masks alone: retain only as a private timing upper-bound variant.
   It exposes pixels and is not a qualified human-test ROM.

Remove all seven mask entries from cold and cached SAT preparation. Set inactive
CPU NAME column2 to blackID128 on rows8..21 before the existing NAME publisher.
P0 remains foreground, with its original palette, priority, grid24 translation,
contact offsets and mechanics; it may overhang the extra4pixel border at an edge.
Enemy sprites clip to targetX24/sourceX11. Multi-copy edge cases retain tile
fallback; normalizedX0 must not collide with the unclipped-sentinel meaning.
Patch both full eligibility and certified reuse. Remove only the obsolete
one-mask scanline count; retain actual P0 rectangles and global32slot safety.

Reuse the resident gap F57E..F5D1 for the border hook and retired ys_mask69E0
storage for11left masks. Preserve right masksA70B and all original active-page,
owner, mapper, source-clock/input/audio behavior. No new RAM/VRAM. Independent
design review confirmed allocations and flagged certified-setup and X160 cases.

## Measurement and acceptance

Measure full natural NTSC/PAL, foreground excluding complete ISR, P95/max gaps,
all26landings and live bear/dense scenes. Isolated cost savings are not FPS.
Continue reversible attempts within item3 if needed; keep rejected variants
and reasons. Do not halve source simulation, remove actors or alter colors.

Before release: source CPU/allRAM, independently declared adapted pixels,
physical owners and active-page protection; cold/cache/edge/wrap/density scenes;
ordered audio and directed helper IRQs; source/ROM identity and independent
review. Update workbook preserving all32AFtabs. Publish every qualified useful
new ROM with exact bytes/hash/source, limits, human A/B tests and a verified
direct WebMSX link. Preserve v18 rollback. Owner/all-level/physical acceptance
remains distinct. No direct mobile channel is assumed without resolving it.
