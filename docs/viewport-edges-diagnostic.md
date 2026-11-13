# Viewport edge corrections

The v27 view opened the playfield to X16 but retained the old P0 source-X8
clip and enemy glyph modulo160 wrap. Owner feedback exposed both defects.
The new P0 source cut5 plus a physical first-byte SGT mask keeps the fractional
pixel at X16. The native enemy row stops at column31 instead of wrapping its
remaining glyph into columns1/2. Each distinct source copy still normalizes
normally; source coordinates, contacts, simulation and PSG are unchanged.

Normal standing-shore programs are regenerated from the original row commands
into the existing banks120..126 reservation:576 cases,239 patterns,134 records,
max4 entries. Private cache keys160..167 distinguish partial P0 positions from
all old clip/shore keys. Old public eligibility/AK code stays byte-identical.
The helpers occupy52 bytes of existing ECC0..ECFF alignment padding; no RAM/VRAM
hardware increase. Previous player palette, footer and five-plane fade remain.

The fallback-only prototype31f16d8 was pixel-correct but rejected for75k-cycle
left-drag sprite preparation. Final source `ece9a5aa395592ac143255dfd618ac46d1b14b4c` restores prepared/cache
paths and is the only new released candidate. Exact ROM `e85b8bc13ebd07888b91d66fc76677ca3e7d210182d40c242cdd6c1a5c2dafd8`.
Build from sealed v27 with `scripts/build_viewport_edges.py`; final artifact is
`outputs/presentation/viewport-ar/build-prepared-final`, not the rejected older
`build-final` local prototype. Raw routes/profiles are in`viewport-ar-research`;
current native review in`viewport-ar-prepared-review`. Historical `shore_recipes`
metadata describes the ancestor; `viewport_edges.prepared_shore` is current.

Whole cadence is approximately unchanged, with0.2% regular-route overhead.
Landing/endpoint snapshots remain unchanged; one NTSC Y run is missed relative
to v27. Stable/all-level30FPS and human/physical acceptance remain open.
See [release/human tests](releases/v0.0.28-viewport-edges-diagnostic.md),
[validation](../references/viewport-edges-result.json) and the43-tab workbook.
