# Core and header cadence diagnostic Z

The owner reports improvement in X, but movement remains far from smooth. Z
combines exact source-core summaries with direct header columns, a cheaper
player selector and cached static SAT emission. It reduces complete-picture
gaps; it does **not** establish original fluidity or a stable 30 FPS display.
Player and world remain one coherent source snapshot. No simulation step,
collision, input sampling point, actor, color or viewport element is removed.

## Complete-route measurements

Standard-speed MSX1, 64 KiB RAM / 16 KiB VRAM, built-in PSG; same original input
route. PAL includes an expanded RAM slot. These are automated emulator results.

| Active metric | X / v0.0.13 | Z |
|---|---:|---:|
| NTSC complete pictures/s | 18.2214 | 20.1127 |
| PAL complete pictures/s | 17.2158 | 19.0708 |
| NTSC mean picture gap | 54.88 ms | 49.72 ms |
| NTSC P95 picture gap | 83.44 ms | 66.79 ms |
| NTSC longest picture gap | 116.82 ms | 100.10 ms |
| Complete foreground preparation | 95,808 cycles | 86,984 cycles |
| Complete ISR per active source step | 23,689 cycles | 21,933 cycles |
| Core excluding input/audio | 14,211 cycles | 12,379 cycles |
| NTSC jump update states presented | 229/390 | 251/390 |
| NTSC distinct jump Y positions presented | 152/234 | 162/234 |
| NTSC consecutive jump Y runs presented | 173/286 | 188/286 |
| NTSC grounded landings presented | 10/26 | 14/26 |
| PAL jump update states presented | 213/390 | 241/390 |

Complete-picture cadence improves 10.38% NTSC and 10.78% PAL. Foreground cost
falls 9.21%; complete active ISR cost falls 7.42%. Input/audio/contact costs are
unchanged. Each of the 26 complete original jumps has 15 vertical updates, nine
distinct Y positions and 11 Y runs. Z presents 9.65 updates per jump on average
in NTSC; three of 84 animation-pose runs still go entirely unpresented.
The source clock remains approximately 59.92 steps/s in both video families.

The passive profile leaves all five natural buffers byte-identical. Foreground
stage means compare different committed-picture populations of the same route
(309 X versus 342 Z); their differences are not isolated component savings.
The ISR comparison covers the same 1,008 active source steps and includes the
21-cycle EI/RETI tail. P95 is the observed-order statistic, not interpolation.
Inclusive helper costs must not be added to the disjoint stage ledger.

Two NTSC fields now leave about 75,606 cycles outside the ISR, versus 86,984
for foreground work: an 11,378-cycle mean deficit remains. This arithmetic is
neither a measured candidate gain nor a sufficient tail/commit guarantee.
The measured world stage remains the largest foreground component at 37,063
cycles; further work must reduce complete preparations and their worst cases.

## Runtime changes and allocation certificate

All six components were separately explored, then measured together. The small
standalone Y gains were insufficient for delivery; combining them with exact
source-core lowering changes both throughput and long gaps. Isolated percentage
gains are not additive.

| Component | Allocation and contract |
|---|---|
| Guarded effect summary | ROM2:9709–978F; only FEB8_rF850, index below 56; rejected guards jump to unchanged same-depth rF859 before RAM/V writes |
| Four-lane ice loop | ROM2:8FD9–9006 and 9A24–9A60; exact normalization, V/carry/NZ and both original source return-stack writes |
| Four-lane actor selector | ROM2:8C42–8CC6; shares the counter triangle/table read; reuses core_lhs/core_rhs at C604/C605 inside the non-reentrant source phase |
| Direct header | ROM0:5DD3–60B5; lookup RAM FD00–FD8A / ROM146:BE00–BE8A; existing E620–E64A scratch and metadata |
| Header dictionary | 5,328 bytes at ROM116:B800–BFFF,117:B800–BFFF,118:B800–BCCF |
| Player segment selector | ROM2:ADD9–ADFB; empty masks return early; existing nonempty callers reload the plane pointer |
| Static SAT cache hit | ROM0:6950–69FB; exact mask/door/logo attributes; original cold-shape producer and pattern upload retained |

No new RAM is allocated. Actor scratch is written before use; decimal helpers
initialize both bytes before reading, and no renderer consumer aliases them.
Core summaries preserve the public source-return CPU state and all 128 RAM
bytes, including diagnostic V. Inner source-PC labels in replaced spans are
retired, so profiling must use surviving public boundaries or new labels.

