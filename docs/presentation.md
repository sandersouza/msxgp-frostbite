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
retains complete phase snapshots, raw native viewports and ordered audio writes.
Same-value writes and silent intervals remain meaningful. The parser rejects
missing phases/records, lost physical frames, bad clocks, invalid event order and
truncated data. Every physical completion is retained alongside the explicitly
partial F476 buffer. The seeded cold RIOT wait can span multiple physical frames;
Stella's160x228/start23 viewport is not assumed equivalent to ALE's160x210 view.
Normalization and black omitted-row validation are separate mandatory gates.
Full source
serialized states/TIA/RIOT/input journals and producer/backend hashes accompany
the raw stream locally; they are not public assets.

For regular262-line frames, normalization selects native rows11..220. The
remaining native margins and every row omitted by the approved MSX mapping must
be black. The first controlled cross-backend fixture matches all33,600 ALE pixels
exactly with this alignment. Partial buffers and irregular startup frames cannot
pass normalization; they remain in the raw observation stream.

Full capsule equality uses identical input and restore journals. Restoring an
already steady Stella state can increment its disabled-jitter stability counter;
comparing to a continuous trace with a different restore schedule would otherwise
misattribute that emulator bookkeeping to the observer. No serialized field is
normalized away. Controlled fixtures disclose their full128-byte RAM injection,
restore baseline and input pins; they do not establish natural reachability.

This is protocol implementation, not a claim of a completed observer, dynamic
renderer, listening review or new testable ROM. Task1 source acceptance is still
pending. An exploratory sound-enabled observer using standard debugger
step/checkpoint bookkeeping reproduced the complete1256-byte frozen initial
interval capsule exactly. This establishes absence of source mutation for that
probe; it does not qualify a renderer or the observer's whole domain.
The published progression diagnostic is unchanged; original graphics
from issue9 prove offline fit only. New live graphics/HUD/PSG need fresh combined
NTSC/PAL timing, actual pixels/events and complete source/native state checks.
