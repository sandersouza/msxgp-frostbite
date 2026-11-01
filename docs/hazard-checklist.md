# Reproduce issue12 locally

Use a clean committed checkout and the configured `.venv`. Original ROMs,
source backends, complete catalogs and route captures are local/ignored;
public CI has no proprietary inputs. Regenerate missing source inputs with
the reference tools before running the dependent commands. Keep captured
helper/backend/capsule identities frozen and always choose fresh output paths.
These commands use the accepted local input names recorded in the handoff.

## Environment and original-free checks

```sh
make environment-check
make test
make source-check
.venv/bin/python -B scripts/native_shift_check.py --out outputs/hazards/shifts-reproduce
```

The last command is a synthetic microcartridge check, not a human ROM release.
It must pass all65536 cases without `--explore`.

## Build the full ROM

```sh
.venv/bin/python -B scripts/hazard_build.py \
  --floes outputs/floes/catalog-issue11-b \
  --edge outputs/hazards/catalog-edge-b \
  --ordinary outputs/hazards/catalog-ordinary-a \
  --shore outputs/hazards/catalog-shore-a \
  --aliases outputs/hazards/catalog-aliases-a \
  --out outputs/hazards/build-reproduce
```

The builder audits every complete raw component/alias, verifies lossless
physical-bank decoding and rejects producer drift/capacity overflow. Compare
its `build.json` ROM hash with the released hash. Prior versions retain their
own build interfaces; `make build` still builds the first diagnostic.

## Full geometry and controlled native phases

```sh
.venv/bin/python -B scripts/hazard_check.py \
  --out outputs/hazards/geometry-reproduce \
  --build-dir outputs/hazards/build-reproduce \
  --floes outputs/floes/catalog-issue11-b \
  --edge outputs/hazards/catalog-edge-b \
  --ordinary outputs/hazards/catalog-ordinary-a \
  --shore outputs/hazards/catalog-shore-a \
  --binary outputs/hazards/observer-shore-source/stella \
  --initial outputs/floes/catalog-issue11-b/initial.state
.venv/bin/python -B scripts/hazard_mechanics.py \
  --out outputs/hazards/mechanics-reproduce \
  --build-dir outputs/hazards/build-reproduce \
  --floes outputs/floes/catalog-issue11-b \
  --edge outputs/hazards/catalog-edge-b \
  --ordinary outputs/hazards/catalog-ordinary-a \
  --shore outputs/hazards/catalog-shore-a \
  --initial outputs/floes/catalog-issue11-b/initial.state
```

Expected:14828 actual visible CPU/128RAM phases and652 full native cases,
with actual contacts. A declared initial fixture is separate from natural play.

## Original input-only routes and independent replay

For each of `bear-chase`, `bear-refuge`, `fish-envelope`, `threat-push`:

```sh
.venv/bin/python -B scripts/hazard_routes.py \
  --kind fish-envelope --out outputs/hazards/route-fish-reproduce
.venv/bin/python -B scripts/hazard_routes.py \
  --replay outputs/hazards/route-fish-reproduce \
  --out outputs/hazards/replay-fish-reproduce
```

Use distinct output names per route. Require the named completion predicate,
all CPU/RAM/TIA/RIOT/input checkpoints and exact final capsule. An interrupted
or predicate-failing attempt is failed research, never a passing shorter route.

## All clock and presentation combinations

Run this command for each route above, each family `ntsc`/`pal`, each layout
`0`/`1` and each width `0`/`1`, using fresh output names (32 runs):

```sh
.venv/bin/python -B scripts/hazard_paced.py \
  --source outputs/hazards/route-fish-reproduce \
  --build-dir outputs/hazards/build-reproduce \
  --family pal --layout 1 --width 1 \
  --out outputs/hazards/paced-fish-pal-layout1-width1-reproduce
```

Expected: complete original CPU/128RAM equality, exact completed-frame pixels,
source cadence, VBlank/29-cycle IO/sprite/guard/device checks. Default-view
acceptance cannot stand in for another view; the PAL/layout1/width1 fish route
was the measured failure that required the compact flag lowering.

## Crowded visual/native stress and deliberate faults

```sh
.venv/bin/python -B scripts/hazard_bench.py \
  --build-dir outputs/hazards/build-reproduce \
  --floes outputs/floes/catalog-issue11-b \
  --edge outputs/hazards/catalog-edge-b \
  --ordinary outputs/hazards/catalog-ordinary-a \
  --shore outputs/hazards/catalog-shore-a \
  --family pal --layout 1 --width 1 --transitions
```

Run both families/all layouts/widths, normal and inverted transition starts,
the explicit `--catalog counts` visual-cache case, and NTSC/PAL `--mixed`
canonical count seeds:15 modes total. Every run verifies240 completed frames
and continuous original CPU/128RAM phases. Its dense visual overlay is separate
from the one-time canonical seed; real NUSIZ0 still means one source copy.

Repeat controlled native cases with `--inject collision`, `rng`, `row_priority`,
`sticky`; repeat stress with `--inject spacing`, `sprite`, `guard`, `state`,
`pixel`, `contact`, `cache` (use `--catalog counts` for cache). These commands
must fail at their intended raw comparison, not at an unrelated precondition.
Keep the full failure witnesses, exact helpers/ROM and producer hashes.

## Seal and publish

The accepted private configuration is
`outputs/hazards/delivery-d-config.json`; it explicitly names every source,
replay, actual unit/native/paced/stress report and all eleven negative witnesses.
When recapturing, update every path and captured helper/ROM identity, including
the 32 named route/view gates, rather than reusing older successful reports.

```sh
.venv/bin/python -B scripts/hazard_delivery.py \
  --config outputs/hazards/delivery-d-config.json \
  --out outputs/hazards/delivery-reproduce
```

Only the exact ROM, `build.json`, `validation.json`, `SHA256SUMS` are public
release assets. The private evidence manifest and original-derived trees stay
local. Run independent review/CI/integration checks, download every published
asset and compare bytes before closing the issue or transferring the checkout.
