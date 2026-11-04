# Issue #42 — native renderer implementation handoff

Issue: https://github.com/sandersouza/msxgp-frostbite/issues/42
Parent: #39, original-speed objective still open. P1 / XL / exploratory 40h.
Owner approved replacing the architecture and resuming GitHub. Continue
autonomously; routine implementation does not require another approval.

## Ownership and source

Current exclusive owner is the issue42 fork/thread
`01a1a457-0a26-77c0-b7c7-ddaa7a36a5eb`, branch
`codex/feat/42-native-renderer`. Draft PR43 is stacked on PR41. The following
starting instructions describe the original transfer; do not create a duplicate
chat/branch or resume predecessor edits.

## Current clock diagnostic checkpoint

Public F→I/J/K/L/M/contact14/P/Q producers reproduce sealed Q byte-for-byte.
R's native header/igloo/player-way path is correct but marginal and rejected
as a human candidate. T separates the original scheduler/native/input/PSG clock
from coherent full-picture preparation. Read docs/fixed-clock-diagnostic.md and
the0.0.10human tests first. Selected ROM SHA
`29b4588b62d4b44a88401c691512d415b26bdaf559198d889730ee2b49763b1e`.

Measured source59.92275NTSC/59.92467PALsteps/s; active pictures9.79790/9.69859fps.
Do not call this smooth/original-speed graphics or close42/39/15/16. Default
original sprites/player/mask, pixels and mechanics remain protected. Independent
review requested real IRQ boundary alignment; the added harness tests nine
mapper/address/stream/snapshot boundaries and actual register/bank/VRAM return
invariants. F3/F4 mixed-pixel hypothesis was retracted; polling moved to the
prepare boundary as optional cleanup. Source F1/F2 input is unchanged.

Local artifacts: outputs/presentation/fixed-clock-t/. Preserve all previous
immutable controls and trial failures. Workbook continuation in
outputs/01a1a457-0a26-77c0-b7c7-ddaa7a36a5eb-T preserves all Q cells/features.
Current exclusive checkout owner remains this issue42chat/branch. Next work:
reduce preparation/cache replacement tails across several source ticks and
measure active complete-picture cadence separately from logical-step cadence.
Manual audio, alternating controls and physical acceptance remain pending.

## Earlier Q checkpoint

Latest implementation commit before review correction:1c25578. O-B rejected,
P-C correct internal packet baseline, Q-C rejected versus P, Q-E lazy actor bands
gain2.85% NTSC /3.10% PAL over P. Q-E ROM SHA
`2654da3abdb2fc2624f6485a9104327447e0493f64a864feb56b41212dc5ada9`.
Active source cadence33.6350 /35.2938 updates/s; original speed remains unmet.
Read docs/direct-enemy-progress.md and docs/issue-42-review.md first for current
evidence/representation and review fix. Source canonical integration and useful
human-ROM delivery remain pending; do not call inherited commits complete source.

Local Q evidence is under outputs/presentation/direct-enemy-q. Use bound reports
and v2 physical receipts.209088 native cases,2115 source scenes,1920 density
scenes,4139 original images and4508 CPU/all-RAM points pass;531 host tests pass.
The Q workbook is under outputs/01a1a457-0a26-77c0-b7c7-ddaa7a36a5eb-Q,
SHA`c50df7aa188ff89a16d2ab16ae6c53238ecc32531449375170d220d639151767`.
M/N/O/P evidence seals were freshly verified unchanged(112/147/220/467 files).

Next: redesign the wider prepare pipeline and its tails. Even zero world work
leaves66928 mean NTSC cycles, above59736; another enemy-only patch cannot solve
the target. Source/input/audio, player/mask and original graphics remain protected.
No human candidate/release was selected from these internal modest-gain tests.

