# Immutable white-ice atlas — Issue42

The owner authorizes autonomous pursuit of29.97/30NTSC with original mechanics,
colors and artwork, using item3/v19 as reversible baseline. No further questions
are needed for this internal representation change. Root remains sole writer.

Choose a certified partial atlas, rather than an oversized all-context atlas:
white color15, source spacing delta8/index1 has61 unique8-byte patterns. Add the
zero pattern, assign62 immutable IDs144..159 and204..249 in SCREEN2 thirds1/2.
Footer IDs160..203 are live and must remain untouched. Other colors/deltas use
v19 exact dynamic packets. Both pages share immutable atlas bytes; NAME writes
remain confined to the inactive page and dirty ice rows12/15/18/21.

Compile16 phase0 NAME programs from source packets, retaining original root
rotation. Upload atlas once after original static initialization. Retired packet
tail bank65:B800..BFFF holds code/data; contact decoder lower14KiB unchanged.
Bootstrap/runtime mapper bridges fit26 retired RAM bytesF5B8..F5D1. No extra RAM,
no expansion beyond existing16KiBVRAM, no CPU/input/audio clock changes. Keep
v19's165 source files and published artifacts unchanged. P0 remains multicolor.

Prove atlas pixels independently, both table thirds, both pages, every phase,
white/blue transitions, alternate delta fallback, footer, IRQ and cold/cache.
Existing ownership audit may receive a shadow NAME view only AFTER validating
registered atlas IDs/patterns/colors/placement; actual pixel/source/active-page
checks remain unchanged. Unregistered high IDs retain old footer guards.

Measure full NTSC/PAL routes,26landings, inclusive foreground and complete ISR;
compare whole-scene FPS/gaps, never local-cycle savings alone. Qualify useful
builds with source/density/header/audio/IRQ/rebuild/CI and independent review.
Update workbook without losing33historical tabs. Publish next free prerelease
with exact ROM/source/hash, human tests and verified WebMSX link. Rollback is
unchanged v19 ROM26260606...6ac9. No all-level/physical acceptance inferred.
