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

For measured262/263-line frames, normalization selects native rows11..220. The
remaining native margins and every row omitted by the approved MSX mapping must
be black. The first controlled cross-backend fixture matches all33,600 ALE pixels
exactly with this alignment. Partial buffers and irregular startup frames cannot
pass normalization; they remain in the raw observation stream.
The original right-edge bear positioning adds one scanline for controlled
coordinates151/159:19988 source cycles, versus19912 in the interior. Identical
plain/probe full capsules and all ALE pixels agree there. The target frame
budgets remain59736/71364 Z80 cycles; source duration is retained independently.

Full capsule equality uses identical input and restore journals. Restoring an
already steady Stella state can increment its disabled-jitter stability counter;
comparing to a continuous trace with a different restore schedule would otherwise
misattribute that emulator bookkeeping to the observer. No serialized field is
normalized away. Controlled fixtures disclose their full128-byte RAM injection,
restore baseline and input pins; they do not establish natural reachability.

## Verified independent source package

The [source receipt](../references/presentation-source-result.json) binds the
canonical checker commit, complete consumed-file hashes, exact backend/patch and
private evidence digest. The clean sound-enabled backend uses standard debugger
step/checkpoint bookkeeping. Its observation sidecars are not serialized and do
not write original ROM, RAM, CPU or TIA/RIOT semantics.

- 1690 controlled fixtures, independently repeated: all requested128-byte RAM
  states, full plain/probe capsules, native viewports and normalized rasters agree.
  Each run retains1690 physical frames and1704 ordered audio writes.
- Literal temperature, footer and level byte domains0..255; reserves0..9; both
  players/eight score values; sixteen blink phases; all160 player and bear X
  coordinates; the complete544 original-graphics fixture set. Invalid BCD bytes
  are explicit literal-domain probes, not reachable gameplay claims.
- 32 cold-route intervals, independently repeated:38 physical frames,31 mapped
  frames and28 audio writes. All seven irregular seeded startup frames remain
  raw and excluded from mapped rendering proof.
- 45 input-only windows, independently repeated:394 observations and1767 audio
  writes across all four progression modes, real player swaps, construction,
  igloo entry, bonus/next-level, death/restart, fish rewards and Select/Reset.
  Overlapping windows do not constitute394 unique whole-game intervals.

The independent checker reopens scripts, raw streams, complete checkpoint files,
derived rasters and final capsules. It verifies actual bytes, source phases,
CPU/all128RAM, raw inputs, restore chains, clocks/frame counters and event order,
with historical Git provenance and frozen-route CPU/RAM comparisons. Tests reject
changed or rehashed phase registers/RAM and modified scripts, capsules, images,
streams or completion markers. All256 literal debugger byte values also underwent
actual readback: decimal `#value` avoids Stella's hex-looking system labels.

```sh
.venv/bin/python -B -m unittest discover -s tests
.venv/bin/python -B scripts/presentation_source_check.py --out outputs/presentation/source-check-local-1
```

The output must be fresh. The committed local-path config documents every input;
raw captures, original ROM copies and generated pictures stay ignored. A later
documentation commit does not relabel the frozen source/checker producers.

## Explicit old-ALE edge disagreement

