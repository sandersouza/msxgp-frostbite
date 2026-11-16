# Frostbite development

The supported product baseline is [1.0.0](release-1.0.0.md): a shared native Z80
game delivered as a 32 KiB Normal cartridge, MSX-DOS COM and Disk BASIC package.
Preserve original gameplay mechanics; document presentation adaptations and
measure cadence changes independently from original-state equivalence.

## Source layout

- `src/`: native Z80 runtime, loaders, constructors and licensed ZX0 decoder.
- `scripts/`: source translation, asset production, linking and validation.
- `tests/`: original-free unit and component checks.
- `references/`: consumed contracts/configuration, tool pins and retained
  native-delivery evidence. These are inputs and evidence, not game binaries.
- `tools/`: maintained Atari observer/backend patches.
- `outputs/`: ignored local builds, raw evidence and qualified input artifacts.

The maintained scripts are the dependency closure of current build/validation
commands and regression checks. Superseded integration stages and standalone
experimental probes are recoverable from Git history. Shared artifact hashing
lives in `scripts/artifact_hash.py`, independently of historical builders.

## Maintenance freeze

The owner has frozen major development after 1.0.0; maintenance is limited to
small adjustments. The unit suite is deliberately limited to six files and
36 checks: source/release identity, native loaders, selective audio gain, raw
input, RAM allocation and bounded validation routes. Broad compiler, component,
experimental and historical-diagnostic unit suites remain in Git history.

For a game change, use the actual native build and the relevant source/pixel,
audio or loading harness below. This focused unit suite alone does not certify
the game. Reopen broader testing only if development scope changes.

## Original-free checks

Prepare the [host tools](toolchain.md), then run:

```sh
make test
make ci-verify
make render-build
```

The unit suite and synthetic diagnostics require no original ROM. CI checks
the synthetic diagnostic's repeatable byte identity; it does not build or
validate the native 1.0.0 game. `make build`, `make run`, `make smoke` and
`make package` remain hardware-diagnostic commands. See
[CI boundaries](ci-and-tracking.md).

## Native game build and qualification

Use the hash-qualified native graphics/IRQ base and accepted graphics control
described in [native formats](native-formats.md). Build into a fresh directory:

```sh
.venv/bin/python -B scripts/build_native_delivery.py \
  --base outputs/compact/issue44-native-enemy-irq-game-02/build \
  --control outputs/presentation/credit-reference-at/build-final \
  --out outputs/compact/my-fresh-native-build \
  --compressor /absolute/path/to/verified/zx0 \
  --effect-gain
```

`--effect-gain` is required for the 1.0.0 audio behavior. The default without
that option targets the older audio configuration. `make native-delivery`
forwards `NATIVE_EFFECT_GAIN=--effect-gain` to this builder.

Qualified inputs, original-derived graphics/contact data and licensed OS/BIOS
files are local prerequisites. A public checkout alone cannot reconstruct the
game. The native builder archives maintained producer/checker sources and
hashes; its successful exit is not acceptance. Use native takeover checks for
`ntsc`, `pal`, `bear-ntsc`, `bear-pal` and `matrix`, plus actual DOS/BASIC
loading checks in both video families. Loader details and invocations are in
[native formats](native-formats.md).

The selected graphics/IRQ base and accepted graphics control are immutable
upstream build inputs. To reconstruct their historical integration stages,
use the release source checkout; those old command-line stages are not part
of the maintained native delivery pipeline.

Separate original CPU/state equivalence, pixel/ownership checks, emulator
routes, manual play/listening and physical hardware results. After renderer,
input, assets, HUD or audio changes, measure complete active routes in both
NTSC and PAL, including dense scenes and bear pursuit. Booting is insufficient.

## Historical recovery

The post-1.0 cleanup removes superseded plans, issue drafts, handoffs, reports
and unused experimental entry points. Runtime assembly, consumed contracts,
native qualification and regression checks remain. Local ignored inputs,
outputs, tools and the inherited snapshot are preserved.

Use `git show v1.0.0:path/to/file` for files present at release time. The last
pre-cleanup source is `52ff734c3f658e735854e548dbdbc1cc5a71b2fc`; it also contains
the subsequently committed experimental builder and unfinished console test.
Restore historical builds in a separate checkout. Recorded hashes remain tied
to their original source tree; cleanup does not recertify them.
