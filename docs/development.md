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
`make verify` checks all five files against the current 1.0.1-rc.2 hashes.
The published 1.0.0 baseline remains immutable in its separate receipt.
`make clean` is simply `rm -rf outputs`. A subsequent build recreates everything
under that directory. Tool binaries remain in `.tools/`.

## Maintained sources

- `src/game/game.asm`: complete native Z80 instructions, tables and cold RAM defaults.
- `src/game/symbols.inc`: fixed native symbol addresses.
- `src/game/video.asm`: explicit initial SCREEN 2 graphics and attributes.
- `src/game/start_hints.asm`: pre-game text and its fixed source overlays.
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

The [1.0.1-rc.2 candidate](release-1.0.1-rc.2.md) adds aligned F1/F2 hints.
They borrow unused igloo slots only on the empty initial/selection screen.
Existing construction is preserved; instructions stay hidden when an existing
igloo occupies those slots. Returning to an empty selection restores the text.
All native background assets are retained. Explicit source overlays use the
bypassed cold initializer, old auxiliary bootstrap and clock-setup tail, plus
unused RST-vector bytes. The IRQ vector remains intact. The cartridge loader
uses symbolic payload addresses without unnecessary header alignment, keeping
all five native formats and the complete Normal 32 KiB cartridge.

For the focused keyboard/display regression check, preserve a built 1.0.0
delivery outside `outputs/` before cleaning, then run:

```sh
python3 scripts/start_hints_check.py --baseline /path/to/1.0.0-delivery \
  --delivery outputs/native --out outputs/hints-check
```

This requires openMSX and its C-BIOS MSX1/European profiles. It exercises actual
keyboard input, all four variations, start, movement/jump, return to selection
and restart in NTSC/PAL. It compares published pictures at matching coherent
source states. It is a bounded route, not a new full-density or hardware claim.

Pre-1.0 research tools and handoffs remain available in the immutable `v1.0.0`
source tree and commit `52ff734c3f658e735854e548dbdbc1cc5a71b2fc`.

The same checker accepts `--igloo-matrix` for a separate renderer diagnostic
that injects all 16 construction stages. This is not natural gameplay evidence;
its receipt explicitly marks target-state injection. Both checks compare against
1.0.0 and require live native assets to remain byte-identical.
