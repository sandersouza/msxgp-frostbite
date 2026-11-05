# Native floe transactions diagnostic AA

AA continues Issue #42 from the exact v0.0.14 control. Its largest average
foreground component was WORLD (37,063 cycles per active picture), dominated
by floes (23,038). AA removes repeated floe setup and mapper work while keeping
the same packets, NAME rows, physical owners, colors and coherent snapshots.
The source simulation, input/audio timing and player/world alignment are unchanged.

## Measured whole-game result

These are complete-route automated emulator measurements on standard-speed MSX1,
64 KiB RAM / 16 KiB VRAM, built-in PSG. Display throughput is separate from the
approximately 59.92 Hz original simulation clock. PAL uses an expanded RAM slot.

| Active metric (NTSC unless stated) | Z / v0.0.14 | AA |
|---|---:|---:|
| Complete pictures/s | 20.1127 | 21.4600 |
| PAL complete pictures/s | 19.0708 | 20.1950 |
| Mean picture gap | 49.720 ms | 46.598 ms |
| P95 picture gap | 66.785 ms | 66.753 ms |
| Longest picture gap | 100.097 ms | 83.441 ms |
| Complete foreground preparation | 86,984 cycles | 80,142 cycles |
| WORLD stage | 37,063 cycles | 31,312 cycles |
| Complete active ISR | 21,933 cycles | 21,986 cycles |
| Jump update states presented | 251/390 | 266/390 |
| Distinct jump Y positions presented | 162/234 | 170/234 |
| Consecutive jump Y runs presented | 188/286 | 196/286 |
| Grounded landings presented | 14/26 | 9/26 |
| Endpoint Y presented | 19/26 | 20/26 |
| Entirely unpresented animation-pose runs | 3/84 | 2/84 |

NTSC complete-picture throughput improves 6.70% (PAL 5.90%); observed mean foreground cost
falls 7.87%. P95 still spans four fields; maximum falls from six to five. Grounded
landing coverage regresses even though total jump coverage improves: a shorter
preparation changes which source instants are sampled. No grounded state is
removed from simulation, but this visible limitation must remain in owner tests.
Both unpresented AA pose runs last one source step; Z also misses a four-step run.
This is a useful diagnostic improvement, not stable 30 FPS or fluidity acceptance.

Passive profiling leaves all five natural buffers byte-identical. Stage means
use 365 active AA pictures versus 342 Z, so their differences are not paired
component savings. Complete ISR uses the same 1,008 active source intervals and
includes the 21-cycle EI/RETI tail. The slight ISR increase reflects more visible
commits; AA does not change ISR code. Two NTSC fields leave about 75,500 cycles
outside ISR, versus 80,142 foreground: a 4,642-cycle mean deficit remains, before
tail and commit constraints. This capacity arithmetic is not a 30 FPS guarantee.

The AA workbook preserves all 25 Z sheets and adds this result, corrected cost
attribution and explicit limitations. The fresh detailed baseline scopes CGT
fills to the floe call: a shared helper also serves 12 actor fills. Old inclusive
floe helper attribution included those calls; old whole-frame totals are valid.
The correction does not rewrite historical sheets.

## Allocation and runtime contract

| Bytes, inclusive | Use |
|---|---|
| RAM F43D–F5D1 / ROM147:B83D–B9D1 | Replaces old floe transaction; main body ends F5B5, then padding |
| ROM0:60B6–60FB | Resident publication helper |
| ROM0:60FC–60FF | Padding |
| ROM0:6100–61FF | Exact 256-byte clone of parent color table at ROM1:B5A0–B69F |
| ROM0:6200–6205 | Direct dirty-row lookup helper |
| ROM0:6206–6209 | Four existing lane Y origins |
| ROM0:620A–6211 | Four existing PGT addresses |

No new RAM or VRAM. `x_name_row` at F5D2 and every later WORLD byte remain exact.
Existing FC00–FC17 flags come from the final dirty union. Signed root correction
preserves `(x-plane) mod 160` for canonical X 0..159 and plane −8..7. Packet bank,
fine offset, both page-specific NAME programs and two-row dirty gates are exact.
The renderer derives addresses once and stays mapped to its packet while resident
code publishes PGT/CGT and owner metadata. Full 128-byte color initialization on
a cache miss is retained. Owner records and tuple identity become valid only
after required writes complete. VDP stream spacing and interrupt-safe address
wrappers are unchanged.

The resident region reclaims the retired typed-header continuation 60B6–6248,
after the live direct header and before the live footer at 6249. As in Z, generic
constructors for kinds 16–18 are no longer a callable API. Dormant dispatch edges
exist, but only the direct header publishes those kinds; it never invokes those
constructors. World, igloo and footer do not request them. New producers must
re-audit this invariant. The rejected NAME experiment is not combined with AA.

`p_w_color` remains defined even on an early return. Unlike Z, a transparent or
clean floe need not map bank 1: the loop is resident/RAM; the next useful floe
maps its packet and each actor invokes the unchanged bank 1 color helper.
All mapper writes use `t_mapper`, including its IRQ-restored shadow. Persistent
tuples E5C0–E5DF, records C1D1–C1F0, colors C1F1–C1F8, packet scratch and error
results retain their contracts. Old-key reconstruction/fusion is unchanged.

