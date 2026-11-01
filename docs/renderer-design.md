# Renderer feasibility design — issue8

The approved project design chooses a measured SCREEN2 hypothesis before native
mechanics and original assets. This diagnostic uses newly written synthetic masks
and a small font. It is not a playable or original-graphics release. The exact
[presentation ABI/allocation](../references/renderer-contract.json) is separate
from the read-only canonical128-byte source state and collision inputs.

Three viable costs were considered. All-hardware sprites cannot represent three
ice copies, three threats, three Bailey color layers and the bear on one line:
ten candidate slots exceed four. Full background raster regeneration would transfer
up to6144pattern bytes before colors/names, exceeding a frame at conservative
VRAM spacing. The selected hybrid keeps ice/threat rows in small background caches
and Bailey/bear in hardware sprites. The three Bailey colors plus bear require at
most four slots, including crowded landings. Two vertical pieces have disjoint
16-line boxes, so splitting a19-pixel synthetic actor does not double occupancy.

Source X0..159 maps to display8+floor(3X/2), with clipping at the240-pixel viewport.
Both canonical parity and display phase are retained. Three ice copies use logical
spacing32; threat fixtures cover0..3 copies and spacing16/32. The second row layout
deliberately crosses the SCREEN2 bank boundary at Y128. These synthetic coordinates
are workload fixtures, not a replacement for original TIA collision geometry.
Right-edge player masks are preclipped; bear input is bounded0..151. Future original
assets must explicitly establish their required masks/bounds and remeasure.

The initial unaligned layout was rejected: adjacent threat/ice bands shared one
name cell, and the independent pixel check caught the overwrite. Its generic
implementation cost roughly97k cycles including the synthetic step. The selected
normal layout aligns bands to eight-pixel rows, shifting them at most four display
pixels from the investigated26-pixel-spacing proposal. The stress layout isolates
one bank-crossing band without a neighboring name-cell conflict. This is an
explicit presentation compromise, not a source-state or collision change. Issue9
must establish the original-to-presentation Y mapping and assess fidelity; this
diagnostic does not claim original geometry/pixel equivalence.

Pattern/color caches alternate tile IDs under an inactive name page. Preparing
the next frame must preserve the visible page; VBlank commits the name page, SAT
and backdrop. Static patterns/names are initialized on both pages. Full color,
igloo and layout transition costs are measured rather than assuming dirty writes
are free. The VDP never supplies gameplay collision results.
Each layout has its own two frame caches, so vertical padding stays zero when
layouts alternate. Local band IDs are shared only between different SCREEN2 banks;
the crossing lower fragment and the last band's upper fragment occupy distinct
halves. Synthetic alias tests and actual pixels validate these boundaries.

VRAM uses0000–17FF patterns,1800/1C00 name pages,1B00 SAT,2000–37FF colors and
3800–3FFF sprite patterns:16000bytes,384bytes unallocated. Sprite patterns consume
the full2048-byte table (ten player parity/clipping variants and two bear parities).
More colors/animations or different actor bounds need a revised allocation.

Precomputed phase/vertical-shift tables alone occupy20480ROM bytes; a16KiB cartridge
cannot hold this strategy. Start with plain32KiB, explicitly map cartridge page2
through BIOS slot handling, measure the used bytes and defer a mapper until native
code/assets show it is required. System RAM remains64KiB with no expansion.

The source's measured19912 Atari CPU cycles correspond to59736 cycles at the
nominal3:1 CPU ratio. Benchmark scheduling exercises59736-cycle NTSC and71364-cycle
PAL presentations with a rational accumulator, preserving every required step and
allowing at most two. Each step charges a measured10k-cycle synthetic workload.
This is a headroom reservation, not translated gameplay performance; source
clock alignment, real core/input/audio and full-game latency remain later gates.

The harness is implemented fresh. Audited ideas from the ignored Seaquest copy
are breakpoint elapsed-time measurement, per-port IO spacing, visible-page checks
and RAM/stack canaries. Its machine/boot addresses, original assets and previous
success reports are not reused. Existing Frostbite isolated C-BIOS provisioning
and verified assembler are reused without changing the user's environment.

TI's original manual specifies four sprites per line and mode-dependent CPU
access windows. Use a minimum29 standard MSX cycles between VRAM accesses, verify
the actual IO stream and openMSX's too-fast callback, and keep physical testing
separate. [TI data manual, sections2.1/2.4.5](https://computers.baffa.tec.br/pages/datasheet/TMS9918A_TMS9928A_TMS9929A_Video_Display_Processors_Data_Manual_Nov82.pdf),
[openMSX debugger commands](https://openmsx.org/manual/commands.html).
