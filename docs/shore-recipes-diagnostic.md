# Exact standing shore-edge player recipes AK

v23 preserves v22 graphics, colors, contacts, source timing, controls and PSG.
It replaces a costly general P0 path only for normal standing-shore states:
sourceY27/X0..23 or84..152, offsetsEB/F0zero, pose0..5/coarse0..1. Other states
retain the original prepared/general paths. X24..83 keeps its original fast
path; X153+ keeps wrap-aware fallback. No new visual compromise.

Source: `295f3308d81bb58273ebde7f1ee8b91d675779b3`.
ROM: `b1a1d10077e778f833cfb4cab233740cf2d705bd5d40c397e5b9c8767f1cadd9`.
4MiB ASCII16; standard-speed MSX1/64KiB RAM/16KiB VRAM/TMS9918/built-in PSG.

## Why this path

v22's worst active bear pictures spend about71,000cycles preparing P0, despite
its much lower average. Normal sourceY27/X<24 falls outside the earlier recipe
proof because of source pattern/color-prefix races. Exact source-derived recipes
retain those races, left clipping, coarse unblank duplication and existing pastel
player palette.154shared16-byte records and25432-byte patterns cover576base
states. Another1,656source-pixel checks prove standingX84..152 may useX22/23
recipes by parity: active rows55..73 have no pattern-prefix or suffix race, color
prefix cutoff<=22, andX<=152 prevents wrap. No captured route state is encoded.

18bytes occupy EFD1..EFE2 inside existing reserved E900..F000 kernel space
(1,745 to1,763 of1,792 bytes occupied). A310-byte bank2 body replaces unreachable
old dirty-description/compare/span bytes after v22 redirected their sole entry.
The actual AJ entry and captureBC53 remain protected. Directory120, records121/
122 and patterns123..126 use retired floe NAME-program tails. Live header116..
118 and igloo/grid-player119 remain untouched, as do all lower14KiB contact
prefixes. No new RAM/VRAM region, mapper size or hardware requirement.

The original P0 cache lookup/miss runs first. Prepared sprites stage32bytes in
dead C500 scratch, then call the original emitter and cache store. At most four
patterns fit the existing six-slot way; no band has over three P0rectangles.
The actual inherited L predicate still determines eligibility and the selected
way at right X. The new path uses that selection; the unchanged cache store
publishes only when its original eligibility permits. Other ways and static
slots remain protected. All publication follows uploads; empty records fallback.

The rejected right-edge prototype used old8-bit3*Xposition math and overflowed
atX87 in the full NTSC route. Corrected code uses16-bit3*X/2+8; the exact failed
source-pixel case and both full TV routes now pass. Rejected binaries and failed
producer attempts remain private. All178parent sources/42sealed roots remain
unchanged, with four additive files/182bound sources. Original mode reproduces
exact v22 SHA b0a3d2...c1e2. Backup:
`codex/backup/42-before-shore-recipes-20261112`.

## Whole-route results versus v22

| Active route / cost | v22 | v23 |
|---|---:|---:|
| Regular NTSC pictures/s |31.2970|31.3564 (+0.19%)|
| Regular PAL pictures/s |29.4768|29.5956 (+0.40%)|
| Bear NTSC pictures/s |25.9404|27.0953 (+4.45%)|
| Bear PAL pictures/s |23.3900|24.2955 (+3.87%)|
| Bear NTSC longest picture gap, ms |66.75|50.10|
| Bear NTSC foreground P95, cycles |123,816|85,694 (−30.79%)|
| Bear PAL foreground P95, cycles |123,810|86,162 (−30.41%)|
| Bear NTSC foreground maximum, cycles |131,650|104,256|
| Bear PAL foreground maximum, cycles |131,426|104,394|
| Regular NTSC foreground maximum, cycles |137,981|127,789|
| Regular PAL foreground maximum, cycles |157,755|138,161|

Bear foreground mean falls78,082→74,384NTSC /79,737→76,148PAL. Sprite/preflight
P95 falls68,131→21,759NTSC and67,886→21,759PAL. These are different sampled
picture populations, not paired component savings. Inclusive helpers are not
added to stage totals. The major value is reducing long preparation outliers.

All26 regular grounded/end-Y landing flags,252NTSC/233PAL consecutive Y runs
and age P95/max remain unchanged: grounded20/26NTSC,15/26PAL; endpoints23/26NTSC,
24/26PAL. Regular P95/max gaps remain50.07/66.78msNTSC,59.81/79.75PAL. Bear P95
remains50.07NTSC/59.81PAL; PAL maximum remains59.84ms. Bear scope is the unchanged
620-step prefix, active195..425 at level4,122X/all eight poses, bounded before
one-player guard630. **Stable29.97/30 across gameplay, original fluidity and
all-level acceptance remain open.**

## Validation and next work

591host tests;2,115source/2,040density/54header scenes;2,115ordered-audio intervals;
18generic+14new actual hardware IRQ boundaries and negative AF2 control pass.
Four clean-source passive replays reproduce all five uninstrumented natural
buffers, with exact source CPU/allRAM, pixels, physical owners and active-page
protection. No passive profiling timeline change is permitted. Exact-source
push/PR CI passes. Independent retirement safety poisons the reclaimed areas
with HALTs and passes all2,115source scenes, plus57,344unchanged contact fields.
Independent24,294calls per ROM (48,588total) cover all160X/both pages/all poses/
reflection/coarse, cold/repeat/postfallback and all three selected ways. Pixels,
full SAT/SGT/cache payloads match the parent exactly; max3P0rectangles/line plus
door<=4.9,254actual AK entries/25,186copies are counted, with exact critical
right coordinates. Native cache/priority/ABI/mapper protection passes.

AK workbook37tabs preserves36historicaltabs/786,599cells/native features. Saved
XML/raw-route audit, zero formula errors, two mutation/restore checks and five
rendered regions pass. Native Excel was not exercised. Browser launch, manual
listening, mobile controls, owner fluidity and physical MSX are separate evidence
classes; no acceptance is inferred from automated proof.

Next targets are remaining world preparation and header/igloo bursts, using full
CPU/gap/landing measurements. Keep42/39/15/16 open and PR43draft/stacked; same
focused issue chat/root sole writer. Read `references/shore-recipes-result.json`
and the v23 release notes for exact artifacts, limits and human tests.
