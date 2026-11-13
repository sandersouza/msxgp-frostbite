# Issue42 — lower left sea-edge closure checkpoint

Same root writer, Issue42 chat and `codex/feat/42-native-renderer`. This is an
internal correctness checkpoint; no new human-test ROM/release has been delivered.
The latest public rollback remains v0.0.25. Performance acceptance remains open.

## Owner steering and correction

The owner reported that the black left playfield column did not close completely.
The old NAME publisher covered rows8..21 / targetY64..175. Water could remain in
column2 / X20..23 below it. The additive closure covers row22 as well, throughY183,
using the existing black tile128. No extra sprite, RAM or VRAM allocation. Source
CPU/RAM, physics, input, PSG, P0 palette and foreground priority are unchanged.
Footer graphics start farther right and remain untouched.

Five new atoms: scripts/build_border_closure.py,
scripts/presentation_border_closure.py,
scripts/presentation_border_closure_check.py,
src/presentation_border_closure.asm,
tests/test_presentation_border_closure.py. Parent200 files remain unchanged.
The explicit independent raster oracle masks background before redrawing source
P0; it does not exempt the new strip from pixel comparison.

## Exact internal artifacts and checks

- Root: `outputs/presentation/player-bands-ao-research/` (unsealed).
- Parent `build-full-02`, ROM
  `d29333a3a62411888de10af3202c3925cac8dbba86750f32004fd8a5ef80c193`.
- Corrected `build-border-02`, ROM
  `4b22951ec3a957f797605c9688e04debb393c77e4191d21adf2ff641d555f9c3`,
  205 source fingerprints, dirty checkout at ac2fb72.
- Patch only58 bytes at resident F57E..F5B7 in bank147. All ROM bytes outside this
  publisher remain byte-identical. The LIVE26-byte AH bootstrap at F5B8..F5D1 is
  preserved exactly. Initialize A128 once, then unroll15 stores in the old slot.
- `border-closure-audit.json`: 256 matrix cases,0 raster differences against the
  declared closure;610 host tests; four natural regular2252/bear620 routes pass
  exact source CPU/allRAM, composed raster, physical owners and active-page guards.
  No late VBlanks. All3497 committed pictures contain tile128 at row22/column2,
  both NAME pages exercised in every route.
- NTSC regular32.0965525 FPS, bear29.4352365. PAL regular30.2850848,
  bear25.0790677. Deltas from the relevant preceding controls under0.000008 FPS;
  this is a graphical closure, not a performance/cadence change.
- `border-closure-comparison.png` shows the same source snapshot87 from actual
  native captures before/after; only8 pixels change, X20..23/Y176..177.
- `border_image.py` and `audit_border.py` reproduce the comparison/audit.
- Owner/mobile/physical hardware evidence remains pending.

## Rejected attempt retained

`build-border-01` / ROM5c096c77...905f93 was rejected immediately by watchdog at
boot/case0. It patched the historical84-byte allocation and erased the later live
AH bootstrap. It was never released. Its logs/artifacts remain as negative
history; only02 is current. Do not repeat the old84-byte padding assumption.

## Pending continuation

Independent review is GREEN in `player-bands-ao-review/border-closure-01/review.json`,
SHA47d4ebbc41a711831e3b3f9cb3ccd02716b0d6f5a5d414038981f7fd9ac0a7c1.
It rebuilt the exact ROM, exercised67,932 native publisher calls and independently
checked256 actual source snapshots plus128 directed foreground-priority cases.
All513 matrix captures differ only in the two PAGE-specific row22/column2 NAME
bytes; all PGT/CGT/SGT/SAT/register bytes stay exact. No blockers; its writers and
emulators have stopped. No new workbook or release marker has run.

The previous AO packed-P0 and full-bear optimization remains active, with strong
native reviews in the same AO review root. Temperature burst design is cleared;
its pure model and two tests exist, but no ASM/builder/runtime candidate exists.
Resume it from the AO plan and temperature-design receipt to attack four NTSC
three-VBlank temperature-update spikes. Future builder should compose the
closure, retain its explicit oracle and preserve all current controls.

Before a human-test release: commit a qualified runtime, rebuild exact ROM from
clean sources, complete relevant density/header/IRQ/audio/source/negative/CI
checks, whole-frame timings/landings and workbook AO preserving the40 AN tabs,
then publish exact ROM/hash/source/notes/tests/WebMSX. Never overwrite a release.
The61 sealed predecessor roots remain immutable. No issue close/merge/successor
or shared-checkout ownership transfer occurred at this checkpoint.
