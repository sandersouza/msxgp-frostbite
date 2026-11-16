# Native MSX1 formats

All formats execute the shared 1.0.0 flat runtime on a standard-speed MSX1 with
64 KiB RAM, 16 KiB VRAM, TMS9918-family VDP and built-in PSG. The complete
32,768-byte Normal cartridge requires no mapper or external payload. Disk
formats require their operating system and disk interface.

## Loading and controls

- Cartridge: insert `frostbite-1.0.0.rom` (builder output `FROSTBIT.ROM`), select
  **Normal** and reset.
- DOS: run `FROSTBIT.COM` from a bootable MSX-DOS disk. An insufficient TPA
  produces an error and returns to DOS before takeover.
- Disk BASIC: keep `FROSTBIT.BAS`, `FROSTBIT.BIN` and `FBGFX.BIN` together;
  run `RUN"FROSTBIT.BAS"`. The launcher stages the companion in VRAM and
  starts the executable at 8800h; the companion is required.

F1 starts/resets; F2 selects a game (release between presses). Use joystick 1
or cursor keys and fire/Space. The game owns RAM/VRAM after takeover. Machine
RESET exits/restarts; return to DOS/BASIC is not implemented.

## Build

All game sources and native static data are versioned. No original Atari ROM,
private upstream image or `.local-inputs/` directory is required.

```sh
make build
make verify
```

The build assembles the native Z80 program and initial SCREEN 2 data, compresses
the payloads with the versioned ZX0 source and assembles the cartridge/DOS/BASIC
loaders. Output defaults to `outputs/native/`. Repeated builds are incremental;
`make clean` removes all outputs and the next build recreates them. The source
contains the accepted 1.0.0 selective audio gain. See [setup](toolchain.md) and
[source layout](development.md).

The ROM uses BIOS slot identity during loading, then decodes the low image
backwards with exactly three bytes of overlap slack and relocates it before
entering C400h. Helpers and bootstrap stack stay outside the destination. The
initializer configures VDP/input/PSG, measures video period, resets source state
and starts IM1/source scheduling. No OS/BIOS service is used after takeover.
The transient loader workspace is not additional runtime RAM.

## Freeze checks

`make verify` checks all five files and their build receipt against the reviewed
1.0.0 baseline. Changed game bytes require a new version and release; identity
does not certify manual play, audio listening or physical hardware.

For real disk loading, retain `scripts/native_disk_boot_check.py --disk ...
--cold ... --out ... --mode dos|basic --family ntsc|pal --dos1-disk PATH`.
Provide a local licensed DOS1 disk and installed Sony HB-701FD firmware.
Optional `--machine-profile`, `--firmware-dir`, `--emulator` make paths explicit.
The harness checks firmware hashes, creates a fresh disk, preserves the input
disk and verifies actual entry, complete cold RAM/VRAM and subsequent execution.

Play/listen at standard speed in NTSC and PAL using the
[release checklist](release-1.0.0.md). Restore broader source/pixel/cadence
harnesses in a separate historical checkout before reopening those change
domains. Original ROMs, research captures and OS/BIOS inputs remain local. Native build data is versioned.
