# Active-play slowdown — owner video, 2026-11-03

**The current ROM still runs at roughly half original speed during the measured
active-play segments.** The previous 600-output averages mixed active play with
lighter phases. Their modest 2–3% improvement remains valid for that sequence,
but those averages understated the slowdown while playing.

The owner reports intact colors/graphics close to the original and unacceptable
speed. Record this as visual feedback for the shown view, not acceptance of all
views, mechanics timing, sound or physical hardware. Issue #14 remains In progress
in its existing exclusive chat/branch. No ROM changes or new release accompany
this investigation; the immutable
[0.0.9 release](releases/v0.0.9-performance-preview.md) remains available.

## Independent video observation

The supplied 66.46-second recording shows an `openMSX 21.0 — C-BIOS MSX2+`
window. The loaded ROM hash, TV mode and emulator speed setting are not visible.
Do not identify it as a specific release from appearance alone or attribute the
problem to that machine: the slowdown is independently reproduced on MSX1.

At 0.1-second sampling, the displayed temperature changes from 44 at 12.1 seconds
to 27 at 55.5 seconds: 17 decrements over 43.4 seconds. The original ROM's normal
play gate at FA97..FA9D decrements every 64 source frames. At its nominal source
clock, that interval would take approximately 18.16 seconds. Conditional on
uninterrupted normal play, the video therefore suggests about 42% of original
speed. This is a HUD-based estimate, not direct CPU timing or display FPS.
The entry/bonus countdown after that interval uses another gate and is excluded.
Video capture FPS is not used as game FPS; no listening verdict is claimed.

The original video, extracted frames and source-derived raw captures remain
local/ignored. [Public evidence metadata](../references/presentation-active-speed-result.json)
records hashes, methods, observations and their limits without publishing them.

## Direct timing of the unchanged 0.0.9 ROM

Source: `12e204e6ecf6403fed63fd0e2f8c602ef84099a4`.
ROM SHA-256: `838b67ae6ba4c7cbed72f643f64f78b45bb404a1e43b395f36331343f6656ae6`.
The isolated profile is standard-speed MSX1, 64KiB RAM, TMS9918A/16KiB VRAM
and built-in PSG. All captured source inputs are original controller inputs;
there are zero canonical RAM injections.

| Input route / family | All measured intervals, updates/s | Adjacent active intervals | Active updates/s |
| --- | ---: | ---: | ---: |
| Existing 600-output NTSC prefix | 38.78 | 286 | 28.56 |
| Existing 600-output PAL prefix | 40.18 | 294 | 30.44 |
| Extended 2,253-output NTSC route | 38.15 | 1,008 | 27.90 |

An interval qualifies when C6=E7=F1=0 in both adjacent captured preparation
states. Rate is the sum of actual logical updates multiplied by 3,579,545,
divided by the sum of measured commit intervals in CPU cycles. The unmeasured
first interval is excluded. This conservative filter separates active states
from attract/delay/death/bonus phases; it does not classify every intermediate
source update. PAL may contain two ordered logical updates per preparation.
These are scenario-specific source update rates, not universal ratios or a
complete display/audio acceptance result.

The extended route uses a private copy of the existing profiler with the sample
bound raised from 600 to 3,000 and timeout from 180 to 360 seconds. It is research,
not a replacement canonical delivery producer. Its hash, adapter, launch script,
emulator/profile and raw artifact hashes are retained in the metadata.

All 2,254 actual CPU/all128RAM checkpoints match the complete retained original
variation-0 progression route. The original assessment also matches: construction
at step 1,733, entry at 1,912, bonus complete at 2,203 and next level at 2,252.
That proves this route's sequence, not correct wall-clock timing, game over/restart,
all variations/views, ordered PSG output, manual play or hardware acceptance.

The extended run still fails cadence: 788 over-budget iterations, 1,433 skipped
VDP frames, 705 visible commits and 148 duplicate VDP frames. Maximum busy cost
is 507,343 cycles against a 59,736-cycle NTSC budget. No failed frames are removed
from the retained raw evidence.

## Cost and next optimization target

Across the 1,008 selected NTSC intervals, preparation averages 100,753 cycles:

| Preparation stage | Mean cycles |
| --- | ---: |
| World: floes, bear and objects | 53,625 |
| Complete player/sprites | 19,551 |
| Dirty-state comparison | 9,179 |
| Header/igloo | 6,426 |
| Final NAME preparation/upload | 5,513 |
| Background | 5,031 |
| Description, release and footer | 1,427 |

Source logic/scheduling averages another 22,059 cycles and commit 1,944. Keeping
those costs, preparation would have about 35,733 cycles available per NTSC frame:
approximately a 65% reduction from its measured mean is needed. This is a planning
estimate only; acceptance still requires complete worst and transition frames to
meet deadlines. Small cache improvements alone are insufficient.

Nested call measurements further split world work into approximately 26,596
cycles for actor primitives and 23,906 for floe preparation. Within floe work,
strip publication averages 11,353 cycles and raw uploads 8,066; these nested
figures overlap and must not be added to the stage totals. The next experiments
must reduce complete actor and floe preparation, rather than treating transfer
speed alone as the cause. A naive atlas of every floe phase/color is not an
accepted solution: it must also fit the shared 256-ID SCREEN2 banks with the
other live roles and satisfy active/inactive ownership.

Continue with equivalent world/floe and complete-player preparation, preserving
all pixels, actors, source updates, audio events and VDP safety/ownership rules.
Measure active play separately on the same input routes and keep transition/worst
frames visible. Repeat canonical whole-image, native-state, audio and NTSC/PAL
checks on changed ROM bytes before publishing another version. Do not compensate
with turbo, slower mechanics, fewer actors, omitted drawing or a lower simulation
frequency. The final combined acceptance and review remain pending; #15 and legacy
cleanup #17 have not started.
