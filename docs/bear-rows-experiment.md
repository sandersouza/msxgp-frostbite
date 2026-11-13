# Rejected prepacked bear row metadata AM

The experiment preserves exact v24 graphics/mechanics/source CPU/RAM/input/PSG,
but **does not improve complete-picture cadence on any measured route**. Do not
promote it. Public v0.0.24 remains the exact tested ROM/base; no new human ROM or
release is warranted. Stable/all-level 29.97/30 NTSC remains open.

Public source `48be6de16c8862580b8add5fd32937d802a7feb3`, ROM
`4686698ca7c19cf6db27a8393d70a15297fe982b0f9a68274964233f2355c5be`.
Private prototype `cee4b6cb5f03b07980284c8bac7430edb08bfff52f8a7ba1d48c65a5b720dfdf`,
based on development commit0f43049 with four dirty experimental sources. Those
four files are archived/hash-bound under ignored AM research, then removed from
the public source tree. All186 v24 runtime sources/52 sealed predecessors remain
unchanged. Restoring archived exact files on the declared parent reproduces the
prototype; no clean-source CI/release qualification is claimed.

## Experiment and allocation finding

The native bear spent about20,184 inclusive cycles per active NTSC picture.
Its bulk path spends1,780 preparing strided logical IDs, plus clearing24 metadata
bytes per row and rebuilding six-byte keys. Compile96 exact192-byte packets:
72day keys+72night keys+12strip indexes+24 original flat IDs+12padding. Empty
keys remain allFF; three-column geometry pads each key row separately while its
logical ID scratch retains nine contiguous IDs+three trailing zeros.

A42-byte helper replaces49 existing RAM bytes EF78..EFA8; original uploader EFA9
is untouched. Body112 contains a96x3 far directory and original bulk admission,
certification, strip uploads and NAME writes. Ten packets per tail use132..141.
Original record pointers, IX strides and C50D scratch remain exact. Each dirty
row uploads its original64-byte PGT/CGT strip before publishing24 prepared keys.
No new RAM/VRAM region or hardware; source/frame clocks remain unchanged.

The initial132..143 allocation was rejected **before runtime construction**.
HALT poisoning caused30/2115 scene pixel differences without a HALT:142..146
contain live enemy occupancy used by v_geometry.149 contains live P0 patterns,
150 partial-contact/I allocations, and151+ unrepacked contact tree/profile data.
These regions remain protected. Corrected132..141-only poison passes2115 scenes,
81,920 contact fields; the larger failed30-scene proof remains preserved.

## Whole-route results versus v24

| Active observation | v24 | AM prototype |
|---|---:|---:|
| Regular NTSC complete pictures/s |31.59394|31.59394|
| Regular PAL complete pictures/s |29.77389|29.77389|
| Bear NTSC complete pictures/s |27.09527|27.09527|
| Bear PAL complete pictures/s |24.68986|24.68986|
| Bear NTSC foreground mean, cycles |74,126.12|73,690.85 (−435.28)|
| Bear PAL foreground mean, cycles |76,037.82|75,595.11 (−442.71)|
| Bear NTSC foreground P95, cycles |85,694|85,338|
| Bear PAL foreground P95, cycles |88,004|87,648|
| Bear NTSC foreground maximum, cycles |97,481|96,705|
| Bear PAL foreground maximum, cycles |97,619|96,843|

The ID helper saves about766cycles/picture, but far lookup and key-publication
overhead consume much of that saving. Full foreground improves only0.59%NTSC/
0.58%PAL. No positive cadence, landing or useful gap improvement follows. Tiny
floating-point/submicrosecond timing differences are not an FPS gain. Regular
foreground distributions are exactly unchanged; all26 grounded/end flags and
254NTSC/234PAL Y-runs match v24, including the existing PAL arc4 omission.

## Evidence and decision

597 host tests at the experiment checkpoint;2115 actual-source scenes and2115
ordered audio intervals pass. Four passive full foreground profiles reproduce
all five uninstrumented natural buffers; source CPU/allRAM, coherent pixels,
physical owners and active generation remain protected.

Independent7,824 actual calls per ROM (15,648total) cover all96 records, both
themes/pages, eight dirty masks, cold/repeated state, edges/fallback/history.
All426 output bytes and AF/BC/DE/HL/IX/IY match, including PGT/CGT/72keys/NAME,
old pointers, logical IDs and scratch. All other VRAM/active metadata/P0/source/
SP/IFF/slot are protected.10,560 metadata copies follow10,560 completed strip
uploads. The independent model matches96 packets and directory entries; all
98,304 contact fields in its protected-domain proof pass. Review:
`a921bffc6028131afdc12a079d9832b1a6277155b74aebdecdc0ab91f3ca6dbe`.

The39-tab AM workbook preserves all38 historical tabs/790,559cells/native
features. Saved XML/raw-route audit, zero formula errors, two mutation/restore
checks and five inspected renders pass. Native Excel was not exercised.
No prototype density/header/directedIRQ/negative/cleanCI/browser/owner/physical
acceptance is claimed; promotion was rejected before those release-only gates.

The useful lesson is the size of the remaining change required. Further small
metadata savings alone do not restore cadence. Next read-only feasibility tests
whether a16-pixel sprite strip plus tile suffix can reduce bear raster work
while keeping every pixel and the four-sprite scanline bound. This is a hypothesis,
not a new implementation or measured frame gain. The earlier four-sprite AE
experiment stays rejected. See `references/bear-rows-result.json` and the issue
handoff; Issue42/39/15/16 remain open and PR43 draft/stacked on41.
