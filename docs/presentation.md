# Original graphics, HUD and PSG integration

Issue14 starts from the accepted native mechanics and immutable
[v0.0.6-progression](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.6-progression).
The original ROM remains gameplay authority. No presentation code may alter
canonical source state, envelope/scoring updates, input order or logical cadence.

The [implementation plan](superpowers/plans/2026-11-01-issue-14-presentation.md)
begins with a separate original raster/audio observer. It preserves the frozen
contact backends and catalogs. A source picture must be associated with the
F019 state that actually draws it through visible-end F476; a recently returned
framebuffer cannot be assumed to show newly changed RAM. Post-visible audio
writes and CPU/RAM transitions retain their actual source order.

The bounded [observation protocol](../references/presentation-contract.json)
retains complete phase snapshots,160x210 indexed rasters and ordered audio writes.
Same-value writes and silent intervals remain meaningful. The parser rejects
missing phases/records, bad clocks, invalid event order, truncated data and any
nonblack pixels in rows omitted by the approved graphics mapping. Full source
serialized states/TIA/RIOT/input journals and producer/backend hashes accompany
the raw stream locally; they are not public assets.

This is protocol implementation, not a claim of a completed observer, dynamic
renderer, listening review or new testable ROM. Task1 source acceptance is still
pending. The published progression diagnostic is unchanged; original graphics
from issue9 prove offline fit only. New live graphics/HUD/PSG need fresh combined
NTSC/PAL timing, actual pixels/events and complete source/native state checks.
