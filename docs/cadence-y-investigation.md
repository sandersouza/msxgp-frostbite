# Cadence investigation after X feedback

The owner reports improvement in v0.0.13, but gameplay is still far from smooth.
This is partial positive feedback, not acceptance. Issue #42 remains In progress.
X is the immutable public control; no Y component is selected for owner delivery.

## Whole-game decisions

Same input-only NTSC route, original source clock and coherent whole-scene
publication. Rates refer to active complete pictures, not source updates.

| Isolated component | Active pictures/s | Long-gap result | Decision |
|---|---:|---|---|
| Published X | 18.22138 | P95 83.44 ms; maximum 116.82 ms | Immutable control |
| Direct static SAT tail | 18.44197 | P95 unchanged; maximum about 116.8 ms | Not selected |
| Empty player-segment shortcut | 18.22138 | Whole-route cadence unchanged | Retain privately; no standalone delivery |
| Direct header half-columns | 18.80360 | P95 83.41 ms; maximum 100.16 ms | Retain privately; no standalone delivery |

The static-tail candidate increases completely unseen pose runs from 3 to 4.
The player shortcut saves 1,502.72 cycles on average across 200 directed cold
complete-frame cases, but does not change natural-route cadence. A proposed
player min/max scan was rejected before ROM construction: all 569 observed
nonempty shapes accept the first cut, so an extra scan would target rare work.

The direct header lowers its exclusive active mean from 6,465.86 to 3,298.06 cycles
and its maximum from 51,028 to 24,508. Those means describe different committed
snapshot populations, not paired-frame savings. Presented jump updates rise
from 229 to 239 of 390; grounded landings fall from 10 to 9 of 26 and endpoint-Y
coverage from 18 to 14. This is not a uniformly better motion result or a fluidity fix.
The components have not been combined; their gains must not be added.

## Complete budget and next target

Passive WORLD and source profiles preserve all five natural X buffers exactly.
WORLD averages 39,232.94 inclusive cycles per active picture, of which floes
consume 24,773.08 (63.1%). The floe cost includes PGT/CGT transfers, NAME copies
and repeated transaction setup; these nested rows are not additive.

The complete active NTSC interrupt service averages 23,688.77 cycles per field,
including the empirically verified 21-cycle EI/RETI tail. Of that, the translated
core excluding input/audio bodies costs 14,211.15; visible/contact preparation
4,764.27; input 1,937.84; and audio 571.00. Remaining wrappers, commit and IRQ work
complete the disjoint total. The two input labels alias one routine and were
deduplicated; both real sampling calls per source step remain accounted for.

Two NTSC fields provide about 72,094.46 cycles outside interrupt service, while
the active renderer requires 95,808.40. The mean deficit is 23,713.94 cycles per
picture. This is a budget equation, not an achievable-speedup claim; interrupt
acknowledge and worst cases still matter. Small isolated patches cannot close it.

The next bounded investigation is a passive block profile inside `core_F476`,
then a measured, proof-backed lowering of the dominant executed patterns while
continuing to reduce native floe transactions. The core already has flag/range
analysis, carry fusion, compact shifts and a guarded write-loop summary; generic
binary arithmetic helpers are not used by the active generated code. Do not
optimize unused helpers, slow the source clock, omit input/audio sampling, or
publish a player pose from a different scene snapshot.

The existing minimum-two-field publication gate caps presentation at 29.96137 FPS
NTSC and 25.07949 FPS PAL, independently of source execution speed. This follow-up
does not change that policy or claim a 30 FPS PAL result.

## Verification and limits

- Static tail: full NTSC source/pixel/owner/guard route; no PAL or broad matrix.
- Player shortcut: 2,115 source scenes, 1,920 density scenes, 2,253 CPU/all-RAM route
  checkpoints, 200 paired cold scenes and 524,288 finite selector checks passed.
- Header: 54 directed header/palette/blank cases, 2,253 CPU/all-RAM checkpoints,
  922 coherent pictures and finite raw-selector/pixel proofs passed. A passive
  profile reproduces its five natural buffers. PAL/general matrix remain pending.
- WORLD/source: passive X profiles with byte-identical CPU/RAM, captures, owners,
  IRQ and picture buffers. Source analysis reads verified existing expanded-PAL
  evidence; it does not claim a new PAL launch.

All new evidence is automated emulator or finite host analysis. No new human,
audio-listening or physical-hardware acceptance is implied. The header prototype
reuses retired generic-header code; canonical integration must preserve the
sole-direct-header-producer invariant or relocate it, because dormant typed-header
dispatch edges remain. It is not a replacement for the callable generic API.

Local producer/receipt identities are bound in
[the investigation reference](../references/cadence-y-investigation.json).
All earlier ROMs and sealed evidence remain unchanged. No runtime source change
or new GitHub ROM release results from this investigation.

The Y research workbook adds only two sheets to X, preserving all 21 existing
sheets and 761,109 cells, styles, formulas and native features. New calculations,
input-change recalculation, raw aggregates, saved-file preservation and six
rendered regions were checked. Native Excel was not exercised. The exact workbook
path and SHA256 are recorded in the investigation reference.
