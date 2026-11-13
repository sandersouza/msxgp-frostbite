# Native renderer feasibility checkpoint

The owner authorized replacing the renderer architecture and resuming GitHub.
The contract is original mechanics and preserved presentation on standard MSX1,
not preservation of the existing renderer. Issue #39 remains open: speed has
not been restored. M-C remains the private owner-test baseline.

## Measured traversal experiment

N-B selects enemy row geometry and metadata once, then traverses the row
directly. It retains the exact publisher, ice overlap composition, gameplay,
audio and scheduling. The 576-byte patch uses resident mapper-restoring
wrappers and certified unreachable atlas space in bank 7. Initial build-a's
bank-2 placement failed the occupied-byte guard before producing a ROM.

| Active route measurement | M-C NTSC | N-B NTSC | M-C PAL | N-B PAL |
|---|---:|---:|---:|---:|
| Source updates/s | 31.1855 | 31.6490 | 32.4926 | 33.1387 |
| Mean complete busy cycles | 111564 | 109629 | 126631 | 124414 |
| Mean world cycles (included above) | 44776 | 42841 | 52204 | 49987 |
| N-B complete busy P95 | — | 242518 | — | 264434 |
| N-B active maximum | — | 336157 | — | 364479 |

Cadence improves only 1.49% NTSC / 1.99% PAL. The same adjacent-state active
predicate selects 1008/843 intervals. Whole-route maximum remains 489112 cycles.
The 1920 synthetic density scenes reduce preparation plus RPC mean by 3.01%;
480 three-copy scenes improve 3.62%, while unchanged repeated scenes are equal.
These synthetic scenes are not a natural highest-level or paced-FPS claim.

Automated equivalence: 2115 complete source scenes and 1920 density scenes are
byte-identical to M-C. Paced NTSC/PAL compare 2253/1886 presentations, all three
full VRAM snapshots per frame and every one of 2254 source CPU/all-128-RAM
checkpoints per route. VDP traffic and every non-world stage's cycles are equal.
This establishes the measured routes, not all-level, listening, human, physical
hardware or VBlank-only acceptance. Bypassed primitive counters do not represent
eliminated publisher work; whole-stage and whole-frame costs decide the result.

Decision: preserve N-B as internal research, not a solution or new human-test
release. It does not justify asking the owner to test another marginal ROM.

## Why the architecture must change further

M-C's NTSC active mean is 111564 cycles against a 59736-cycle video frame.
World is 44776, source work 22059 and sprites 15207; other work is about 29522.
Even zero-cost world rendering leaves about 66788 cycles. Optimizing only the
enemy loop or ice path cannot establish the complete budget. Transitions and
worst-frame bursts also require attention.

The next implementation should retain published ice patterns across NAME-page
generations instead of tying their residency to a page-private pool. A software
model pins both the displayed and next requested tiles and includes color in
each key. It retains exact vertical phases and the clipped column's full strip.

| Model, slots per bank | NTSC semantic misses | PAL semantic misses |
|---|---:|---:|
| Existing page-private policy | 6852 | 6803 |
| Shared residency, 56 | 2756 (−59.78%) | 2714 (−60.11%) |
| Shared residency, 64 | 2559 (−62.65%) | 2523 (−62.91%) |

These are **offline semantic misses, not measured Z80 cycles, transfer bytes or
FPS**. The model excludes runtime lookup/eviction cost and complete enemy/fused/
static allocation. Its peak pinned union is 30/36 slots in banks 1/2 on these
routes, not a universal bound. It differs from the earlier roughly 10% model,
which shared only within a generation. The full permanent atlas still has
capacity pressure and is not assumed to fit.

Start with the existing 64 ice slots per bank and stable physical ownership;
protect actual displayed references across generation changes. Implement a
bounded direct lookup and prepared row NAME mappings. Replace the current
page-derived key recovery and independently validate actual physical ownership.
Do not disable a guard merely because the old checker assumes private pages.
Then measure the full frame, including metadata, allocation and commit costs;
replace remaining generic stages as the budget requires. Player-as-tiles stays
on hold. No graphics concessions or dropped gameplay updates are assumed.

## Reproduction and identities

Private root: `outputs/presentation/native-bands-n/`. Inputs and raw captures
remain ignored. Public aggregate: `references/native-band-feasibility.json`.

- M-C ROM: `0e43bd16a5219a2d2548580e581ee5e26c7f440e715c18d96e07dbe033351ad0`.
- N-B ROM: `cd90ef510ba8c52ca3792d7803c4308d211d2855b700e39cc8a2cadeddc1a751`.
- Build-C hardens input authentication and produces the exact same ROM bytes.
  Build-B source snapshots remain in `sources-build-b/`.
- Builder pins ROM, metadata, M-C symbols, I symbols and allocation proof before
  assembly. Recorded patches reproduce the candidate from M-C.
- `scripts/presentation_band_report.py --root outputs/presentation/native-bands-n`
  reproduces paired aggregates using the preserved private M-C analyzer and F
  profiler. Family/frame counts, identities and capture sizes must agree.
- `scripts/presentation_residency_probe.py --out <new-path>` reproduces the host
  model from the verified original and sealed M-C captures.
- All 112 entries in the existing M-C seal were freshly verified unchanged.

Independent review checked patch reconstruction, mapper ABI, allocation,
full matrix/density equality and profiler breakpoint non-aliasing. Its build
input, capture-format and paired-report guard findings were addressed with
synthetic regression checks. Existing M workbook is preserved; these new
measurements are recorded in the report/aggregate rather than overwriting it.
