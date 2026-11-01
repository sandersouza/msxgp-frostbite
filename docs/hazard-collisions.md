# Original hazard and shore collision acquisition

Issue #12 extends the original-clock boundary used by the native MSX1 port.
The source ROM and unchanged original execution remain authoritative; a VDP
collision flag or synthetic display geometry cannot supply gameplay contacts.

## Boundary and current evidence

The original kernel clears shore collisions at F1FC and reads CXPPMM at F244.
It clears each row at F307, reads odd object windows at F331 and combines
CXPPMM/CXM1P in even floe windows at F3BE/F3C0. The shore sample updates ED
only when negative, preserving the source sticky lifetime.

The separate local observer applies `tools/stella-hazard.patch` after the
frozen floe patch on pinned Stella 7.0. It adds the nine-window `hazardProbe`
command without changing the source ROM, original CPU or actual TIA latches.
The old command, binary and frozen captures remain available independently.
Upstream Stella copyright and GPL-2.0 terms apply to these observation patches.

The strict 674-byte local record contains nine 58-byte literal-view truth
windows (B0..B7, then shore), 128 RAM bytes, logical A/X/Y/P/SP and 19 glyph
bytes. Each window retains 228 player views for each electrical high bit.
The two channels are separate; source row low bits must remain 07.

Initial exploratory verification passes 9,444 controlled source cases with all
228 actual views, all 256 source Y bytes, 32 source animation pointers, NUSIZ
0..3, reflection and edge positions. Every row sample and complete visible
CPU/RAM reduction matches. Thirty-two unchanged-Stella phase comparisons and
64 old-floe protocol comparisons pass. A first count-zero/object-X0 case
produces the real B7 ghost contact; count zero is not an invented empty mask.

This is controlled source research. The complete geometry catalog, native
all-channel target, crowded natural routes, timing and release are not yet
accepted. A failed first capture exceeded the unchanged 30-second process
watchdog; its partial bytes remain failed exploration. The successful checker
uses the same cases in independent batches of at most 1,024.

## Reproduction

Keep the existing source ROM, environments, frozen evidence and legacy intact.
Use fresh ignored output directories; full states and original-derived tables
are never public source or release assets.

```sh
.venv/bin/python -B scripts/stella_hazard.py build
.venv/bin/python -B scripts/hazard_observer_check.py --out outputs/hazards/observer-check-a
.venv/bin/python -B -m unittest discover -s tests
```

The observer builder uses a fresh private directory and verifies the pinned
revision and both patches. The checker records every helper, backend, capsule,
raw input/result/log and independent comparison identity. Canonical evidence
requires committed, frozen helpers and complete domain receipts; an exploratory
success must not be relabeled as a canonical producer.

## Representation and target gates

The implementation must preserve native source state, RNG calls, collision
priority, fish segment/reward ordering, push/attachment and bear behavior.
Any translation, clock-wave factorization or compression must be proved with
complete original observations before use. Rejected floe raster/convolution
models do not become valid hazard models by assumption.

The existing 4 MiB ASCII16 build has only 232 cycles of worst measured PAL
margin. A candidate must fit its measured cartridge layout and pass fresh
full-density and true paced NTSC/PAL checks with actual acquisition work,
29-cycle VDP data spacing, four sprite slots, VBlank commit, device/stack/heap
guards and every required source step. No new testable MSX ROM exists yet.
