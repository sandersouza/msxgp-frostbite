# Pixel-identical hybrid bear feasibility AN

Same owner-authorized autonomous Issue42/root sole writer, HEAD e7c5663, public
v24 source48be/ROM4686...55c5be and186sources. AM rejected/archived;56 predecessor
roots immutable. Standard-speed MSX1/64KiB RAM/16KiB VRAM/PSG, no expansions.
Preserve every source mechanic, clock/input/audio and composed pixel. Player-as-
tiles and new palette/shape compromises remain unapproved and outside scope.

## Evidence and selected direction

AM saves only435/443 complete-foreground cycles with no cadence gain. Current
bear WORLD averages35k, bear helper20k. The old AE full-sprite bear remains
rejected. Conservative read-only admission against FINAL complete v24 SATs:
adding two rectangles per bear band (four total) is safe in only1/105 active
NTSC and1/96 PAL pictures; three existing P0 rectangles produce S4=5. Adding
one rectangle per band (two total) is safe in105/105 and96/96. These are sampled
SAT constraints, not exact preflight/pixels/SGT/CPU/ROM proofs.

Investigate a left16-pixel sprite strip plus unchanged right8-pixel tile suffix
of the24x20 bear. Two nonoverlapping16x16 rectangles at y43/44 and y59/60 retain
exact raster pixels51..70/71; reuse only independently verified source pattern
halves. Keep current P0 colors, silhouette, controls and all enemy choices.
Safe initial viewport gate is normalized bearX11..144: x>=24 avoids exposing
pixels20..23 over v19's black NAME column2 at rows8+. Edges and unsupported
states retain full native bear tiles. No visual compromise is authorized here.

## Required offline feasibility gates before runtime work

Derive all512 original pose/reflection/Xphase/coarse descriptors from the sealed
parent, not captured route states. Prove exact combined PGT+SGT raster for both
themes/pages and relevant colors. Check96record aliases may have different crop
cuts; do not assume one cut per record. Crop first suffix column2 by0xFF>>phase
where phase is exact targetX mod8; column3, when present, is unchanged. Padding,
vertical row boundaries, coarse reset, prefix/source raster and reflection all
require independent source comparison.

Prefer reusing original canonical logical pattern IDs for masked8-byte shapes.
If necessary, a bounded synthetic logical namespace may extend at13539..16383
with independently derived originalID/cut patterns and normal kind0 keys. Its
owner oracle must derive pixels from original masks/backgrounds, not just read
candidate tiles. No general renderer may accidentally decode a synthetic ID
through the original contact/asset tree. Existing actor/floe/fixed role and active
page guards must remain strict; no blanket audit exemption.

Measure deduplicated partial tile pool, directory/record/SGT size first. Only
132..141 tails are currently retirement-proven;114, body112 spare and66 directory
padding are hypotheses requiring audit/poison. Protect142..146 occupancy,147/148
resident/P0,149 P0,150 partial contact/I and151+ live contact tree. Keep original
AI records/tiles/body/bulk fallback intact. No ROM resizing/newRAM/VRAM region.

## Proposed integration subject to audit

Render the bear AFTER x_actor/floes complete, using actual final SAT, then append
bear last. This preserves existing enemy choices and sprite priority. Bear rows
6..8 are disjoint from first enemy at80+ and ice at96+, but prove this across all
source/coarse states. Recompute complete original bear descriptor from coherent
F000 snapshot; never read advancing canonical C000 state. Remove only the early
bear call. All dirty, hidden/gameover/level, wrap/color and collision behavior
must retain original fallback. Reconstruct caller-dependent p_w_* scratch needed
by original ai_entry, rather than assuming actor-loop leftovers harmless.

Potential hook: presentation_hud_prepare before its first snapshot LD A,(F03F),
so world/allactors are complete. A wrapper runs the deferred bear, restores
incoming mapper/stack/required registers and executes that original instruction
before continuing HUD+3. Audit unused old w_header EBCA..EC37 (protect w_owner,
w_level,w_save) before any reuse;15free kernel bytes alone are not assumed enough.
Mutable active/page SG Tkeys at E8B8..BA need explicit liveness proof; E8B0..B7
are live enemy clip caches. All initializer mirrors/code hashes stay exact.

SGT slots22/23 page0 and46/47 page1 appear free after P0/enemies; protect static
48..57 and all active-generation patterns. Upload inactive two-pattern64B payload
before publishing group+1 cache keys; new SAT terminator/count stays<=32. Real
S4 admission counts full rectangles including transparent P0 portions; no
flickering/priority degradation. Keep fallback for unsupported viewport, palette,
geometry, metadata, slot or S4 conditions.

## Promotion boundary

Only implement after offline raster/pool/admission/liveness review clears a
concrete layout with credible savings over20k tiles INCLUDING SGT/preflight and
ownership. RED→GREEN meaningful model/bounds tests, independent finite native
proof and all2115source/density/header/audio/IRQ/negative guards. Measure four
complete routes, gaps and all26landings before promotion. Attribute deferred bear
cost separately from HUD while reporting full foreground/ISR costs without double
counting. Reject if no useful complete-picture gain, as AM was rejected.

A useful qualified ROM gets a new versioned prerelease with exact tested ROM,
SHA/source, updated workbook preserving39tabs, WebMSX and concrete human tests.
No all-level/stable30FPS, mobile/owner/listening/hardware acceptance is inferred.
Issue42/39/15/16 stay open; PR43 draft/stacked41. Root sole tracked writer.

