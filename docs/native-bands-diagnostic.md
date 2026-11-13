# Native bands AO

This v26 diagnostic continues v25 rather than replacing its gameplay model.
The supplied Atari source remains the authority. Source CPU/all128RAM, original
simulation/input/PSG and composed graphics are checked independently. The only
additional presentation adaptation is the owner-requested lower left background
closure X16..23/Y176..183; original player foreground priority is preserved.

## Implementation

All72 normal player descriptors preserve the original pixels with three color
rectangles and at most two concurrent scanlines, using70 of the existing137
pattern slots. Signed cache offsets are uniform for ordinary, general and AK
publishers; existing4..6-plane restrictions and static/logo guards remain.

The bear keeps its exact left16-pixel pair and adds its right8-pixel silhouette
as one sprite. Six96-byte triples fit the existing bank132 tail. Extra slots58/59
occupy64 previously unused bytes within the existing2KiB SGT reservation, with
no new VRAM region. Exact weighted scanline/capacity admission preserves existing
actors and priorities, then retains v25 hybrid and full native fallbacks.

Temperature packets retain32-byte records but use streams1/1/1/24. The three
additional bottom padding bytes are guaranteed zero by the valid source
constructor. The original54-byte gate and14-byte kernel helper stay exact;
unsupported glyphs and other header changes use the unchanged fallback. The
eligible body costs5369→3829 CPU cycles. Invalid nonzero padding remains a
separate negative domain and is never claimed equivalent.

For a warm exact temperature update, header NAME rows0..2 already match the
inactive page. The final private publisher trims only those three sorted rows,
after all other list consumers finish. A new checker validates the complete
input list, exact post-publication suffix and actual unchanged96 NAME bytes.
Dirty flags and every source/raster/key/owner/active-page guard remain enabled.
The generic public uploader stays byte-identical. The58-byte resident publisher
and12 bytes of a proven retired fixed gap suffice; the live26-byte AH bootstrap
and kernel1777/1792 occupation remain intact. No new RAM/VRAM allocation.

## Evidence and limits

Source `eaa441806da4bb8fa4bfff2b0a6e73b3976286fe`,214 files, reproduces ROM
`7765bb9e1485a237c49abe0a95c621bea918b61989aae1fc4ad97b1d8b031c84`.
191 v25 source files and61 sealed controls remain unchanged. A clean independent
rebuild covers the entire chain from v25. Earlier195/200/205/209-source phase
reviews are rebound by preserved hashes to the final214-source candidate.

507,286 phase-proof native calls cover cache publication, exact geometry,
admission, both PAGE values, typed owners and mapper/stack/register contracts.
Additional real checker controls reject corrupt complete lists or changed header
NAME bytes; nine host suffix/marker controls reject omitted/reordered lists.
Source2115/density2040/header54/audio2115, four complete natural/passive routes,
66 hardware IRQ boundaries, AF2 negative,612 host tests and two exact CI pass.

The41-tab workbook preserves all40 earlier tabs and794,519 cells/native features,
with zero formula errors, two mutation/restore checks and five inspected views.
Full foreground and inclusive calls are measured separately; bear cost is inside
HEADER in both versions, and sampled picture populations differ.

Bear NTSC28.1214→29.8305FPS; foreground mean70670→62257, P9582663→76628,
maximum93939→79409 cycles. PAL24.6899→25.0791FPS. Regular NTSC31.5939→31.8277,
PAL29.6550→30.4636. Regular PAL P95/max costs98577/138173→100622/138450 regress
slightly despite improved overall cadence. One50.06ms NTSC bear gap remains;
regular maxima66.75ms NTSC/79.75ms PAL still prevent uniform30FPS.

All26 regular jumps are retained: grounded snapshots20→22 NTSC and14→17 PAL;
endpoints23→25 and23→24; consecutive Y runs254→257 and235→240 of286. No prior
grounded/endpoint flag is lost. These are presentation improvements, not changes
to physics. The bear route is a620-step level4 prefix before the existing630
guard. All-level, owner, mobile, listening, native Excel and physical acceptance
remain open. See [release and human tests](releases/v0.0.26-native-bands-diagnostic.md)
and [machine-readable validation](../references/native-bands-result.json).
