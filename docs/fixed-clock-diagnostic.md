# Independent source clock diagnostic

Issue [#42](https://github.com/sandersouza/msxgp-frostbite/issues/42) now has an
MSX1 interrupt-driven source clock and a separate coherent-picture renderer.
This is a useful architecture diagnostic, not acceptance of original-speed
presentation. The CPU still cannot draw every requested picture on time.

Published as [v0.0.10-fixed-clock-diagnostic](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.10-fixed-clock-diagnostic),
from clean source `854dcf462b56274f60f1f0cf978bc487d124e57a`.
[Validation](../references/fixed-clock-result.json) binds all selected receipts
and raw artifacts. [Publication](../references/fixed-clock-delivery.json) records
the exact remote tag and byte-identical fresh downloads of all four attachments.

## Measured clocks

| Measured rate | NTSC | PAL |
| --- | ---: | ---: |
| Original logical steps / second, whole route | 59.92275 | 59.92467 |
| Complete pictures / second, whole route | 19.23420 | 16.94241 |
| Complete pictures / second, active intervals only | 9.79790 | 9.69859 |
| Worst interrupt service, MSX CPU cycles | 29,810 | 53,268 |
| Worst elapsed preparation, including interrupts | 617,301 | 604,848 |
| Observed stack use out of 128 bytes | 64 | 62 |

These are input-only openMSX routes on standard3.579545MHz64KiB MSX1 profiles,
with16KiB TMS9918-family VRAM and built-in PSG. PAL also uses RAM in secondary
slot2 of expanded primary3. Its original1/2-step accumulator remains unchanged.
Both routes have zero late VBlanks. Frame counters/times are sampled at interrupt
entry, before the variable-length PAL service. IRQ costs overlap preparation
elapsed costs; adding them would count the same CPU time twice.

An active picture interval requires C6=E7=F1=0 at **every original source point**
between its two snapshots. It excludes intervals crossing death/attract. These
picture rates must not be compared as if they were Q's33.6350/35.2938 active
logical-step rates. Q ties each logical step to a completed preparation; T does
not. T restores original simulation timing in the measured route, while its
coarser visible motion and snapshot age remain a substantial gameplay limitation.

## Implementation and fidelity

The unchanged native scheduler, source step, input acquisition and ordered PSG
updates run in an IM1 VDP interrupt. Main rendering reads an atomic128-byte
snapshot, not concurrently changing source RAM. It prepares the whole inactive
picture; a VBlank commit publishes the SAT and NAME page before the next source
work. At most one picture is admitted per two VBlanks. Actual drawing is slower.
No original logical step is intentionally skipped.

All sprites, colors, ice, enemy objects, player and left black mask are retained.
The slot takeover uses built-in RAM for the IM1 vector. A resident mapper tracker
records the intended bank before changing the cartridge. IRQ saves/restores main,
alternate and index registers and bank. VDP address pairs and source snapshot
copy are protected by DI. Diagnostic F3/F4 polling occurs between preparations;
original F1/F2 and controller input remain within source steps.

Code occupies384bytes in E900..EA7F; private state is E880..E8FF, snapshot
F000..F07F, guard F080..F2FF and stack F300..F37F. Old O shared-cache storage at
F000 is absent from the selected Q-derived renderer. No RAM expansion is used.

## Reproduction and proof boundaries

`native_pipeline_build.py` now reproduces F through I/J/K/L/M/contact14/P/Q with
public, original-free producers. The supplied reference ROM and generated contact
catalogs remain private build inputs. Reproduced Q is byte-identical to sealed Q-E.
The listing inventory identifies47actual mapper instructions and123renderer
snapshot operands; it excludes source/audio accesses, assets and overwritten code.

The diagnostic ROM hash is
`29b4588b62d4b44a88401c691512d415b26bdaf559198d889730ee2b49763b1e`.
`build_fixed_clock.py` authenticates Q, all inherited allocations, original source
data, patch extents and RAM image. `presentation_prepared_check.py` retains the
2115source-scene and1920density-scene gates, with the clock disabled for isolated
renderer tests. `presentation_fixed_clock_probe.py` drives real key pins, compares
every original CPU/all128RAM checkpoint, and verifies each committed picture
against the exact original snapshot. It also audits active VRAM, physical owners,
VDP access spacing, slot mapping, immutable code, redzone and observed stack use.

`presentation_fixed_clock_boundaries.py` additionally parks the CPU in a separate
diagnostic loop until a real hardware VBlank is pending, then restores the saved
PC/IFF at nine boundaries: before/after mapper shadow, each VDP low-address byte,
each data-stream byte and before/during/after snapshot copy. Deferred IRQs must
wait for the protected section. The test compares main/alternate/index registers,
I, SP, return PC, bank and unchanged VRAM/snapshot after RETI, while retaining the
source and picture oracles. Its intentionally delayed picture timings are **not**
performance evidence. A deliberate AF2 corruption must fail its register oracle.

Final qualification passes545host tests, both exact-source original-free CI
runs,2115source scenes,1920density scenes,4507natural CPU/allRAM checkpoints,
1355natural pictures, eighteen directed boundary cases and the AF2 negative
control. Clean-source replays reproduce all D measurement buffers byte-for-byte.
M/N/O/P/Q seals remain unchanged (112/147/220/467/434files). The T workbook
retains238600Qcells, formulas, styles, panes, widths and its native chart; its
new formulas, sensitivity, independent aggregates, XML and views were checked.
Native Excel itself was not exercised.

The single independent review found no demonstrated kernel blocker, requested
this directed test, and retracted a preliminary F3/F4 mixed-picture hypothesis:
inactive render.asm was cited initially; the active path reads those flags only
for dirty identity. Moving that polling is an optional coherence cleanup.
Directed testing also corrected a test assumption: an IRQ may legitimately
advance live source RAM after snapshot completion and before its caller resumes.
Atomic copy equality is checked inside DI; later pixels are compared with their
recorded original source index, not with newer live state.

R's header/igloo/player-way experiment remains preserved and rejected as a human
candidate: only1.03% NTSC/0.73% PAL over Q. M/N/O/P/Q are immutable controls.
Original-time drawing, unseen levels/timing tails, manual listening, alternating
controller testing and physical hardware remain open. The next work is to reduce
the repeated full-preparation cost when source snapshots are several ticks apart,
especially cache replacement/ice and sprite tails. This diagnostic does not close
#39, #42, #15 or #16.
