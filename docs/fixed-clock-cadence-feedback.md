# Cadence feedback after the clock diagnostic

The owner reports excessive speed, cadence unlike the original, and apparent
skipped pictures after0.0.10delivery. This is an unresolved human-play result;
the loaded binary hash and emulator speed are not independently confirmed.
Issue42returns to In progress. The release is not accepted for gameplay cadence.

The read-only audit rechecked2253CPU/all128RAM points and the original video
counters. All2251post-startup intervals span one original Atari frame, not two.
The exceptional cold-start interval spans seven frames and is excluded. The
retained source sequence therefore provides no support for halving the simulation
clock as a timing repair. An accelerated game clock was not reproduced in this
controlled standard-speed MSX1 replay; the owner's observation remains open.

Visual skipping is confirmed:164active picture intervals span an average6.043
original states, ranging from2to9. In the first normal jumps,29original frame
intervals take about0.484seconds of MSX logic time but produce only4or5pictures.
Eleven normal temperature decrements are64original frames apart and take
1.068036..1.068044seconds between MSX IRQ anchors. These are logical-event anchors;
they are not the times at which a human first sees those events.

An additional instrumented replay leaves every existing CPU, picture, owner,
IRQ and presentation buffer byte-identical. Disjoint mean foreground costs per
active snapshot, excluding measured IRQ entry-through-RETI time, are:

| Stage | MSX CPU cycles |
| --- | ---: |
| World / ice / enemy preparation | 100,566 |
| HUD / igloo | 32,713 |
| Player / sprites | 24,446 |
| Final names / upload | 15,673 |
| Background | 12,704 |
| Dirty comparison | 9,951 |
| Snapshot / description | 4,072 |
| Release and footer | 1,187 |
| Total foreground, including interrupt acknowledge overhead | 201,312 |

The old Q cost ledger cannot be reused as the new renderer's per-picture budget:
with several source steps between snapshots, more of the world changes each
time it is drawn. The world remains the largest measured cost, about half of the
foreground work. The next change must reduce complete preparation and improve
actual presentation regularity; lowering simulation frequency would alter the
original wall-clock mechanics without drawing the missing states.

[Bound feedback and raw-evidence hashes](../references/fixed-clock-cadence-feedback.json)
preserve the distinction between owner observation and controlled measurements.
The ROM and its published attachments are unchanged; this audit creates no new
ROM release. Original graphics, mechanics and the immutable0.0.10artifact remain
the control for further work.
