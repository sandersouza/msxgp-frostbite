# Immutable white-ice diagnostic AH

The owner accepted v18's gameplay and delegated item3/further performance work
while away. v19 replaced the left sprite mask with a four-pixel-wider tile border.
AH retains that exact presentation and changes only internal ice representation.

Runtime source: `665cbdf4393fca63fe33299dca35442aa8fabce8`.
ROM SHA256: `c036c3d960da3be4331df6afbb168bc5037777d47be9f4892a16ff6f5d4e43ac`.
Standard-speed MSX1,64KiB RAM/16KiB VRAM,TMS9918-family VDP,built-in PSG;
4MiB ASCII16 ROM. Original source simulation/input/audio clock stays unchanged.

## Representation and rollback

White color15/delta8 spacing has61 distinct8-byte patterns; zero adds the62nd.
Boot uploads immutable PGT/CGT into IDs144..159 and204..249 of SCREEN2 thirds1/2.
These occupy1,984 formerly unused bytes within existing16KiB VRAM. Live footer
IDs160..203, bank0 artwork, sprites and dynamic slots remain untouched. Both NAME
pages reference the same immutable patterns. Sixteen source-packet-derived NAME
programs retain original phase/root rotation. Blue ice, other spacing and water
retain v19's complete original dynamic fallback. No new RAM allocation.

Retired packet tail65:B800..BFFF holds1,255bytes of code/data; lower14KiB contact
payload remains unchanged. Two mapper bridges occupy24 of26 retired zero bytes
F5B8..F5D1. Original static initialization runs before atlas boot publication.
Atlas fast paths leave original tuple/owner/color metadata untouched, allowing
exact later fallback. IRQ context/mapper restoration remains the original one.

All165v19 bound source files remain unchanged; five additive files bring the
closure to170. `build_ice_atlas.py --mode original` reproduces exact v19 ROM
`26260606e1ecbdeed0a8c0d3ae7ef4eb37658341da3a0ab02cd52ac8a5286ac9`.
Local rollback tag:`codex/backup/42-before-ice-atlas-20261112`.
All files in27 sealed predecessor evidence roots were reverified unchanged.

## Whole-route results

| Active route | v19 | AH | Change |
|---|---:|---:|---:|
| Regular NTSC complete pictures/s |28.9237|30.4355|+5.23%|
| Regular PAL complete pictures/s |26.2082|28.0505|+7.03%|
| NTSC foreground mean, cycles |60,254|56,073|−6.94%|
| PAL foreground mean, cycles |63,693|58,332|−8.42%|
| NTSC WORLD mean, cycles |20,440|16,868|−17.47%|
| PAL WORLD mean, cycles |22,173|17,938|−19.10%|
| NTSC grounded landings /26 |17|20|+3|
| PAL grounded landings /26 |13|14|+1|
| NTSC endpoint Y /26 |25|23|−2|
| PAL endpoint Y /26 |22|24|+2|
| NTSC consecutive Y runs /286 |232|248|+16|
| PAL consecutive Y runs /286 |221|229|+8|

The regular route is level0; 30.44 is its mean, not constant cadence or all-level
performance. NTSC P95/max gaps remain50.07/83.44ms; PAL59.81/79.75ms. Grounded
landings lose arcs3/16NTSC and23PAL; endpointY loses6/16NTSC. First-post-landing
age P95 remains3NTSC/4PAL; maximum5NTSC/4PAL. Source states/contact mechanics do
not change, but presentation can still miss a brief state. ISR mean rises0.18%
NTSC/0.22%PAL over identical source-index sets. Stage picture populations differ;
these are observed costs, not paired component savings.

The separate clean-start620step bear prefix reaches15.0453NTSC(+1.75%) and
15.3333PAL(+9.82%). Its active level4 window has122Xvalues/all8poses; the unchanged
one-player guard ends broader valid coverage before630. This is not all-level
acceptance. A passive NTSC bear profile reproduces all five buffers and measures
138,852foreground cycles/picture,89,525WORLD,74,124inclusive generic bear-tile
cost. This is the next substantial target; the previously rejected sprite
experiment is preserved and will not be promoted from local cycle claims.

## Verification and limits

583host tests;2115original-source/2040density/54header scenes;2115ordered-audio
intervals(3499source/2472PSGwrites). Full regular NTSC/PAL routes compare original
CPU/all128RAM, exact v19 pixels, both physical NAME pages, owners and active-page
protection. Final clean-source runs reproduce all five measured buffers.
18generic and10atlas-specific real VDP IRQ boundaries pass; deliberate AF2
corruption is rejected. Negative-control evidence is separate from positive
atlas ownership audits. Exact-source push/PR CI passes.

Independent review rebuilds exact ROM/170source closure and original rollback;
6144actual Z80 cases cover both pages/all4lanes/all160roots white→blue→white and
all16phases/all10deltas. All1984individual atlas-byte corruptions are rejected;
8192contact14fields remain identical, including speculativeB800read. Footer,
SGT, active-page tables/names and original owner tuples are protected. The owner
auditor receives shadow NAME only after actual immutable bytes/positions are
validated; actual source/pixel/active-page checks are never shadowed.

AH workbook34tabs preserves all33AGtabs/780419cells/styles/native features;
independent raw-route/XML audit, zero formula errors, two mutation/restore checks
and five rendered regions pass. Native Excel was not exercised. No manual
listening, mobile-control, physical MSX, all-level or owner-fluidity acceptance.

Read `references/ice-atlas-result.json` and the v20 release notes. All new proof
is under ignored `outputs/presentation/ice-atlas-ah{,-research,-review}/` and
workbook output`-AH`. Issue42/39/15/16 remain open; PR43 remains draft/stacked41.
