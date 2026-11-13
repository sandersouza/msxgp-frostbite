# Issue #42 — native renderer implementation handoff

Issue: https://github.com/sandersouza/msxgp-frostbite/issues/42
Parent: #39, original-speed objective still open. P1 / XL / exploratory 40h.
Owner approved replacing the architecture and resuming GitHub. Continue
autonomously; routine implementation does not require another approval.

## Ownership and source

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