The direct header writes only dirty upper/lower halves and required colors,
while maintaining exact owner/metadata validity. Old generic typed-header
constructors for kinds 16–18 are **retired**, not a preserved callable API.
Dormant dispatch edges still exist. Safety relies on the audited producer
invariant: only the direct header publishes these kinds, and current world,
igloo and footer producers never request them. A new producer must re-audit
that invariant or relocate the header before using those constructors.

The reclaimed directory tails are safe because X embedded both page-specific
NAME pointers in each of 1,280 immutable ice packets. The builder verifies all
2,560 embedded pointers before replacing old directory storage. Live NAME
programs, physical pattern ownership and slot bytes FCC1/FCC5/FFFF stay intact.
Independent review found no blocker under these explicit invariants.

## Reproduction and qualification

The maintained builder uses verified X plus assembly and the local original
ROM. It never reads private candidate ROMs or captured gameplay states.
Original ROMs, generated dictionaries and complete disassemblies remain ignored.
Each output path must be new; sealed X/W/Y evidence is never rebuilt in place.

```sh
.venv/bin/python scripts/build_core_cadence.py \
  --base outputs/presentation/native-lanes-x/build-final \
  --out outputs/presentation/core-cadence-z/NEW-BUILD
.venv/bin/python scripts/presentation_native_check.py BUILD OUT ntsc 2252
.venv/bin/python scripts/presentation_native_check.py BUILD OUT pal 2252
.venv/bin/python scripts/presentation_native_check.py BUILD OUT matrix 2115
.venv/bin/python scripts/presentation_native_check.py BUILD OUT density 1920
.venv/bin/python scripts/presentation_native_check.py BUILD OUT header 54
.venv/bin/python scripts/presentation_audio_check.py --build-dir BUILD --out OUT
.venv/bin/python scripts/presentation_native_clipping.py BUILD NEW-REPORT.json
```

IRQ qualification uses `presentation_fixed_clock_boundaries.py` for nine NTSC
and nine expanded-PAL boundaries, plus its AF2 negative control. Cadence and
jump reports use `presentation_cadence_report.py` and
`presentation_jump_coverage.py`. Natural gameplay, injected scene coverage and
directed interrupt timing are separate evidence classes.

The measured ROM passes 557 original-free host tests, 2,115 original render
scenes, 1,920 dense synthetic scenes, 54 directed header/blank transitions,
4,507 CPU/all-RAM checkpoints and 1,785 coherent pictures across NTSC/PAL.
All natural runs have zero late VBlanks and zero canonical source writes, with
active VRAM, owner, RAM-code and stack guards preserved. Ordered audio checks
cover 2,115 intervals, 3,499 original writes and 2,472 physical PSG writes.
All 18 IRQ boundaries, the AF2 negative control and 10,560 clipping cases pass.

Local component proofs add 622,592 effect, 131,072 ice and 262,144 actor
original-CPU executions; actual Z80 fixtures cover 1,084 / 1,244 / 16,384 cases
respectively. These finite domains and full routes are bounded proofs, not
all-level or physical-hardware acceptance. The header dictionary compiler also
checks every generated column against an independent source-pixel projection.

The selected 4 MiB ASCII16 ROM SHA-256 is
`e59d719e9169a4a73300eb9099008d1a92c77a247b205c78d6961015d16886c5`.
See the release's source/validation attachments for exact clean-build, CI and
publication evidence. The Z workbook preserves every Y sheet and adds measured
cadence/cost comparisons. Previous binaries and workbooks remain immutable.

## Owner test and next work

Compare with v0.0.13 on the same standard-speed MSX1 profile at 100%, ASCII16,
64 KiB RAM / 16 KiB VRAM. Tap F1 to start; use arrows/joystick and Space/fire.
Walk both ways, repeat down/up jumps, steer in the air, ride/reverse ice lanes,
collect fish, pass enemies near edges, and observe HUD/igloo/death transitions.
Expect the same durations, contacts, colors and control response, with more
intermediate pictures and shorter long stalls. Remaining uneven motion is known.
Report machine, TV mode and release, preferably with a short recording and audio.

Continue Issue42 with the remaining world/preparation cost and long-gap cases.
Issue42, parent39 and final timing/full-game issues15/16 stay open. No manual
listening, owner-motion, all-level or physical MSX1 acceptance is claimed.
