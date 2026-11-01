# Original hazard and shore collision acquisition

Issue #12 extends the original-clock boundary used by the native MSX1 port.
The source ROM and unchanged original execution remain authoritative; a VDP
collision flag or synthetic display geometry cannot supply gameplay contacts.

## Sealed automated acceptance

The current candidate is source `e83569dfde46f9bb6f39ea05817d6e3204333a54`,
ROM SHA-256 `37beb4d58bfc6566ba064ff59d48118ce6bc70655f92dcc9695cb534a88bfd93`,
4,194,304 bytes, ASCII16. The clean immutable package is
`outputs/hazards/issue12-final-e/`; its public compact result is
[hazard-result.json](../references/hazard-result.json).

All 14,828 actual visible phases and 652 controlled full-native phases pass.
An original-free actual-Z80 matrix checks all 65,536 combinations of shift,
operand mode, value, observed N/Z/C flags, input carry and overflow. The new
lowering omits only outputs proved dead by the existing contextual liveness;
RAM80..FF shifts preserve A directly and all hardware/indexed aliases retain
their original path. Transfer/comparison operand and IY paths are unchanged.
The shared baseline generator and published 0.0.4 ROM remain unchanged.

All four input-only original interaction routes and independent full-state
replays pass in **32 route × NTSC/PAL × layout × width combinations**: 26,816
complete CPU/all-128-RAM checkpoints and 24,604 completed pixel-checked frames.
No active canonical/contact injection or skipped source interval is accepted.
The worst route/view costs are:

| Route | Source checkpoints per run | NTSC busiest cycles | PAL busiest cycles |
| --- | ---: | ---: | ---: |
| Bear chase / death / recovery | 702 | 40,817 | 61,051 |
| Bear refuge | 1,235 | 45,116 | 66,865 |
| Fish and all delayed awards | 812 | 47,558 | 70,719 |
| Threat attachment / push / death / recovery | 603 | 45,370 | 67,655 |

Fifteen dense/cache/toggle/mixed-count stress modes add 3,600 completed frames,
peaking at 49,545/64,802 NTSC/PAL cycles. Budgets remain 59,736/71,364;
the minimum named PAL margin is 645. All pixels, minimum 29-cycle VRAM spacing,
four sprite slots, VBlank commits, heap/stack guards, slots and interrupts pass.
All eleven intentional faults are rejected by their actual raw witnesses.
Maximum visible/control-phase costs are 6,679/33,563 cycles.

The packager independently rechecked the complete source catalogs and observer,
exact native fixture/CPU streams, every saved natural frame/state, original
replays, copied ROM/build/profile identities, named matrix coverage and negative
witnesses before sealing. Full original/private evidence stays local; only
ROM/build/compact-validation/SHA files belong in the prerelease.

The first alternate-view PAL test failed at 74,816 cycles. Compact flag lowering
reduced that exact complete original route/view to 70,719, then the clean ROM
received the entire expanded matrix and all other gates again. Earlier
candidates/seals below are historical and are not publication candidates.
Independent review passed with no blocking findings. PR35 is integrated, the
clean merged-main rebuild is byte-identical, and all four published release
assets were downloaded and verified; see the
[delivery receipt](../references/hazard-delivery.json). See
[human test instructions](releases/v0.0.5-hazards.md); original presentation,
progression/whole-game and manual/physical acceptance remain later work.

[The reproducible local checklist](hazard-checklist.md) lists the build,
source replay, whole-native, all-view paced and stress commands. They require
the ignored original/capture inputs; public CI never downloads those inputs.

## Earlier candidate C (superseded)

The clean candidate at `025bc66683d612aeb88b817e28b316bcab723769` is a
4,194,304-byte ASCII16 ROM, SHA-256
`cd2ca94637d409c1d31afda0262e44b1ea422809afdc871aa1b54038f8e4cac2`.
It passes 14,828 actual original-visible CPU/all-128-RAM cases and 652 controlled
whole-native-phase cases. The latter include both players, every row/kind,
grounded/airborne contact, three seeds/six stages, existing fish at F7=0C,
bear stage2/3, water/temperature causes and every 8-bit RNG seed. Maximum visible
phase cost is 6,679 cycles; the largest controlled full phase is 36,275 cycles.

Four cold input-only original routes and independent complete-state replays
also pass in the actual paced MSX ROM for both clock families:

| Route | Source checkpoints | NTSC completed frames / busiest cycles | PAL completed frames / busiest cycles |
| --- | ---: | ---: | ---: |
| Bear chase / death / recovery | 702 | 701 / 41,762 | 587 / 62,909 |
| Bear refuge and blocked sweep | 1,235 | 1,234 / 44,794 | 1,033 / 67,942 |
| Fish and complete reward envelope | 812 | 811 / 45,842 | 679 / 70,846 |
| Threat attachment / push / death / recovery | 603 | 602 / 45,818 | 504 / 69,364 |

Fish collection at checkpoint771 removes one segment and the complete twenty
ten-point awards finish at798. Threat attachment/push/recovery occur at
304/306/602. Every checkpoint compares all logical CPU registers and all128RAM;
every completed frame checks pixels, its own latest state and uninterrupted
source cadence. Active canonical RAM/contact injections are zero. Cold source
preparation and restore journals remain explicit and independently replayed.

