# Bear sprites experiment AE

The owner authorized a bear-sprite experiment against v0.0.17, with exact
graphics/mechanics, full-game measurements and publication only if worthwhile.
Neither tested implementation earns promotion. **v0.0.17 remains the public
ROM. No runtime source is changed and no new human-test release is published.**

## What was tested

The bear's 24x20 target raster needs four 16x16 sprites. Two adjacent vertical
bands begin eight rows above its raster, keeping the lower rectangles before
the first enemy band. Existing player, door, mask and logo retain priority.
Unsupported wrap/position/pose, SAT exhaustion or more than four whole sprite
rectangles on a scanline retain the original tile path. No flicker rotation,
actor deletion, physics adjustment or asynchronous player motion is introduced.

Two independent page sets use SGT slots22/23/58/59 and46/47/60/61. Sixteen
prepared pose/reflection groups use2048ROM bytes; their parity invariance is
checked over16horizontal phases and two coarse-Y states (512comparisons) against
the existing independent geometry compiler. The mapper-safe upload/world gates
extend existing clock RAM. Everything is an ignored, unqualified private spike;
all154bound v17 sources and the v17 ROM remain unchanged.

A tries sprites unconditionally. B first clears its selection flag and checks
the original level: below3 it uses the original preflight/tile renderer directly.
At level3 or later it uses A's exact sprite eligibility/fallback. Both retain
the original dirty union and conservative enemy preflight, including its SAT
capacity threshold. These implementation choices limit the conclusions.

## Whole-game measurements

Standard-speed MSX1/64KiB/16KiB/TMS9918/PSG. PAL also uses expanded-slot RAM.
The complete2252-step input route has level0, bearpose0 and bearX140 throughout;
it does not measure a moving bear. Original source timing remains about59.92steps/s.

| Active complete pictures/s | v17 | A unconditional | B level gate |
|---|---:|---:|---:|
| NTSC |25.900928|24.690540 (-4.673%)|25.841656 (-0.229%)|
| PAL |23.122575|22.088392 (-4.473%)|23.122577 (effectively unchanged)|

A's observed full foreground rises69,756→74,172cycles NTSC and74,907→79,268PAL.
The sprite/preflight phase rises about3121/3419cycles per active picture over
different committed populations; this is not paired isolated CPU overhead.
A's entry call includes the existing enemy preflight and averages5114/5238cycles
per active picture. Do not add inclusive helper costs to the foreground total.
The existing bear primitive costs only520/560cycles per active picture on this
route. Eliminating that measured call cannot offset the observed extra work;
this is not an upper bound on every possible bear/dirty/NAME redesign.

### Actual moving-bear input route

The sealed clean-start bear-chase route supplies a second live-clock test.
The unchanged one-player guard rejects its later state at source630 in all
four initial700-step attempts. Those failures are preserved. The accepted
test is an explicitly bounded620-step prefix, with no source RAM/CPU injections.
Only the source-route directory changes in a private copy of the existing probe;
the CPU/all-RAM, graphics, ownership, active-page and clock oracles are unchanged.

The active interval is source195..425, level4, with122bearX values and all8poses.
The before/after source CPU traces are byte-identical.

| Active bear-chase pictures/s | v17 | B level gate | Change |
|---|---:|---:|---:|
| NTSC |14.205704|13.748278|-3.220%|
| PAL |13.703336|13.773877|+0.515%|

The gate avoids most first-stage overhead but does not produce a consistent
live-game win while the bear is active. Keeping the current public ROM is the
supported decision. A faster isolated scene is not a full-game performance gain.

## Controlled-scene signal and limitations

Both variants pass the2115original-source scene matrix with zero pixel
differences. Identical source rows/order permit paired whole-prepare comparisons.
For A, mean prepare work falls20.99% across the full matrix. The653nonblanked
level>=3 rows fall36.29% (129884→82754cycles), but218of653rows are slower.
This predicate indicates bear-enabled source state, not actual sprite admission
or literal visibility in every row. It combines523controlled fixtures and130
natural-window-derived snapshots injected by the existing scene harness. The
253levels,8poses and160X values are marginal coverage, not their Cartesian product.
Only435unique(level,pose,X) tuples occur. The130natural-window snapshots alone
improve12.99% in aggregate, with38faster and92slower rows.

B's corresponding paired means fall21.24% overall and36.22% in the same653-row
subset. All2115 B images also match exactly. Its live-clock tests above still
do not establish a consistent gameplay gain.

The controlled harness disables the live source/IRQ clock. Its timing measures
preparation plus the fixed CALL harness, excluding live IRQ/commit/wait work;
it must not be labeled gameplay FPS. It demonstrates useful savings when the
sprite path is admitted, while the live routes expose the cost of checks,
fallback and competition for sprite/SAT capacity. A future substantially different
admission/dirty design is not disproved by these two private implementations.

Natural standard routes preserve source CPU/all128RAM, exact coherent pixels,
physical owners and the active page. All passive accepted profiles must reproduce
all five natural buffers. Directed audio/density/IRQ release qualification,
owner/controller/listening/physical acceptance and all-level speed testing are
not claimed for these rejected prototypes. The first two A-control profiler
attempts failed from a Tcl channel-name collision; only the corrected -02 runs
are performance evidence. No old receipt or sealed directory is rewritten.

Raw producers, ROMs and results remain under ignored
`outputs/presentation/bear-ae-research/`; independent review under `bear-ae-review/`.
See `references/bear-sprites-result.json` and the AE performance workbook.

## Visual changes with greater potential — analysis only

The v17 NTSC mean foreground is69756cycles; WORLD alone is26010cycles (about37%).
Foreground P95 is123363cycles, far above the mean. Reducing occasional expensive
composition matters more for smooth cadence than another tiny average saving.
The following proposals are not implemented, benchmarked or approved adaptations.

| Proposal | Visible change | Why it may help | Main validation need |
|---|---|---|---|
| Align the eight sea bands to eight-pixel tile rows | Slightly adjust vertical spacing; use24-pixel pitch instead of26 | Eight-row enemy art and seven-row ice can occupy separate complete tile rows, avoiding split/fused cells | Consistently transform all actor/jump positions; retain exact logical collision, input and source timing |
| Reduce Bailey to two palette layers | Merge the pastel hat into the skin palette; keep gray torso | Fewer overlapping sprite layers/patterns and more room for enemy sprites | Exact poses, priorities, dense rows and actual whole-game gain |
| Replace the black sprite mask with aligned border/clipping | Small left-edge presentation change | Free one sprite per sea scanline and seven SAT entries | Hide waiting/wrapped actors correctly; maintain required visible geometry/contact cues |

My first choice is the band layout. For ordinary unshifted frames, one concrete
proposal moves enemy anchors153/127/101/75 to152/128/104/80 and ice anchors
167/141/115/89 to168/144/120/96: at most7target pixels. This keeps colors,
shapes and actor counts. It also removes the inherited one-pixel coarse display
shift from the proposed layout. A continuous, consistently applied presentation
mapping must keep Bailey's feet visually aligned with the same logical ice
contacts; simply moving the ice while leaving Bailey unchanged is not acceptable.

If needed after measuring that layout, test two-color Bailey and border clipping
separately. Neither losing enemies/poses nor changing jump duration, collision
windows or game speed is an acceptable performance shortcut. Simplifying the
already small aurora/static-HUD work is lower priority. No proposed adaptation
has a promised FPS gain or proves original-fluidity acceptance.
