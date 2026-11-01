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

A cached top-object command restores the complete original prefix plus all
observation sidecars and executes the unchanged F263→F335 window. Its 78-byte
record retains the full two-channel truth, actual B7 sample and glyph. A
2,560-case comparison spanning all 160 player X positions matches complete
phase execution byte for byte. A further 384 literal-view invariance links
across four rows, header changes and other-window changes pass. Backend
receipts bind the exact binary to the pinned revision and additive patches.

Unchanged-Stella snapshots show the final odd sample at horizontal counter 93
when source Y is 0..18, and 57 otherwise. Thus the final graphic line is only
partially sampled; a whole-image overlap invents contacts. A clock-horizon
research formula matches 2,080,272 literal-view checks at sampled ordinary X
positions 64/151, but fails at the edges. It is not an accepted substitute for
original-clock acquisition. Edge truth and complete domain/capacity proof remain
required before native use.

## Frozen source foundation

The final foundation checker at clean source
`fe4814081bb7ecadb45a9dec048f5bd81d284d91` passes 9,476 controlled cases,
768 literal-view invariance links, 2,560 object-window and 2,880 shore-window
full/ROI pairs, 32 unchanged-Stella phases and 64 old-protocol comparisons.
The domain contains 33 object pointers: 32 animated pointers plus cold-cleared
A3=0. The full shape/reflection/NUSIZ mode list has 264 entries and requires
an index wider than eight bits. All eight bear animation indices retain their
source pointer aliases.

The shore ROI stops at F246 and records the fresh accumulator sample; old
sticky ED is not a substitute for that read. Source/header/row/prefix helpers
and backend identities are frozen in the local receipts. The full host suite
has 221 passing tests at this source checkpoint.

Capacity prototypes reconstruct 13,004,800 existing floe and declared partial
edge cells through 2,654,560 distinct leaf queries without differences. Typed
32-byte pools, 16-bit IDs and sparse roots occupy 58 banks for that combined
corpus. Each record scalarizes bit6 only after validating its 228 identical
bits; bit6 may still differ between Y samples. View-dependent channels reject
this representation. The three-X edge experiment is partial and excludes the
newly identified cold pointer; it is never complete-domain acceptance.

The simplified bear overlap model is rejected because it diverges even at
ordinary player X. Shore acquisition retains complete original-clock truth.
Final complete-domain capacity and actual Z80 access costs are gates of native
integration, followed by whole-frame timing. No new testable ROM is implied by
the source foundation or the size prototypes.

## Reproduction

## Native lookup groundwork

The component collector freezes its complete source helper closure and uses at
most four bounded workers. Edge truth keeps all 264 modes at all 17 exceptional
player positions; ordinary single-copy, actual-copy alias and shore components
are separate domains. A 34,650-case ordinary-X smoke capture passes a second
audit of every raw case, observation marker, result, log and profile. Partial
or exploratory components cannot become complete native build inputs.

The compiler rejects substituted preparation capsules, missing receipt ranges
and rehashed profiles/fixtures which disagree with original raw execution.
Source-only acquisition may overlap unrelated native edits: the root producer
and consumed helper hashes remain frozen, while each batch honestly retains
its observed global commit/dirty facts. This is not whole-ROM clean-producer
acceptance; that still requires a fresh committed build and capture.

The native compact reader passes 464 actual standard-MSX1 Z80 unit checks in an
original-free synthetic fixture cartridge: 288 sparse/slot/bank boundary cases,
16 profile-directory cases including mode 264, and all 160 copy distances.
The first native distance run failed at distance 8 because a compare carry was
mistakenly returned as a hit. The corrected full check passes, including IX/IY,
stack and interrupt preservation. The fixture is not a playable game version.

Full-domain native ROM generation, ordinary-copy alias proof, complete original
CPU/RAM phase equality, natural routes, footprint and crowded frame timing are
still pending. Existing releases remain the human-testable artifacts.

```sh
.venv/bin/python -B scripts/hazard_decoder_check.py --out outputs/hazards/decoder-fixture-new
```

## Source reproduction

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