All fifteen dense/cache/layout/toggle stress modes pass, including both
NTSC/PAL mixed seeds with actual source NUSIZ0/1/2/3. Each benchmark seeds
canonical state once and compares every subsequent complete phase continuously;
its dense visual overlay is separately labeled. Maximum crowded NTSC/PAL work
is 51,321/68,018 cycles. Source budgets remain 59,736/71,364 cycles; the tightest
accepted named-route PAL margin is 518. Every checked VRAM interval is at
least29 cycles, occupancy stays within four sprites, commits stay in VBlank,
and guards, slots and interrupt state pass. All eleven intentional mutations
are detected at their intended comparison: row collision, RNG, row priority,
shore sticky lifetime, VRAM spacing, fifth sprite, heap guard, canonical state,
pixel, floe contact and cache state.

An earlier candidate failed the same PAL fish route at71,404 cycles. The repair
clears all odd latches and dispatches the single live26-Y band proved by every
literal-view source profile. It changes no lookup value, RNG or source step.
The complete geometry, controlled cases and all named paced routes were rerun
on the changed ROM. Original instructions/seeded controlled fixtures and natural
input-only routes remain distinct. The generated native core source text is
byte-identical to the published0.0.4 rebuild; resident-call relocation changes
assembled bank bytes. The published0.0.4 ROM remains byte-identical.

Immutable packaging, independent review and release integration are pending
at this checkpoint. Synthetic graphics/HUD and no audio remain diagnostic
limitations. Manual-emulator and physical MSX acceptance require owner feedback;
whole-game/progression acceptance belongs to later issues.

## Boundary and historical source research

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

That initial checkpoint was controlled source research, before the complete
catalog/native/paced acceptance above. A failed first capture exceeded the unchanged 30-second process
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

## Complete lookup and boundary checkpoint

The clean `ce8cbe9606ca639f4efcd5f5c67e6c5e7af28142` engineering build
contains the actual eight row channels and sticky shore acquisition. Its
4,194,304-byte ASCII16 image has SHA-256
`c50df909b6ddba21b7b463c0db9fbd8791eae912aba4eacf70a1dcccbd54f08f`.
This is an internal verification checkpoint; publication requires the remaining
mechanics and whole-frame gates.

The complete components contain 25,132,800 exceptional-X cells, 4,954,950
ordinary single-copy cells, 8,294,400 shore cells and 3,203,200 independently
executed actual-copy alias cells. Together with the frozen 8,704,000 floe
cells, the compiler audits 50,289,350 source observations. It verifies every
declared raw input/result/log/receipt/profile and their committed producer,
backend and preparation identities before packing.

All 10,716 records, 59,246 blocks and 104,849 row roots remain lossless.
An independent physical-bank reader checks 16,776,480 leaf queries across
their unique source rows. The image uses 239 contact banks and 256 cartridge
banks; resident/assets/native usage is 12,416/13,088/9,216 bytes respectively.
The first complete layout exceeded the ASCII16 bank limit and was rejected.
The accepted layout removes repeated zero-Y profile pointers and ordinary
player directories already served by the proven resident common profiles.
It does not omit live contacts, either electrical channel or raw evidence.

Every source row component is zero outside normalized Y36..61 within the
captured domain; shore truth is zero outside Y12..46. Native early returns
and compact profile indices use the same generated bounds. Compilation
rejects omitting any live or shadow-only Y. Ordinary profiles at every
PX25..151 are byte-identical, admitting 198 bytes of resident common pointers;
PX9..24 retains its actual directory, and the 17 exceptional positions retain
all 264 modes.

For NUSIZ0..3, pinned Stella's draw-counter decodes use single-width copies
at offsets 0, 16 and 32 modulo 160, independently of pattern bits. The
ordinary representation unions actual single-copy truth at those positions;
it does not compute overlap from a raster. Its independent actual-copy matrix
covers every ordinary player X, object X, vertical window and count, with
rotating source shapes/reflections and all 228 literal player views. This
matrix is not the Cartesian product of every shape with every count; the
pattern-independent counter implementation supplies that structural argument.
Hidden-clock exceptional positions are never factored this way. Primary code:
[draw-counter decodes](https://github.com/stella-emu/stella/blob/d55b1aec0d067a4c901a6dcdf81cb8f579685659/src/emucore/tia/DrawCounterDecodes.cxx),
[player clocks](https://github.com/stella-emu/stella/blob/d55b1aec0d067a4c901a6dcdf81cb8f579685659/src/emucore/tia/Player.hxx).

The actual ROM matches the complete original visible CPU/all-128-RAM result
in 14,828 controlled cases, including every exceptional position/mode, all
literal views, all source Y values, different row data, blanking, headers and
sticky carry-over. No odd/shore sample is neutralized. Maximum measured visible
phase cost is 6,990 cycles. The original-free Z80 unit cartridge passes 576
checks; maximum decoder/generic/common/copy-distance costs are
805/1,295/1,135/93 cycles including RPC call/return overhead.

Real-key cold replays also match 702 original bear-chase checkpoints and 1,235
refuge checkpoints. Chase contact/push/death/active-recovery occur at
362/363/426/693, including the two-player reserve total 7→6 and turn swap.
The refuge holds X9 with bear X15 and reserve3 throughout its 768-interval
safe wait. The corrected test harness selects canonical C047 (source C7);
an earlier C007 typo was caught by the first nonneutral refuge input. The ROM
bytes were unchanged by that harness correction. These are unpaced automated
replays; crowded timing, remaining fish/threat/reward validation and manual or
physical acceptance remain separate.

The synthetic presenter now maps original NUSIZ0/1/2/3 to 1/2/2/3 copies and
16/16/32/16 spacing independently of row-direction flags. Original graphics,
clipping, HUD and audio are still later presentation work. The published
0.0.4 ROM rebuild remains byte-identical, and every input consumed by its clean
42261b7 rebuild is unchanged at this checkpoint.
