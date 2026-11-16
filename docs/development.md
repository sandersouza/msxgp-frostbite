# Frostbite maintenance freeze

The supported product is [1.0.0](release-1.0.0.md). Maintenance is limited to
small adjustments. Preserve its mechanics, hardware requirements and published
baseline.

## Build from a fresh checkout

Install Python >=3.11, Git, Make, a C/C++ compiler and `file`, then run:

```sh
make build
make verify
make run
```

The first build fetches and compiles the pinned sjasmplus toolchain. ZX0 is
compiled from its versioned C source. No Python packages, Atari ROM, emulator,
private inputs, previous outputs or sibling repositories are required to build.
Internet is needed only to provision sjasmplus; later builds use its local cache.
`make run` additionally requires openMSX with C-BIOS MSX1 data.

`outputs/native/cartridge/FROSTBIT.ROM` is the complete Normal 32 KiB cartridge.
`outputs/native/disk/` contains COM, BIN, graphics companion and BASIC launcher.
`make verify` checks all five files against the reviewed 1.0.0 hashes.
`make clean` is simply `rm -rf outputs`. A subsequent build recreates everything
under that directory. Tool binaries remain in `.tools/`.

## Maintained sources

- `src/game/game.asm`: complete native Z80 instructions, tables and cold RAM defaults.
- `src/game/symbols.inc`: fixed native symbol addresses.
- `src/game/video.asm`: explicit initial SCREEN 2 graphics and attributes.
- `src/native_*.asm`: native cartridge, DOS and BASIC loaders.
- `src/third_party/zx0/`: decoder and compressor source with their licenses.
- `scripts/`: source assembly, packaging, tool provisioning and focused checks.

The native sources consolidate the historical source-built integrations into
the exact accepted address layout. They assemble into cold RAM/VRAM products;
there is no precompiled game payload or captured emulator state in the build.
The fixed symbol addresses and layout assertions deliberately preserve the
freeze ABI. Changes that alter instruction sizes require updating that layout.
See [source provenance](../references/native-source.json).

## Checks

```sh
make ci-verify
make verify
```

The three unit test files contain 16 checks covering loaders, release identity
and public-source policy. CI also compiles the actual game and compares all five
artifacts. Byte identity is separate from emulator play, listening and physical
hardware evidence. Use the [release play checklist](release-1.0.0.md) for changes.
Changed game bytes require a new version and appropriate release validation.

Pre-1.0 research tools and handoffs remain available in the immutable `v1.0.0`
source tree and commit `52ff734c3f658e735854e548dbdbc1cc5a71b2fc`.
