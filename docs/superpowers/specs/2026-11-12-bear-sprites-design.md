# Bear sprites experiment AE

The owner authorized an isolated bear-sprite test against v0.0.17, full-route
measurement, an updated workbook and publication only if worthwhile. Graphics,
source mechanics, input/audio timing and coherent pictures remain exact.
Visual compromises are analysis only and must not enter this experiment.

Use four 16x16 sprites: two columns and two vertically adjacent bands starting
eight rows above the bear's 20-row raster. This keeps the lower rectangles
before the first enemy band. Reject wrapped/clipped X, invalid pose, full SAT or
any scanline exceeding four full rectangles; retain the original tile path.
The existing player, door, mask and logo have priority before the bear.

Precompile all 16 bear groups and two horizontal parities from the supplied
ROM. Two page-specific sets of four unused SGT slots protect the active scene.
Per-page pattern keys avoid repeated uploads. A scoped world gate omits only
the bear tile constructor when the exact sprite path was selected. Initially
retain the original dirty union and conservative enemy preflight: measure the
real resulting cost rather than assume savings from removed construction.

Allocation proposal: the 20-byte resident gap after AD and before the footer
holds bank bridges; a small extension to the existing clock RAM payload holds
mapper-safe upload and world gates; helper uses the remaining bank119 tail.
Pattern data may use only a certified retired decoder region. Every producer
must verify prior bytes and preserve all 154 v17 source files. Stop the experiment
if safe allocation or exact graphics cannot be demonstrated.

The second isolated variant adds a level>=3 gate, clearing the current selection
before every decision. It is assessed separately; it does not replace A's evidence.
Add a clean-start live bear-chase prefix, bounded before that route exits the
unchanged one-player contract. Keep controlled-scene CPU costs separate from FPS.

Gate: compare complete NTSC/PAL input routes, gaps, landings, foreground and
full ISR with v17. If cadence is worse or tradeoffs are unjustified, preserve
the rejected experiment, update the workbook and keep v17 as the public ROM.
Only a worthwhile candidate proceeds to the complete density/audio/IRQ/review,
clean-source rebuild and exact-asset release gates.
