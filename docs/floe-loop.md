# Native floes and build-and-enter diagnostic

Issue11 adds original-clock floe acquisition ahead of the existing native game
phase. The target is a standard-speed MSX1 with 64 KiB RAM, 16 KiB TMS9918-family
VRAM and built-in PSG. The diagnostic uses a 4 MiB ASCII16 cartridge; cartridge
ROM does not expand host RAM. ASCII16's256 16 KiB bank selections are documented
by [asMSX](https://symsx.github.io/asMSX/man/asmsx-en.html).
No Atari CPU/TIA interpreter runs in the released cartridge.

## Authority and phase boundary

The supplied 4 KiB original has SHA-256
`cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834`.
The new `visible_step` reduces original F019→F476 effects, then the audited
static Z80 translation executes F476→F019 with real MSX input. Canonical
RAM 80..FF remains the game state; the renderer only reads it.

The reduction preserves all 128 RAM bytes and A/X/Y/P/SP for its declared input
channels, including palette/attract effects, sticky ED, final display pointers,
return bytes and footer CPU flags. Entry requires D clear/SP FF. Odd hazard
windows and shore acquisition remain issue #12. Their diagnostic inputs are07;
ED keeps its previous value unless that future acquisition supplies a hit.

## Electrical table, not visible overlap

Raster-only overlap fails at the horizontal edges: TIA collisions include
hidden clocks, positioning and data-dependent collision-update events. A
19-row coefficient convolution also fails because equal consecutive GRP0
bytes change event scheduling. Those rejected research helpers are retained
only to reproduce the failures, never to drive the cartridge or acceptance.

The pinned Stella7.0 source is
`d55b1aec0d067a4c901a6dcdf81cb8f579685659`. The focused
[observation patch](../tools/stella-floe.patch) keeps original CPU/TIA/ROM
behavior and adds228 parallel literal player views (6 poses × 19 shifts × 2 reflections)
at the actual Player counters. Each view preserves its own byte-equality
update events. Source code and compiled observation tools remain local;
[tool instructions](../tools/README.md) explain the build.

The complete controlled domain contains 8,704,000 cases:

- 160 player positions × 160 floe positions × 10 legal 9C/9D control pairs.
- Top-row Y 45..77 and an outside-actor Y 0 sentinel; other rows translate by 26.
- All 228 literal views and both source latch channels in every record.

Each 58-byte record contains 228 P0-contact bits and 228 M1/P1-shadow bits. The
latter bit 6 can change near the actor even when the outside sentinel is set;
it must not be dropped. Only the outside-actor sentinel was factored, after
checking every player X/view. BF bit 7 suppresses new collisions entirely.

Byte-exact interning produces 2,972 records, 5,507 position rows and 444 profiles.
Three-byte bank-local pointer trees consume177 contact banks / 2,861,024 useful
bytes. With the existing code/atlas the smallest fitting power-of-two image
is 4 MiB. No X classes, clipping heuristics or vertical interpolation are used.
Both channels are preserved in near-actor records; identical records alone
share storage. Generated tables and raw original states stay ignored.

## Input, presentation and timing

The original `LDA $0C,X` dummy read retains bus low bits 0C for either player.
The floe diagnostic therefore supplies 0C/8C, including keyboard fire, while
older published ROM bytes retain their own sampler. Unmodified-source probes
cover both players and all four combinations of fire inputs.

The diagnostic presentation is synthetic. Igloo FF means empty; incomplete
progress uses two coarse stages, and only CD 0F shows the completed door.
This display reduction cannot change source construction, reversal costs,
entry, temperature or scoring. Original graphics/HUD/audio acceptance remains
later work. Header text is background; sprites retain TMS9918priority above it.

The optional native carry-branch fusion reuses the raw Z80 carry only at a
uniquely entered adjacent comparison/binary-arithmetic branch. It preserves
the saved source carry whenever live and excludes decimal arithmetic and
alternate entry. It is disabled for older ROM builds. Complete CPU/RAM and
hardware-write-shadow comparisons validate the specialized core.

PAL measurement required eliminating redundant uploads of empty hazard name
rows. Each inactive name page records whether all four fixed hazard rows are
already blank. Any nonempty request invalidates that page; the first empty
request clears all four before later empty requests may skip them. Layout
changes do not move those hazard rows. This changes no simulation, pixels,
VDP I/O spacing or source cadence. Counts tests include nonempty→empty
transitions on both pages; a corrupted cache must fail the pixel oracle.
Landing when temperature reaches zero can still award the block in that same
step while F1requests the later temperature-loss phase; the original instruction
order decides simultaneous events. Controlled full-ROM cases also cover both
players, held/released fire, free completed-igloo reversal, cooldown boundaries,
door edges and coordinate wrapping.

The SAT terminator is written before enabling display, avoiding startup
sprite-overflow from the previously zeroed table.

## Evidence boundaries

The source electrical checker compares 4,632 cases / all 228 actual tuples,
3,756 invariance links, 32 unmodified Stella phases and 768 cached/full-window pairs.
The canonical matrix freezes the complete source helper closure, backend,
capsule, exact cases/results/logs and completion markers. Interrupted catalog-A
and other exploratory runs are not canonical evidence.

The natural original route starts at controlled power-on and real Reset,
uses only directional inputs, constructs the igloo, enters and initializes
level1. It contains 2,254 source checkpoints: construction 1,733, entry 1,912,
initialized next level 2,252. It loses three reserves and finishes with zero;
this is successful natural completion, not a deathless route. No source RAM,
contacts or hazards are patched. Its replay compares every full serialized
state, including CPU/RAM/TIA/RIOT/input state and final bytes.

Replay preserves the original restore journal. Upstream
[JitterEmulation::load](https://github.com/stella-emu/stella/blob/d55b1aec0d067a4c901a6dcdf81cb8f579685659/src/emucore/tia/frame-manager/JitterEmulation.cxx)
calls setSensitivity after loading, resetting the display instability metric.
Regrouping identical inputs changed that metric at 429 checkpoints, while all
CPU/RAM/cycles/otherTIA/RIOT fields and final state agreed. That failed replay
is retained; no fields were masked. The journal-aware replay passes every byte.

Controlled native geometry cases use actual original even-row samples and
explicit neutral odd/shore inputs in unchanged original instructions. All 1,368
cases compare complete CPU/RAM; 1,081 also match the full actual original phase.
The 287 remaining cases expose odd-window ghost contacts near the edges even
with D8=0. They are explicitly declared deferred-channel stimuli, not full
hazard acceptance. The independent natural route avoids those contacts and
must match every actual original CPU/RAM byte without such stimuli.

Actual paced-ROM natural replay additionally checks every completed frame:
source cadence, frame budgets, unchanged visible preparation, all pixels,
SAT/patterns,29-cycle data-write spacing, four sprite slots, VBlank commits,
standard hardware/clock, source continuity, stack and heap. The final partial
frame after the last requested logical step is excluded from frame acceptance.
Dense layout/width/transitions and focused counts are a separate stress suite.
Automated results never imply manual-emulator or physical acceptance.

## Reproduction

Preserve existing environments and source inputs. Use a fresh ignored output
path for each capture/build; never overwrite published binaries.

```sh
mkdir -p outputs/floes
.venv/bin/python -B scripts/stella_floe.py build
.venv/bin/python -B scripts/reference_traces.py
```

Derive the active source F019 capsule with the verified preparation helper,
retaining its returned provenance alongside the capsule:

```sh
PYTHONPATH=scripts .venv/bin/python -B - <<'PY'
import json
from pathlib import Path
from reference_routes import source_reset_checkpoint
raw, proof = source_reset_checkpoint(Path('outputs/reference-traces/summary.json'))
Path('outputs/floes/repro-initial.state').write_bytes(raw)
Path('outputs/floes/repro-initial.json').write_text(json.dumps(proof, indent=2)+'\n')
PY
.venv/bin/python -B scripts/floe_observer_check.py --out outputs/floes/repro-observer --binary outputs/floes/observer-source/stella --initial outputs/floes/repro-initial.state
.venv/bin/python -B scripts/floe_catalog.py --out outputs/floes/repro-catalog --binary outputs/floes/observer-source/stella --initial outputs/floes/repro-initial.state --workers 4
.venv/bin/python -B scripts/floe_routes.py --out outputs/floes/repro-route
.venv/bin/python -B scripts/floe_routes.py --replay outputs/floes/repro-route --out outputs/floes/repro-route-replay
.venv/bin/python -B scripts/floe_build.py --catalog outputs/floes/repro-catalog --out outputs/floes/repro-build
.venv/bin/python -B scripts/floe_check.py --build-dir outputs/floes/repro-build --natural-source outputs/floes/repro-route --out outputs/floes/repro-natural-native
.venv/bin/python -B scripts/floe_check.py --build-dir outputs/floes/repro-build --binary outputs/floes/observer-source/stella --initial outputs/floes/repro-initial.state --out outputs/floes/repro-geometry
.venv/bin/python -B scripts/floe_mechanics.py --build-dir outputs/floes/repro-build --catalog outputs/floes/repro-catalog --initial outputs/floes/repro-initial.state --out outputs/floes/repro-mechanics
.venv/bin/python -B scripts/floe_bench.py --build-dir outputs/floes/repro-build --source-catalog outputs/floes/repro-catalog --suite
.venv/bin/python -B scripts/floe_paced.py --build-dir outputs/floes/repro-build --source outputs/floes/repro-route --family ntsc --out outputs/floes/repro-paced-ntsc
.venv/bin/python -B scripts/floe_paced.py --build-dir outputs/floes/repro-build --source outputs/floes/repro-route --family pal --out outputs/floes/repro-paced-pal
.venv/bin/python -B scripts/native_contract.py --fast-phase --carry-fusion
.venv/bin/python -B -m unittest discover -s tests
```

Canonical producers must be committed/clean. Private CPU proof cartridges are
unit fixtures, not offered human ROMs. Final release delivery freezes the exact
integrated ROM, source commit, raw-artifact manifests and relevant checks;
changed published ROM bytes require a new version.
