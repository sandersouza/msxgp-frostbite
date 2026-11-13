# Prepared temperature-unit updates AL

Same owner-authorized autonomous Issue42 continuation, root sole writer. v23
runtime295f330 ROMb1a1...cadd9/182sources, HEAD304c5ae,47sealed roots. Preserve all
source/mechanics/graphics/pastels/controls/PSG, exact v23 rollback, no new hardware.

Passive NTSC bear profiles reproduce all5v23 buffers. Four active header bursts
cost18,868..18,996cycles; hy_header alone17,142..17,270, igloo594..722. Decisions:
hy_first0/color0/up0/lo14. Only lower glyph7 changed (temperature units), causing
three columns1..3 updates; generic full traversal dominates. Initial profiling
bank filters missed calls; corrected02 reproduces raw buffers and actual costs.

Test exact prepared programs only when first0/color0/up0/lo14. Glyph neighbors
remain unchanged, lower degree icon is always32; pair digits must be0..15 else
fallback. 16x16=256programs include24PGTbytes (three original8-byte lower streams)
and6metadata bytes (low-nibble contribution and tail byte per column), padded32.
Index=tens*16+units, packed64programs/2KiB tail, banks127..130 (4tails). Body131.
CGT remains untouched because colors match. Update only middle lastPGTbyte and
bottom first7bytes, plus four lower-key fields per column; preserve upper key
nibbles and all other metadata. Full current v23 path remains fallback.

Gate after existing NAME fill, at hy_header.no_clear; first instruction3-byte
load becomes guarded JP to fixed bank0 stub69FC..6A45 (74bytes), subject to retirement proof. Protect LIVE
aa_publish60B6..60FF, upload6A46,
world palette6100..61FF, igloo6212..6248 and all v23data/header116..118/grid119/
P0tables120..126. Audit retired gap/six tails before runtime writes. A short RAM
copy helper+mapper-exit fits14of29remaining reserved kernel bytes atEFE3. Banked
body stages32bytes at dead P0planes C480..C49F after P0 upload. Gate pushes prior
mapper; unsupported glyphs restore it before original continuation, successful
path restores original last-lookup bank118 then w_save. Exact SP/IRQ/mapper and
scratch liveness require independent proof. No new RAM/VRAM region or ROM size.

RED→GREEN program bounds/middle-key nibble preservation; finite actual Z80
font/upper-key/flags/fallback/active-page/IRQ proof, all source/density/header/
audio/negative/CI/clean replay. Measure whole regular/bearNTSC/PAL/gaps/landings;
reject without useful whole-route win. Qualified ROM gets workbookAL preserving
37tabs, exact release/source/hash/WebMSX/human tests. Stable/all-level30FPS and
owner/physical acceptance remain open; keep42/39/15/16 and draftPR43.
