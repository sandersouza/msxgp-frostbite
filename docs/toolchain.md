# Development tools

Supported host setup: macOS arm64 or x86_64, Python >=3.11, Git, Xcode command
line tools and Homebrew. The original fresh-source setup exercised arm64;
Intel/Rosetta and installation on a fresh OS were not certified by that test.

[tools-lock.json](../references/tools-lock.json) pins sjasmplus, DiStella,
DASM and Python dependencies. Managed assemblers live under
`.tools/frostbite/<name>-<commit>/`, with source/build/binary receipts.

```sh
bash scripts/setup.sh --dry-run
bash scripts/setup.sh
bash scripts/setup.sh --check
make test
make ci-verify
make render-build
```

Setup creates a missing `.venv` and prepares pinned tools. It checks existing
versions instead of silently replacing incompatible environments or binaries.
Check is read-only; dry-run describes changes. Do not delete the whole
`.tools/` or `.venv/` tree to repair one failed tool. No system Python is replaced.

`make build`, `make run`, `make smoke` and `make package` operate on the
original-free 16 KiB hardware diagnostic. `make render-build` creates a
synthetic SCREEN2 benchmark. These are retained infrastructure checks, not
commands for the released game. The hardware-diagnostic release-note template
under `docs/releases/` remains because its maintained packager reads it.

For the native 32 KiB game and its disk formats, follow
[development](development.md) and [native formats](native-formats.md). The
ZX0 compressor path is explicit and its source revision is verified. Local
qualified original-derived inputs are required; public CI does not fetch them.

## Reference tools

Provide the owner-supplied original ROM locally at
`references/roms/frostbite.bin`, then use:

```sh
make reference-check
make reference-rebuild
make mechanics-check
```

The reference inventory validates its identity before backend execution.
Generated disassemblies, graphics, contact tables and raw routes remain ignored.
The source timing decoder requires the reviewed Stella debugger format;
emulator/firmware checks use their recorded versions and hashes. A tool merely
being installed is not proof that a runtime check passed.

DOS/BASIC validation requires a licensed local DOS disk and the firmware
specified by the native disk harness. Those files are never release assets.

## Provenance

Retained infrastructure follows the project GPLv3 license and the provenance
recorded in [baseline preservation](baseline-preservation.md). Host tools
retain their upstream licenses. The ZX0 runtime decoder source and notice are
under `src/third_party/zx0/`. Original Atari material remains separately owned.
