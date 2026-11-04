# Replace generic rendering with an MSX1-native residency and band pipeline

GitHub: https://github.com/sandersouza/msxgp-frostbite/issues/42

Implementation child of #39. Owner approved architectural replacement and
resuming GitHub. Original Atari 2600 mechanics remain authoritative; preserve
graphics, colors, actors, viewport, input order and audio event timing. The Atari
400/800 fan port and Seaquest are implementation references, not gameplay specs.

## Measured checkpoint — 2026-11-04

The public F→I/J/K/L/M/contact14/P/Q chain now reproduces sealed Q exactly.
The T independent-clock diagnostic runs59.92275NTSC/59.92467PALlogical steps/s
in input-only original routes, with4507CPU/allRAM and1355coherent-picture checks.
Active drawing remains9.79790/9.69859fps: original-speed presentation is unmet.
It is a diagnostic, not the final performance solution. All original colors,
actors, player and mask remain. R's marginal header/igloo path is preserved and
rejected. See docs/fixed-clock-diagnostic.md and the0.0.10human tests. Do not close
#42/#39/#15/#16 from the source-clock result.

Independent review found no demonstrated kernel blocker and required directed
hardware-IRQ boundary alignment in addition to natural replay. The new harness
checks nine mapper/VDP/stream/snapshot boundaries, complete main/alternate/index
registers, SP and bank after RETI; an AF2 mutation must fail its oracle. Manual
listening, alternating controllers, unseen levels and physical MSX remain pending.

### Preserved Q measurements

Shared residency O-B is correct but rejected(-6.91%/-6.90%). Prepared ice P-C
improves4.87%/5.35% against M-C. Eager enemy bands Q-C regress against P-C;
lazy-key bands Q-E improve2.85% NTSC /3.10% PAL over P-C, or7.85%/8.62% over M-C.
Active source cadence33.6350 /35.2938 updates/s remains below the original goal.
NTSC whole-frame mean102843 cycles, P95 219663; complete-route maximum484270.

Q validation:209088 actual Z80 actor cases,2115 original scenes,1920 dense
synthetic scenes,4139 source-model images,4508 source CPU/all-RAM checkpoints.
The complete host suite passes531 tests. Independent review found an evidence
binding gap; corrected reporters reject mixed-ROM proofs and altered audited
buffers. Fresh v2 owner receipts and bound reports preserve identical timings.

The O/P and Q workbooks each contain8278 paired observations and424 cost rows;
historical M and all previous artifacts are preserved. No manual/listening/
physical or complete-game acceptance is claimed. Q-E remains an internal test;
At that checkpoint canonical source integration and a useful human ROM/release
were pending; the current clock diagnostic above supersedes that source gap.

Next: redesign the wider prepare pipeline and its tails. Even zero world work
would leave66928 mean NTSC cycles, above59736. Further enemy-only changes cannot
solve the complete-frame target. See docs/direct-enemy-progress.md and
docs/issue-42-review.md. Keep draft PR43 stacked on41; #39/#42 remain open.

## Goal and first implementation boundary

Build an MSX1-oriented rendering pipeline with a credible complete-frame budget.
Start with shared ice-pattern residency across NAME generations and bounded
per-band NAME preparation. Keep displayed references pinned, including both
colors and vertical phases. Rework physical ownership/key recovery and its
independent checker together; do not weaken active-display protection.

Measure allocation, metadata, lookup, composition, IO and scheduling together.
Replace further generic stages when the whole-frame ledger requires it. The
56-slot host model avoids about 60% of semantic misses; this is a hypothesis
for implementation, not an FPS prediction. N-B traversal alone gained only
1.49% NTSC / 1.99% PAL and is retained as internal evidence.

## Dependencies / Definition of Ready

#39 research and sealed M-C control are available. Read
`docs/native-band-feasibility.md`, its design/plan, and the dedicated handoff.
Start in a forked `Frostbite — ISSUE #42` chat with exclusive checkout
ownership and branch `codex/feat/42-native-renderer`.
No next-issue implementation in the predecessor chat.

## Acceptance / Definition of Done

- Standard-speed MSX1, 64 KiB RAM, 16 KiB VRAM, TMS9918 and built-in PSG only.
- Original CPU/state/input/collision/audio contracts remain equivalent; full
  physical pixels, colors and actors match the sealed control on all tested
  scenes. No frame skipping or reduced simulation rate used to claim success.
- Independent VRAM allocation/visible-reference checks pass, including overlap,
  wrap, phases, blue/white rows, transitions and dense four-lane cases.
- Paired active NTSC/PAL whole-frame mean/P95/max and source cadence identify
  actual gains and remaining shortfall. Update the performance workbook and
  record exact ROM/source/tool/input hashes. Do not sum inclusive helper costs.
- Independent review and focused PR delivery are integrated before closing.
  If original cadence is not achieved, explicitly retain #39's unmet goal;
  #15/#16 remain independent final timing/full-game/hardware qualification.
- Preserve all prior versions. Publish a useful human-test candidate as a new
  prerelease with exact ROM, SHA/source, current limits, next work and concrete
  setup/action/expected-result tests. Internal rejected experiments are archived.

Player-as-tiles remains on hold. Any material visual compromise needs a concrete
owner decision. Do not assume a complete permanent atlas fits VRAM. Automated,
manual-emulator and physical-hardware evidence remain separate.

## Tracking

MSX Game Ports project #7. Type: Task (repository native types unavailable).
Priority P1; size XL; estimate 40 hours, exploratory engineering and validation,
not a deadline. No new labels, milestones or shared project settings required.
