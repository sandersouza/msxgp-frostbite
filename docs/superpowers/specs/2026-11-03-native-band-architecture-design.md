# Native band renderer feasibility

Issue: #39. Owner authorized replacing the architecture on 2026-11-03 and
resuming GitHub when useful. This is an executable feasibility step, not a
promise that one replacement will restore original cadence.

## Contract

Keep the Atari 2600 logic, input order, collisions and audio as the behavioral
authority. Preserve M-C's pixels, colors, viewport and actors for this first
prototype. No sprite conversion, player-as-tiles, frame dropping or turbo.
Target standard MSX1, 64 KiB RAM, 16 KiB VRAM and built-in PSG. The implementation
may replace all rendering structures; the owner never required preserving them.

M-C is the immutable comparison artifact, SHA-256
0e43bd16a5219a2d2548580e581ee5e26c7f440e715c18d96e07dbe033351ad0.
Its measured active NTSC mean is 111564 cycles versus a 59736-cycle frame.
World averages 44776, source 22059 and sprite stage 15207. World-only work cannot
close the total gap even if it became free. Whole-frame and tail costs decide
progress; do not report a faster helper as a restored game.

## Approaches and choice

1. Continue local optimizations inside the generic compositor: low integration
   risk, but recent diminishing gains do not establish a path to the budget.
2. Specialized per-band transactions, prepared data and fixed destinations:
   selected for the first prototype. Seaquest demonstrates this representation;
   Frostbite-specific overlap, vertical phases and page ownership still require
   their own proofs. Reuse finite assets and the original logic, not its costly
   generic cell execution architecture.
3. Different graphics mode, sprites or visual simplification: possible later
   alternatives, but not required or assumed here. Material visual concessions
   need a concrete comparison with the owner first.

The owner approved autonomous execution of the hardware-focused direction.
Detailed implementation choices here are engineering decisions, not additional
owner requirements. No repeated approval round is needed for this reversible
prototype.

## First executable replacement

Replace the enemy primitive walker with a private Z80 band walker. Select the
fixed physical role and metadata origin once per tile row. Traverse the bounded
two/three-column geometry directly; share roles across repeated copies. Retain
the exact existing publisher initially so this isolates traversal cost and
permits byte-identical complete VRAM comparisons. Retain the exact overlap
combiner for cells containing ice. This is the first slice of a new path, not
the complete proposed architecture.

Use verified unreachable atlas space in bank 7 for the new walker and a small
resident trampoline. Every helper that changes the mapped bank must restore bank 7 before
returning into the walker. Preserve public routine addresses and baseline files.
Explicitly bound scratch usage; no writes into gameplay state or guard areas.
Reject the build if padding, expected parent bytes or ROM identity differ.

Then measure whether eliminating repeated geometry/context/metadata work can
meet an allocated band budget. Separate measured costs from hypothetical
budgets for the remaining ice, player, dirty-state and UI replacements. Any
future complete architecture must include all those stages and worst bursts.
Never add inclusive helper costs to their enclosing stage.

## Evidence and delivery

Run original-source graphics scenes, paired input-only NTSC/PAL routes and
synthetic dense/wrap/reflection/coarse cases. Compare original CPU/all-RAM
chains, complete captures, traffic and all non-world stages against M-C.
Test bank restoration and partial dirty rows; preserve source and active-page
ownership. Do not weaken a checker to make the candidate pass.

A measured failure is a valid feasibility result and stays archived. A useful
human-test candidate requires independent review and the standing versioned
release process. Failed internal builds are not releases or recommended ROMs.
Keep current and historical ROMs intact. Publish only implementation, aggregate
results and documentation; original ROMs, traces and derived tables stay ignored.

The successor decisions are driven by measured remaining costs, with a total
frame budget and headroom. No stable cadence, all-level, raster or physical
hardware claim follows from a passing image comparison.