Dead renderer scratch is not an all 64 KiB RAM-equivalence promise. Old floe
`p_tl_y/p_tl_delta/p_tf_row` writes are retired. Family/tile/bank scratch is
initialized by subsequent active actor/footer consumers. `p_w_name` is now a
temporary row base; actor eligibility overwrites its alias before use and tile
traversal calls `p_fast_cell`. `x_world` overwrites return registers/flags before
using them. Canonical source CPU and all 128 original RAM bytes remain the oracle.

## Alternatives and Seaquest reference

The quarantined Seaquest renderer shares patterns among three copies within one
lane and still publishes four independent NAME bands. Frostbite already uses
fine phase plus coarse three-column rotation. Its lane pairs cannot simply alias:
52-pixel separation changes vertical phase by four; source X, activation color
and SCREEN2 banks are independently meaningful. Seaquest evidence is guidance,
never Frostbite acceptance proof.

A separate circular NAME-row layout passed 51,200 finite byte comparisons but
was rejected before ROM construction. Its 692 unique repeated pairs need 88,576
bytes; the proposed contiguous allocation is unavailable. Deduplication of 756
individual 30-byte rows still needs 45,360 bytes before pointers versus 44,288
allocated. This rejects that proposed layout, not every future relocation or
encoding. There is no measured NAME-experiment speed claim.

Intermediate B reduced complete foreground to 80,830 cycles and reached 21.341
pictures/s. C/AA adds the exact resident color table and reaches 21.460. Isolated
gains are not additive. Only selected AA becomes a testable release; private
experiments and all v0.0.14 evidence remain immutable local controls.

## Reproduction and qualification

The maintained builder verifies the exact v0.0.14 ROM and all 145 parent source
hashes, then assembles new maintained source. It never reads the private
candidate ROM. Original-derived generated data remains ignored. It binds 147
source files and rejects a changed ROM hash or an existing output directory.

```sh
.venv/bin/python scripts/build_floe_transactions.py \
  --base outputs/presentation/core-cadence-z/build-final \
  --out outputs/presentation/floe-transactions-aa/NEW-BUILD
.venv/bin/python scripts/presentation_native_check.py BUILD OUT ntsc 2252
.venv/bin/python scripts/presentation_native_check.py BUILD OUT pal 2252
.venv/bin/python scripts/presentation_native_check.py BUILD OUT matrix 2115
.venv/bin/python scripts/presentation_native_check.py BUILD OUT density 1920
.venv/bin/python scripts/presentation_native_check.py BUILD OUT header 54
.venv/bin/python scripts/presentation_audio_check.py --build-dir BUILD --out OUT
.venv/bin/python scripts/presentation_native_clipping.py BUILD NEW-REPORT.json
```

Use `presentation_fixed_clock_boundaries.py` for nine NTSC and nine expanded-PAL
boundaries and its AF2 negative control. `presentation_cadence_report.py` and
`presentation_jump_coverage.py` distinguish complete-picture gaps from source
steps. Independent review reconstructs the entire ROM and audits allocation,
mapper/IRQ, persistent publication and retired scratch consumers.

Qualification passes 557 original-free host tests, 2,115 source scenes, 1,920
full-density scenes, 54 header transitions, 18 directed IRQ boundaries plus a
rejected AF2 negative control, and 10,560 clipping cases. Audio matches 3,499
ordered source writes and 2,472 PSG writes over 2,115 intervals. The natural
NTSC/PAL routes compare 4,507 canonical CPU/all-RAM checkpoints and 1,829
coherent pictures with exact pixels/owners, zero late VBlanks and zero canonical
source writes. All measurements remain bounded, automated evidence.

Selected ROM SHA-256:
`d28c68590a27004d6624af3d1ecb9d80dc422ed3f4f4241caed2df278d1a5db0`.
Release source/validation attachments identify final clean-build qualification,
CI and delivery evidence. Automated replay, manual observation, owner feedback
and physical hardware are separate evidence classes.

## Owner test and next work

Compare against v0.0.14 on the same standard-speed MSX1 profile at 100%, ASCII16,
64 KiB RAM / 16 KiB VRAM. Tap F1 to start; arrows/joystick and Space/fire.
Walk left/right, repeat down/up jumps and steer in the air. Pay particular
attention to whether the instant of landing looks skipped. Ride/reverse floes,
activate their colors, pass enemies/fish near edges and observe HUD, igloo and
death transitions. Expect identical graphics, contact rules, durations and
control response, with somewhat more intermediate images. Uneven motion remains.
Report release, machine, TV mode and a short recording with audio if possible.

Next work remains the largest WORLD/foreground costs and long-gap cases, with
landing coverage retained as a metric. Issue #42, parent #39 and final timing/game
acceptance issues #15/#16 stay open. No all-level, manual listening, owner-fluidity
or physical MSX1 acceptance is claimed.