Start only in dedicated fork `Frostbite — ISSUE #42` within the Frostbite
project, cwd `/Users/sandersouza/Developer/msx-gamePorts/frostbite`. Fork from
the committed native-band checkpoint on `codex/fix/39-atari800-performance`
(parent `b341e9f020f94de197a5bafa7d45b4fe678f9a4d`). The transfer message supplies
the exact checkpoint commit. Create `codex/feat/42-native-renderer` there.
PR #41 carries the research checkpoint; avoid accidentally closing #39.
Only the new issue chat edits after activation; predecessor stops mutations.
Do not reset inherited files or rebuild into previous artifact directories.

Read AGENTS.md, required Obsidian guidelines, approved original design, local
issue copy `.github/issues/frostbite/native-msx-renderer.md`, and
`docs/native-band-feasibility.md`. Private continuation with prior M-C build
details: `.superpowers/sdd/issue-39-local-current.md`.

## Exact artifacts and evidence

- Owner-test M-C: `outputs/presentation/playfield-m-c/build/`, ROM SHA
  `0e43bd16a5219a2d2548580e581ee5e26c7f440e715c18d96e07dbe033351ad0`.
  All 112 files of its existing seal freshly verified unchanged.
- N-B internal walker: `outputs/presentation/native-bands-n/build-b/`, SHA
  `cd90ef510ba8c52ca3792d7803c4308d211d2855b700e39cc8a2cadeddc1a751`.
  Hardened build-C is byte-identical. Original build-B sources archived.
- N evidence: matrix-b (2115), density-b (1920), ntsc-b (2253), pal-b (1886).
  Every original CPU/all-RAM checkpoint and three complete VRAM snapshots match
  M-C; traffic and non-world cycles unchanged. 514 host tests passed.
- Active cadence M-C → N-B: NTSC 31.1855 → 31.6490 (+1.49%);
  PAL 32.4926 → 33.1387 (+1.99%). Whole-route peak remains 489112 cycles.
  N is not an accepted architecture solution or human-test delivery.
- Offline shared residency, 56 slots/bank: NTSC 6852 → 2756 semantic misses;
  PAL 6803 → 2714. At 64 slots: 2559 / 2523. No Z80/FPS/transfer claim.
- Public aggregate `references/native-band-feasibility.json` binds measurements
  and model to private inputs. Public source contains no original-derived assets.

## Implementation starting point

M-C is the control, not a requirement to keep the renderer. Its average NTSC
busy cost is 111564 cycles, world 44776, source 22059, sprites 15207. Zero world
still exceeds the 59736-cycle frame. Address whole-frame and tail costs.

1. Declare a physical shared ice pool, initially using existing 64 slots per
   bank. Current IDs: bank 1 = 19..50 and 83..114; bank 2 = 9..40 and 73..104.
   Verify these against the live asset generator before editing.
2. Pin actual displayed and complete-next references. Use bounded exact lookup
   for pattern+color keys and prepared per-band NAME mappings. Audit scratch
   allocation explicitly; never assume unused low RAM survives BIOS/slot calls.
3. Replace generation-derived `p_fast_old_key` behavior and ownership checks
   for physical IDs shared across pages. Add an independent reference-based
   guard; do not merely remove the old private-page checks. Preserve overlap
   fusion destinations and visible pattern/color/SAT/SGT protection.
4. Original logic/input/collision/audio remain untouched and authoritative.
   Audit Seaquest's prepared-data/dirty-region approach, adapting for Frostbite's
   overlap/vertical phases and TMS9918 constraints instead of copying assumptions.
5. Measure the complete frame with the original F profiler/input adapter and
   matched active NTSC/PAL routes, plus complete source matrix and synthetic
   density. Update a NEW performance workbook, preserving M's original file.
6. Continue other stages as required by measured budget. Only deliver a useful
   candidate after review, with a versioned prerelease, exact ROM/source/hash
   and human tests. No human or physical acceptance has occurred for N.

No player-as-tiles, graphics concessions, fewer actors, hidden source steps,
turbo, expansions or changing original mechanics. Respect VDP IO spacing and
current-display ownership; eventual VBlank/timing acceptance remains separate.
Keep #39/#15/#16 open for their own unmet acceptance conditions.
