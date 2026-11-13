# Replace generic rendering with an MSX1-native residency and band pipeline

GitHub: https://github.com/sandersouza/msxgp-frostbite/issues/42

Implementation child of #39. Owner approved architectural replacement and
resuming GitHub. Original Atari 2600 mechanics remain authoritative; preserve
graphics, colors, actors, viewport, input order and audio event timing. The Atari
400/800 fan port and Seaquest are implementation references, not gameplay specs.

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