540 of544 frozen ALE rasters match all33,600 pixels exactly. The four controlled
`edge-0/1/7/8` cases differ only in the bear region:109/123/126/126 pixels. The
older [ALE TIA implementation](https://github.com/Farama-Foundation/Arcade-Learning-Environment/blob/v0.12.1/src/ale/emucore/TIA.cxx#L2175)
and [pinned Stella7 counter handling](https://github.com/stella-emu/stella/blob/d55b1aec0d067a4c901a6dcdf81cb8f579685659/src/emucore/tia/TIA.cxx#L2098)
resolve the horizontal reset near blanking differently. This is retained as an
explicit backend disagreement; it is not hidden by shifting mechanics.

Stella7 remains the rendering authority, consistent with the frozen source
contact geometry. Its actual bear pixels match the original glyph across all160
controlled X coordinates: origin `(E8+(6 if E8<15 else1)) mod160`, vertical origin
`58+(E8>=150)` for the measured pose/reflection/day fixture. Other poses, priority
and combined scenes still need the general compositor proof. The extreme control
fixtures are not evidence that normal play reaches those coordinates. Real Atari
hardware has not adjudicated the emulator disagreement.

## General source compositor and finite resources

The read-only `presentation_model.describe/pixels` implementation reproduces
every one of33600 source pixels in all2115 checked frames:1690 controlled
fixtures,31 regular cold-route frames and394 natural-window observations.
It derives glyph masks, coordinates, priority, colors and source scanline holds
from the original tables/kernel. It contains no frame/route playback table and
does not replace the native gameplay core. Seven irregular seeded startup frames
remain explicitly outside the normalized rendering domain.

The [resource receipt](../references/presentation-assets-result.json) binds
producer `641c26a2cf7e5aba354fc3ff1429a74c7fc65d5a`, the original source receipt,
measured palette receipt and all consumed helper/config hashes. Its private
full proof SHA-256 is
`50f3730428d8a0dbc9fc5bf5f40b0cde8a15a435f7f83e10f5deb6bbef28d355`.
The checker reopens source scripts, raw streams, checkpoint files and provenance
before comparing pixels. The independent palette calibration measures all128
even source codes in two seeded ALE0.12.1 instances, retaining complete
indexed/RGB images and unchanged before/after readback states. This is RGB
calibration only; Stella7 remains the selected rendering/contact authority.

Exact offline SCREEN2 compilation needs at most45/34/47 tiles across its three
banks, four full sprite rectangles per scanline and384 sprite-pattern bytes.
The complete colored tile unions are715/1182/618, so a static global atlas
cannot occupy the256 available hardware IDs per bank. Two64-slot generations
per bank fit the complete checked domain, with explicit rejection above64 and
no lossy fallback. A signature is only a lookup hint: full16-byte tile equality
governs reuse. Prepare transactions target unreferenced patterns, colors,
name pages and sprite patterns; SAT publication belongs to VBlank. Unchanged
resources are reused. This host model is not live Z80 performance evidence.

One16KiB primitive bank uses13984 bytes:12288 for all eight-bit expansion masks
at16 horizontal phases,1024 for source table views,256 reversal entries,
160 clipping masks and256 source-color conversion entries. These generated
original-derived bytes remain ignored. No full bitmap is stored as ROM playback
or uploaded every frame. The largest2784-byte preparation in the offline suite
includes initialization and arbitrary fixture transitions; it does not prove a
frame deadline. The maximum SAT transaction is49 bytes.

The proposed standard64KiB RAM reservation holds exact cache tile bytes at
D000–E7FF (6144 bytes), separate768-byte name shadows atC800–CAFF andCD00–CFFF,
and signatures/scratch/control data atCB00–CCFF. Primitive work usesC480–C4FF
and two128-byte source snapshots useC500–C5FF. CanonicalC000–C07F, source ABI
C600–C6FF and IO shadowC700–C75F retain their roles. The presentation profile
must enforce the E800–F2FF heap guard, F300–F33F stack redzone and F340–F37F
stack bounds. Frozen diagnostic profiles retain their original guard. The
manifest lists disjoint reservations; actual target writes/guards and the
complete graphics/input/audio frame budget still require verification.

Reproduce from committed producers and the retained ignored inputs:

```sh
.venv/bin/python -B scripts/presentation_palette.py --out outputs/presentation/palette-new
# Use that fresh calibrated path in a reviewed committed assets config.
.venv/bin/python -B scripts/presentation_assets_check.py --out outputs/presentation/assets-check-new
.venv/bin/python -B -m unittest discover -s tests
.venv/bin/python -B scripts/source_policy.py
```

The committed config references the existing immutable calibration; a new
capture does not silently replace it. Diagnostic layout metadata stays outside
the source compositor; every target view needs its own checks.

## Remaining target work

Source acquisition does not qualify a dynamic renderer, listening review or new
testable MSX ROM. The published progression diagnostic is unchanged; graphics
from issue9 and the resource model above prove offline fit only. New live graphics/HUD/PSG need fresh combined
NTSC/PAL timing, actual pixels/events and complete source/native state checks.
