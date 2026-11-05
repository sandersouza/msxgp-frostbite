# Native lane cadence diagnostic X

The owner rejected W's slideshow-like movement. X replaces the general world
walker with native lane transactions, precompiles ordinary player shapes, and
reduces background/header work. It improves presentation substantially, but it
is **not original-speed or smooth-animation acceptance**. Gameplay/input/PSG
still follow the unchanged original source clock; player and world are published
from the same snapshot.

## Measured complete-game route

Standard-speed MSX1, 64 KiB RAM, 16 KiB VRAM. The PAL test also uses an expanded
RAM slot. Identical original input route; active gameplay is separated from
blank/startup/death. These are automated emulator measurements, not human or
physical-hardware acceptance.

| Metric | Published W | Diagnostic X |
|---|---:|---:|
| Active complete pictures/s, NTSC | 10.6131 | 18.2214 |
| Active complete pictures/s, PAL | 10.5441 | 17.2158 |
| Mean active picture gap, NTSC | 94.22 ms | 54.88 ms |
| P95 active picture gap, NTSC | 133.47 ms | 83.44 ms |
| Maximum active picture gap, NTSC | 150.19 ms | 116.82 ms |
| Mean complete foreground cost, NTSC | 182,896 cycles | 95,808 cycles |
| Jump update states actually presented, NTSC | 132/390 | 229/390 |
| Mean presented update states per jump | 5.08/15 | 8.81/15 |
| Consecutive pose runs never presented, NTSC | 12/84 | 3/84 |

Each complete original jump has 15 vertical updates, nine distinct Y positions
and 11 consecutive Y-position runs. Launch and grounded landing are counted
separately. The route contains 26 complete active jumps and one interrupted arc.
X presents 152/234 distinct Y positions and 173/286 Y-position runs, versus
106/234 and 114/286 for W. Better pose coverage alone does not prove full arcs.
Landing latency uses measured IRQ bounds, not an invented source-return time;
means over different sampled landings are not paired latency estimates.

The foreground total excludes measured IRQ service. Its passive profile leaves
all five natural measurement buffers byte-identical. Phase means compare the
committed populations of the same route; changed cadence changes those snapshot
populations. P95 uses the observed-order statistic, not interpolation.

## Implementation and invariants

- Native floe lanes use embedded page-specific NAME pointers in six previously
  unused bytes of each immutable ice packet. Original shape/color data stay intact.
- Enemies use sprites only when the full 16-scanline rectangles, global SAT count,
  clipping and ownership permit. Otherwise the existing exact tile path runs.
  Three player cache ways leave four enemy patterns per physical page.
- Stable sprite-only enemies and old/current wholly hidden mode0/X0 enemies omit
  only their own dirty-row contribution. Floe, bear, HUD, background and coarse
  dependencies remain in the union. A rejected previously sprite-based enemy
  forces restoration of both tile rows before publication.
- Player recipes cover the proven ordinary domain and retain the original
  fallback for other positions/animation states. No pose or source update is removed.
- The background writes only required native rows; a 24-byte dirty lookup avoids
  repeated bit decoding. The sparse header retains original colors and fallback;
  wholly empty igloo rows skip unnecessary column composition.
- The black HMOVE mask, viewport, colors, source collision rules, actor counts and
  source timer are unchanged. No turbo, expansion or extra audio device is used.

The measured HUD-as-sprites alternatives regressed whole-game cadence and were
rejected. Right-player recipe extension and native igloo experiments provided
negligible additional gains and are not part of X.

## Allocation certificate

| Allocation | Range / ownership |
|---|---|
| Existing clock plus player recipes | RAM E900–EF32; ROM115:B800–BE32 |
| Native world | RAM F400–F8D7; ROM147:B800–BCD7 |
| Background and empty igloo-row gate | RAM F900–FAC4; ROM148:B800–B9C4 |
| Dirty lookup | RAM FC00–FC17 |
| Sparse header | RAM FD00–FE6F; ROM146:BE00–BF6F |
| Enemy cache keys and previous SAT masks | E8A0–E8A9 and E8B0–E8B7 |
| Background scratch | E86C–E86E |
| Enemy chooser | ROM7:A50D–AA25, after qe_end |
| Enemy patterns | ROM255:9400–A47F |
| Player descriptors/pattern pool | ROM146:B900–BDFF,149:B800–BFFF,148:BA60–BFFF,147:BD00–BFFF |

