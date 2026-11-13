# Ready-picture presentation diagnostic AB

AB continues Issue #42 from the exact v0.0.15 ROM. Fresh profiling identifies
WORLD as the largest average foreground stage: 31,312 cycles per active picture,
including 17,458 for floes and 10,587 for actors. The landing investigation also
finds fully prepared pictures waiting approximately 20 ms behind the old
two-field presentation gate. AB addresses repeated actor eligibility work and
that avoidable wait, while keeping the original simulation clock and coherent
whole-world snapshots.

## Measured result and selection

The same complete natural route runs on standard-speed MSX1. PAL uses an expanded
RAM slot. Display throughput is separate from the approximately 59.92 original
source steps per second. No simulation states are slowed, removed or replayed.

| Active metric | AA / v0.0.15 | AB |
|---|---:|---:|
| NTSC complete pictures/s | 21.4600 | 25.4519 |
| NTSC mean picture gap | 46.598 ms | 39.290 ms |
| NTSC P95 picture gap | 66.753 ms | 66.753 ms |
| NTSC longest gap | 83.441 ms | 83.441 ms |
| NTSC jump update states presented | 266/390 | 277/390 |
| NTSC consecutive jump Y runs presented | 196/286 | 207/286 |
| NTSC grounded landings presented | 9/26 | 15/26 |
| NTSC endpoint Y presented | 20/26 | 21/26 |
| NTSC entirely missed animation-pose runs | 2/84 | 0/84 |
| NTSC mean first post-landing picture age | 3.077 source steps | 2.500 source steps |
| PAL complete pictures/s | 20.1950 | 22.9176 |
| PAL P95 picture gap | 59.907 ms | 79.713 ms |
| PAL grounded landings presented | 13/26 | 12/26 |
| PAL endpoint Y presented | 21/26 | 19/26 |
| PAL mean first post-landing picture age | 2.654 source steps | 2.846 source steps |
| PAL maximum first post-landing picture age | 6 source steps | 7 source steps |

NTSC throughput improves 18.60%. PAL throughput improves 13.48%, but its landing
coverage and tail intervals regress. This release is an NTSC-focused diagnostic,
not a general PAL landing improvement or stable 30 FPS result. PAL landing steps
1732 and 1762 lose grounded presentation; their first post-landing ages rise
from 3 to 7 and 2 to 6 source steps. Endpoint presentation also loses step 202;
step 232 gains both metrics. All per-arc changes, including NTSC regressions,
remain in the workbook and machine-readable evidence.

Twenty-four of the 26 complete jumps have a grounded window of only one original
source step. An endpoint Y position alone is insufficient: it may already show
the next jump pose. PAL can execute two source steps within one IRQ; landings
202 and 1190 occur before its second source update, so only 24 of the 26 grounded
states are sampleable by the current atomic-after-IRQ snapshot architecture.
The denominator of 26 is retained for cross-version comparison. First-post ages
include every complete arc, including missed grounded states.

The isolated eligibility change reaches only 21.665 NTSC pictures/s and loses
one grounded landing. It is not released alone. First-field admission alone
reaches 25.258; the combination reaches 25.452 and gains another grounded landing
and endpoint without losing either relative to that experiment. Gains from
isolated experiments are not added together.

## Whole-frame costs

Passive profiling reproduces all five natural buffers byte for byte. Complete
foreground preparation averages 70,935 cycles versus 80,142; WORLD averages
26,058 versus 31,312. These are different picture populations (433 versus 365)
on the same route. The 11.49% observed foreground-mean decrease is not a paired
CPU saving or a claim that changing a comparison instruction saves those cycles.
Earlier presentation changes which snapshots are prepared and their workload.

Complete ISR averages 22,129 cycles versus 21,986 on the identical 1,008 active
source intervals, including the 21-cycle EI/RETI tail. More visible commits add
about 143 cycles per source interval. AB foreground P95 is 126,273 cycles and
maximum 173,876; these remain well beyond a two-field budget. Long gaps persist.

The fresh AA profile attributes 6,557 cycles to floe NAME selection, setup and
copy, including 4,764 in copying. An offline residency experiment finds 52.02%
of copied rows already identical and an upper bound of 2,672 cycles/picture
before cache lookup and invalidation costs. Its RAM representation and partial
dirty updates are not certified. No NAME-cache implementation or measured speed
gain is included in AB. Seaquest's shared-pattern approach remains a design
reference; its historical timing is not Frostbite evidence.

