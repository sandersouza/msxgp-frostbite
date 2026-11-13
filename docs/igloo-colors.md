# Igloo color-only diagnostic AD

AD continues v0.0.16 with a publisher scoped to the igloo. An exact key hit
reuses the complete tile. When a valid previous igloo has the same masks and
both backgrounds certify the same pattern shape, AD updates only its eight
CGT bytes. New tiles, changed shapes, nonuniform backgrounds, gray backgrounds
and forced/invalid contexts retain the original complete constructor.

## Complete-route measurements

Standard-speed MSX1,64KiB RAM/16KiB VRAM, built-in PSG. PAL uses an expanded
RAM slot. The original simulation remains approximately59.92source steps/s.

| Active metric | v16 NTSC | AD NTSC | v16 PAL | AD PAL |
|---|---:|---:|---:|---:|
| Complete pictures/s | 25.4519 | 25.9009 | 22.9176 | 23.1226 |
| Mean picture gap, ms | 39.290 | 38.609 | 43.635 | 43.248 |
| P95 picture gap, ms | 66.753 | 66.752 | 79.713 | 59.843 |
| Longest gap, ms | 83.441 | 83.442 | 99.683 | 79.780 |
| Complete foreground mean, cycles | 70,935 | 69,756 | 75,403 | 74,907 |
| Complete foreground P95, cycles | 126,273 | 123,363 | 134,836 | 134,044 |
| Igloo cycles / active picture | 3,909 | 3,390 | 4,259 | 3,742 |
| Complete ISR mean / hardware IRQ, cycles | 22,129 | 22,152 | 26,163 | 26,174 |
| Grounded landings shown /26 | 15 | 14 | 12 | 13 |
| Endpoint Y shown /26 | 21 | 21 | 19 | 20 |
| Entirely missed pose runs /84 | 0 | 0 | 1 | 0 |
| Mean first post-landing age, source steps | 2.500 | 2.538 | 2.846 | 2.500 |

NTSC/PAL complete-picture rates improve1.76%/0.89%. The observed whole foreground
means fall1.66%/0.66%. Igloo cycles per active picture fall13.29%/12.15%, but
the before/after picture populations differ (433/441NTSC and391/394PAL). These
stage-mean differences are not paired component CPU savings. Passive profiling
reproduces all five natural buffers byte for byte. Complete ISR includes the
21-cycle EI/RETI tail on identical1008NTSC and843PAL active source intervals.

NTSC loses grounded landing arc21, source step1672; endpoint coverage is unchanged.
Its first post-landing age changes2to3source steps. PAL gains grounded/endpoint
arc23, step1732. PAL P95 and maximum gaps improve about24.93%/19.97%. All26arc
ages and per-arc changes remain in the workbook. PAL still has only24post-IRQ
sampleable grounded windows under the existing atomic source scheduler.

The observed worst igloo call increases25,025to27,389cycles because the full
fallback remains necessary and the new dispatch adds work. Full foreground
maxima nevertheless fall173,876to173,397NTSC and174,727to172,891PAL on this
route. This is a modest diagnostic gain, not stable30FPS or original-fluidity
acceptance. Original game state and contact rules are never slowed or removed
to improve coverage statistics.

## Allocation and contracts

There is no new RAM or VRAM. A35-byte resident bridge uses6212..6234 inclusive,
the remaining retired typed-header continuation before the live footer6249.
The1169-byte banked helper/tables start at119:B800. This is retired NAME-directory
storage: all2560native page-specific pointers already reside in ice packets and
target banks120..145. The current5328-byte header dictionary uses116..118.
Future producers must not revive the retired directory or generic typed-header API.

The bridge saves the entry mapper on the existing stack. Exact hits and full
fallback restore that mapper; successful color updates restore bank1, matching
the old constructor. Every mapper switch uses the IRQ-restored shadow. The
page, group, row, column and forced-ID gates preserve fixed physical ownership.

The color-only certificate requires previous/current type5 keys, identical
upper/lower masks, foreground14, role flags0 and two backgrounds with PGT=FF
and equal CGT nibbles other than14 on every scanline. Zero-mask halves retain
the background colors. The old identity is invalidated before CGT writes; the
new six-byte key becomes valid only after all eight bytes complete. Exact hits
do not change VRAM. Full fallback keeps original bounds and constructor behavior.
The scoped publisher does not promise typed-constructor scratch output on a
cache hit or color-only path; later constructors initialize their own scratch.
Original CPU/all128-RAM remains the mechanics oracle.

## Qualification and reproduction

569 original-free host tests pass. Independent review rebuilds all154bound
sources, preserves all151parent sources, and compares917,504actual-background
constructor results plus transition/mutation cases. The exact clean ROM passes
2115source scenes,1920density scenes,54header cases,10560clipping cases and2115
ordered-audio intervals (3499source/2472PSG writes). Natural NTSC/PAL compare
4507CPU/all-RAM checkpoints and2510coherent pictures, with zero lateVBlanks or
canonical source writes. Final clean-source runs reproduce all five measured
buffers. Exact-source push/PR CI passes.

Nine NTSC and nine expanded-PAL directed IRQ boundaries pass, with an AF2fault
correctly rejected. Two additional full-route probes force a real interrupt
while streaming AD's bank119 CGT data. Registers, alternate/index registers,
SP, mapper, VRAM and coherent snapshot are preserved. These deliberately
perturbed routes are safety evidence and are excluded from performance results.

```sh
.venv/bin/python scripts/build_igloo_colors.py --base outputs/presentation/ready-presentation-ab/build-release --out NEW-BUILD
.venv/bin/python scripts/presentation_ready_check.py BUILD OUT ntsc 2252
.venv/bin/python scripts/presentation_ready_check.py BUILD OUT pal 2252
```

Use the same ready-check entrypoint for matrix2115,density1920,header54 and the
three boundary modes. Use the existing audio/clipping checks separately. Raw
producers and receipts remain under ignored `outputs/presentation/igloo-*`.
See `references/igloo-colors-result.json` and `references/igloo-colors-delivery.json`.

ROM SHA-256:
`c50a3131df056011af9a037b58624d9de84930b3474579b24d2137d736e9d562`.
Runtime source `059bec5f985f3aac121014016dadfa31ec3fc892`.

## Human tests and next work

Compare against v0.0.16 on the same100%MSX1 profile,64KiB RAM/16KiB VRAM,
ASCII16 mapper. TapF1 to start; arrows/joystick move and jump, Space/fire acts.
Build igloo blocks while the upper band changes colors. Expect the same shapes
and gray foreground without flashing, missing blocks or stale background colors.
Reverse an ice row and check changed igloo progress against v16. Repeat up/down
jumps, immediately jump after landing, and steer horizontally. Report NTSC/PAL
separately, including a short recording with audio and any skipped landing.

The next targets remain WORLD preparation, long foreground tails and the
additional cold/fallback igloo cost. Keep issues42/39/15/16 open. Automated
emulator, owner observation, manual listening and physical hardware acceptance
remain separate; all-level and original-fluidity acceptance are pending.