Slot state FCC1/FCC5/FFFF and the stack/redzone remain untouched. Auxiliary RAM
code has exact byte guards in matrix and natural-route launches. World replacement
bypasses old floe/V-NAME decoders; old bank7 decode code and bank255 pair tables
are unreachable. Builder checks exact prior bytes and resolves old directories
before replacing their consumers. The new enemy SGT ranges are 18–21 and 42–45;
player ways use 0–17 and 24–41, static patterns 48–57 and mask 63.

## Reproduction and evidence

The verified local W parent is required; original ROMs/assets remain ignored.
No captured gameplay states are embedded in the ROM.

```sh
.venv/bin/python scripts/build_native_lanes.py \
  --base outputs/presentation/header-palette-w/build-final \
  --out outputs/presentation/native-lanes-x/NEW-BUILD
.venv/bin/python scripts/presentation_native_check.py BUILD OUT ntsc 2252
.venv/bin/python scripts/presentation_native_check.py BUILD OUT pal 2252
.venv/bin/python scripts/presentation_native_check.py BUILD OUT matrix 2115
.venv/bin/python scripts/presentation_native_check.py BUILD OUT density 1920
.venv/bin/python scripts/presentation_native_check.py BUILD OUT header 54
.venv/bin/python scripts/presentation_native_clipping.py BUILD NEW-REPORT.json
```

`BUILD` and `OUT` are distinct paths; outputs are immutable. Density derives a
state from the hash-verified W route, then independently varies glyph/reflection,
coarse, copy mode, edges and repeated cache reuse. It is renderer coverage, not
proof of observed high-level gameplay. IRQ-boundary and negative-register checks
use `presentation_fixed_clock_boundaries.py`. Cadence and jump reports are
reproducible with `presentation_cadence_report.py` and `presentation_jump_coverage.py`.

Passed: 553 host tests; 2,115 original-render scenes, 1,920 synthetic density scenes,
54 directed header/palette/blank transitions; 4,507 CPU/all-RAM checkpoints and
1,674 coherent pictures across NTSC/PAL; 18 directed IRQ boundaries and AF2 negative
control; 10,560 independent clipping cases. All natural runs have zero late
VBlanks/source writes and preserve active VRAM owners and stack guards. Independent
source build and review reproduced the same ROM and found no release blocker.

The release ROM hash is
`b92478f778a57c70e152497e92102637879248fefac7a9161a9f196928a2c0dc`.
See `references/native-lanes-result.json` for bounded result/producer hashes and
release attachments for the exact source commit and checksum. Workbook X appends
to all 14 preserved W sheets; W and earlier ROMs remain immutable.

## Remaining work and owner test

The active average remains below 29.96 FPS and some gaps still exceed 100 ms.
The largest remaining mean cost is world rendering (~39,251 cycles); header and
igloo changes still cause spikes. Continue Issue42 with these measured cases;
do not close it based on this diagnostic.

Use a standard-speed MSX1 profile, ASCII16 cartridge, 64 KiB RAM and 16 KiB VRAM.
Keep emulator speed at100% and compare with v0.0.12 on the same profile. Test arrow
keys/joystick and Space/fire: walk both directions on shore, repeat down/up jumps,
steer left/right while airborne, ride/reverse floes, collect fish and pass enemies,
and observe HUD/igloo changes. Expect the same jump duration, collision/contact,
input response and colors, with more intermediate pictures; remaining uneven
movement is a known limitation. Report whether improvement is visible, where it
still stalls, any flicker/vanishing enemy, machine/TV mode and preferably a short
recording. Audio listening, controllers, all levels and physical MSX1 remain
separate pending owner checks.
