# Reproduce issue13 locally

Use a clean committed checkout and `.venv`; see [toolchain.md](toolchain.md).
Original ROMs, complete source captures/catalogs and generated effect data stay
local/ignored. Public CI runs original-free tests only. Existing canonical
evidence paths are immutable: use fresh output paths for every new run.

## Environment, original-free checks and native microproofs

```sh
make environment-check
make test
make source-check
.venv/bin/python -B scripts/native_write_loop_check.py --out outputs/progression/reproduce-loop
.venv/bin/python -B scripts/native_shift_check.py --out outputs/progression/reproduce-shifts
.venv/bin/python -B scripts/progression_check.py --primitives
```

Expected: all original-free tests, 135168 actual-Z80 pure-loop cases, 65536
unchanged shift/flag cases and816 primitive score/bonus cases. The injected-vector
microcartridges require their harness and are private proof fixtures, not human
game releases. Do not use `--explore` for acceptance.

## Exact cartridge and full visible/native boundaries

```sh
.venv/bin/python -B scripts/progression_build.py \
  --floes outputs/floes/catalog-issue11-b \
  --edge outputs/hazards/catalog-edge-b \
  --ordinary outputs/hazards/catalog-ordinary-a \
  --shore outputs/hazards/catalog-shore-a \
  --aliases outputs/hazards/catalog-aliases-a \
  --out outputs/progression/reproduce-build
.venv/bin/python -B scripts/progression_check.py \
  --out outputs/progression/reproduce-phases \
  --build-dir outputs/progression/reproduce-build \
  --floes outputs/floes/catalog-issue11-b \
  --edge outputs/hazards/catalog-edge-b \
  --ordinary outputs/hazards/catalog-ordinary-a \
  --shore outputs/hazards/catalog-shore-a \
  --initial outputs/floes/catalog-issue11-b/initial.state
```

Expected:4MiB ASCII16 with the released SHA and818 complete original CPU/all128RAM
phases. These fixtures intentionally declare starting RAM; continuous routes
below forbid active canonical/contact injection. Build metadata records the
current clean source commit even when regenerated ROM bytes match an earlier
commit. Never overwrite a published version with different bytes.

## Original capture and independent replay

The compact [source result](../references/progression-source-result.json) binds
all eight selected routes. The private accepted input/restore journals are
needed to reproduce those exact difficult advanced routes. Replay them without
changing inputs, active state or the original backend:

```sh
.venv/bin/python -B scripts/progression_routes.py \
  --replay outputs/progression/route-progression-v2-b \
  --out outputs/progression/reproduce-source-v2
```

Repeat with distinct outputs for every selected progression and
exhaustion/restart route, variations0..3. `--kind progression --variation 2`
acquires a new bounded original route; `--plan` can provide controller-pin
proposals. A failed route/predicate is research and cannot replace the complete
selected route. The four retained hazard routes use the independent replay
commands in [hazard-checklist.md](hazard-checklist.md).

## Full current-ROM acceptance matrix

The checked-in [configuration](../references/progression-config.json) contains
paths only, with no private source data. It documents the exact accepted inputs.
Copy it into ignored outputs, then point all new target outputs at a fresh root:

```sh
mkdir -p outputs/progression
.venv/bin/python -B - <<'PY'
import json
from pathlib import Path
c = json.loads(Path('references/progression-config.json').read_text())
root = 'outputs/progression/reproduce'
c.update(build='outputs/progression/reproduce-build',
         phases='outputs/progression/reproduce-phases/progression.json',
         loop_unit='outputs/progression/reproduce-loop/check.json',
         shift_unit='outputs/progression/reproduce-shifts/check.json',
         geometry=root+'/geometry/geometry.json', mechanics=root+'/mechanics/mechanics.json',
         suite=root+'/stress.json', negatives=root+'/negatives.json',
         negative_root=root+'/negatives', logs=root+'/logs')
for name, entry in c['routes'].items():
    entry['native'] = root+'/native/'+name+'/natural.json'
    entry['paced'] = {view: root+'/paced/'+name+'/'+view+'/verified.json' for view in entry['paced']}
Path('outputs/progression/reproduce-config.json').write_text(json.dumps(c, indent=2)+'\n')
PY
.venv/bin/python -B scripts/progression_suite.py --config outputs/progression/reproduce-config.json --stage geometry
.venv/bin/python -B scripts/progression_suite.py --config outputs/progression/reproduce-config.json --stage mechanics
.venv/bin/python -B scripts/progression_suite.py --config outputs/progression/reproduce-config.json --stage native --workers 4
.venv/bin/python -B scripts/progression_suite.py --config outputs/progression/reproduce-config.json --stage paced --workers 4
.venv/bin/python -B scripts/progression_suite.py --config outputs/progression/reproduce-config.json --stage stress
.venv/bin/python -B scripts/progression_suite.py --config outputs/progression/reproduce-config.json --stage negatives
.venv/bin/python -B scripts/progression_delivery.py --config outputs/progression/reproduce-config.json --out outputs/progression/reproduce-seal
```

Geometry/mechanics replay audits frozen actual original observations before
executing14828/652 fresh target cases; it does not relabel old target results.
Natural replay executes all12 routes independently in the native harness and
all96 route×NTSC/PAL×layout×width combinations. Every CPU/128RAM checkpoint and
every completed pixel frame must match. No logical step is dropped.

Run the serial stress stage before negatives; only these two stages create
automatic benchmark directory names. All15 stress modes and14 named runtime
faults must pass their own proof. The sealer re-reads raw inputs/CPU/pixels/cycles,
checks helper/ROM/profile hashes, validates the original catalogs and recomputes
maxima. Hard limits remain59736/71364 cycles,29-cycle VRAM spacing and four
sprites per line with standard clock/RAM/VDP, mapper/stack/slot/interrupt guards.

Publish only ROM, `build.json`, `validation.json` and `SHA256SUMS` from the seal.
`private-evidence.json` and transitive source/raw evidence remain local/ignored.
Manual emulator and physical hardware observations require the separate
[human checklist](releases/v0.0.6-progression.md); automation cannot supply them.