## Runtime contracts and allocation

The certified enemy path replaces only ROM bank 7 A50D–AA25. Fixed preflight
entrypoints AA00 and AA03 remain unchanged. The preflight's previous-SAT bit and
clear invalid bit certify the same lane for the current coherent snapshot.
Base SAT contains at most 19 sprites; four lanes add at most 12, so at most 31
are used. The 26-line lane pitch exceeds sprite height. Player/static rectangles
cannot change between preflight and WORLD. Uncertified lanes use the full
existing eligibility path. Copy counts, offsets and clipping scratch are rebuilt
for every certified lane; they are not reused from the last preflight lane.

The presentation change is one operand byte in the fixed-clock RAM kernel at
EA36 (stored in ROM bank 115). It admits an already completed coherent picture
after one actual VBlank instead of requiring two. It does not display partial
work, update the player independently, interpolate source states, change the
source scheduler, or alter input/audio ordering. Same-field commits remain
forbidden. No new RAM or VRAM is allocated. Existing packets, colors, geometry,
NAME programs, physics and collision rules remain exact.

The legacy two-field validator remains available for earlier releases. The new
`presentation_ready_check.py` entrypoint verifies the explicit one-field build
contract and actual ROM instruction, then uses a separate spacing validator.
It retains CPU/all-128-RAM, pixels, owners, IRQ ordering and protection checks.
Raw timestamps and hardware field indices are never rescaled. A companion
`ready-contract.json` binds the new producer and the unchanged underlying
receipt; boundary receipts are not rewritten after hashing.

## Reproduction and qualification

The additive maintained builder verifies the exact v0.0.15 ROM and all 147
parent source hashes. It assembles new source and applies the single admission
operand; it never reads a private candidate ROM. Generated original-derived
data stays ignored. The build rejects an existing output directory or a ROM
different from the selected measured hash.

```sh
.venv/bin/python scripts/build_ready_presentation.py \
  --base outputs/presentation/floe-transactions-aa/build-release \
  --out outputs/presentation/ready-presentation-ab/NEW-BUILD
.venv/bin/python scripts/presentation_ready_check.py BUILD OUT ntsc 2252
.venv/bin/python scripts/presentation_ready_check.py BUILD OUT pal 2252
.venv/bin/python scripts/presentation_ready_check.py BUILD OUT matrix 2115
.venv/bin/python scripts/presentation_ready_check.py BUILD OUT density 1920
.venv/bin/python scripts/presentation_ready_check.py BUILD OUT header 54
.venv/bin/python scripts/presentation_ready_check.py BUILD OUT boundary-ntsc
.venv/bin/python scripts/presentation_ready_check.py BUILD OUT boundary-pal
.venv/bin/python scripts/presentation_ready_check.py BUILD OUT boundary-negative
.venv/bin/python scripts/presentation_audio_check.py --build-dir BUILD --out OUT
.venv/bin/python scripts/presentation_native_clipping.py BUILD NEW-REPORT.json
```

Use a fresh OUT for each run. The release validation attachment records final
clean-source qualification, independent review, CI and exact artifact identity.
Automated emulator proof, manual observation, owner feedback and physical MSX1
acceptance remain distinct. All-level and subjective fluidity acceptance remain
open even when bounded source/pixel checks pass.

Selected ROM SHA-256:
`9d2ee2926bc8de7fd0d22b05e7ad334e76078141bfde997720adfb62414cc77b`.

## Human tests and next work

Compare with v0.0.15 using the same MSX1 profile at 100% speed, 64 KiB RAM /
16 KiB VRAM, ASCII16 mapper. Start with NTSC. Tap F1 to start; use arrows or
joystick and Space/fire. Repeat down/up jumps, immediately jump again on landing,
and steer left/right in the air. Expect more visible intermediate states and
unchanged control response; occasional skipped landing instants remain possible.
Ride and reverse floes, activate each lane, pass enemies/fish near both edges,
and check player colors, HUD, igloo, death transitions and audio.

If testing PAL, report it separately: some landings and long gaps are worse in
the measured route despite higher average throughput. Please include release,
machine, TV mode and a short recording with audio, especially consecutive
landings and horizontal steering. Do not interpret higher average FPS as final
fluidity acceptance.

Next: reduce remaining WORLD/floe NAME work and long foreground tails, then
address PAL landing sampling with the original source clock intact. Issues #42,
#39 and final timing/game acceptance #15/#16 remain open.