## Concrete layout / history strategy for review

Independent4b796e9d...7aa647 proves512 geometries/2048RGB compositions for both
foreground colors1/15, 96record aliases with onecut,148canonical suffixmasks and
80 synthetic patterns13539..13618. Two-slot stage uses3..6 nonempty tiles.
Selected64B record:6synthetic/canonical IDs12B,24final-tileindices48B covering
2themes×2colors×6cells, originalcols/cut/twopad4B.96records6144B. Directory512x2
and naïve16×64SGT1024B share132tail. Records133..135;460final16Btiles7360B in
136..139 (8192capacity);140..141 spare4096B, registry/masks fitunused poolpadding.
Code1142KiB, not a live contact bank. All originalAI fallback resources remain.

Root poison of66BC00padding/114tail/w_headerEBCA..EC37 passes2115source and54header
scenes. Four passive NTSC/PALregular/bear read/write watchpoints find zeroCPUaccess
afterclockstart toE8B8..BF, five rawbuffers unchanged; static indirect-span audit
still required. Reclaimed110B kernel slot can hold mapper-safe wrappers/copies/
SGT/per-cell upload helpers. Protectw_owner/w_level/w_selected/w_save and allP0.

History safety: level<3 earlygate calls originalAI unchanged; headerwrapper then
executes originalHUDentry with minimal overhead. Level>=3 earlygate defers bear;
HUDwrapper runs after finalWORLD, preserving incoming registers/flags/mapper,
then executes originalLD A,(F03F). Deferred active bear context always forces
rows6..8 and exact sorted dirtylist/FC00 view, restores original complete NAME
rows6..8 (col0/31=128, E/D/C from actual four-theme background tables; profile32
all128), then draws hybrid or fullnativefallback on fresh background. This avoids
per-page mode caching and supports SAT-only eligibility changes/no-world-dirty
frames. Only collect rows again when bits were newly added; no other rows erased.
Audit fixed bear-role retirement (no shared ice/actor references in6..8). Always
append hybrid SAT even if descriptor unchanged. Hidden states retain original
skip. Recompute sourcebear fields/F000 and clear geometry memo/i_active before
originalfallback; use resident6100palette rather than bank-changingp_world_color.

Synthetic IDs are allowed only in firstsuffix boundary roles: bank0slots2/6,
bank1slot2, plus64forPAGE1. Keepnormal kind0 and exact bg/color/clip fields.
Auditor derives originalID/cut registry masks, rejects unknown/misplaced IDs and
retains source-frame RGB, owner, activepage, SAT/SGT and all other checks. This
concrete layout is conditional on independent history/ownership review before
runtime construction; no complete-frame gain is implied by feasibility.

## Measured iteration 03

Iteration02 preserves all four source/RGB/owner routes but loses overall cadence;
26.4290 NTSC bear FPS versus27.0953 v24. Therefore it is not deliverable. Preserve
its five source atoms under local source-02. Actual source palettes are day1 and
night15; other combinations fall back to the complete original native bear.

Remove repeated row-program address arithmetic using six precomputed three-byte
far pointers per22-byte record. The first93 records fit2046 bytes in133:B800;
three remaining records occupy66 bytes alongside the114 body and registry. All
352 existing44-byte transactions and their eight tail banks remain unchanged.

When original dirty bits already include rows6,7,8, the prior xh_bg has restored
all three complete NAME rows (none is a covered floe row); early bear drawing is
skipped and all remaining WORLD objects begin below these rows. Reuse this exact
background. Otherwise union all three bits, rebuild the dirty list/FC00 flags,
and explicitly restore all three rows before choosing hybrid or native. This
retains zero-dirty and partial-dirty mode-transition safety without a new cache.

## Final candidate 04 delta

Iteration03 reaches27.7374 bearNTSC FPS (v24 27.0953), foreground mean71979
versus74126 cycles. The earlier64B/per-cell layout above is historical only;
final layout is22B far records and35244B bulk row programs. Offline tile pool is
461 entries; only transactions, directory, SGT and240-byte registry ship. Body114
includes records93..95 and registry. RAM wrappers occupy105 of the retired110B;
existing total reserved kernel occupation remains1777/1792, no new allocation.

After filtering the complete final SAT for rectangles intersecting the bear's
32-line span, a list of at most3 existing rectangles proves every scanline has
at most3 existing sprites plus one bear sprite. Accept immediately in that case.
For4+ overlapping rectangles retain the exact existing critical-scanline test.
Duplicates count individually, capacity remains at most31 plus terminator,
transparent rectangles count, and existing actors remain ahead of the bear.

## Final candidate 05 delta

04 saves a few cycles but does not improve complete-picture cadence over03.
The common finalSAT has four overlapping rectangles with tops35,51,51,51.
For exactly four filtered rectangles, compute min/max starts relative to the
same47-position filter origin. Four16-line intervals share a scanline iff their
start span is at most15. A span>=16 therefore certifies existing concurrency<=3
and admits one bear rectangle per line immediately. Relative coordinates retain
soundness across raw-Y wrap. ExactlyM4 only; M>4 keeps the full critical-line
algorithm, and M4/span15 keeps it too. No sprite choices, priorities or graphics
change. Independent review explicitly covers span15/16/17 and Y-wrap adversaries.
