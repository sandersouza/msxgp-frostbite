# Native MSX1 formats — Issue44

All formats execute one shared flat runtime on a standard-speed MSX1 with
64 KiB RAM,16 KiB VRAM,TMS9918-family VDP and built-in PSG. The cartridge is a
complete32,768-byte Normal ROM. It needs no mapper or external payload. Disk
formats naturally need a disk interface and the corresponding operating system.

The accepted v0.0.30 remains immutable. On2026-11-14 the owner explicitly
accepted publishedv0.0.31 fluency as pleasant likev30 after being told its
measured presentation cadence is4.1–8.3% lower. This is an owner-approved
cadence tradeoff for Issue44, not numerical parity or physical-hardware proof.
Original mechanics/source state, audio and per-picture graphics have separate
automated equivalence checks. See references/compact-delivery/issue-44-owner-acceptance.json.

## Loading and reset

- Cartridge: insert `FROSTBIT.ROM`, select **Normal** (no mapper) and reset.
- MSX-DOS1: copy `FROSTBIT.COM` to a bootable DOS disk and run `FROSTBIT`.
  It is a self-contained executable loaded at0100h. It checks DOS TPA before
  taking over; an insufficient TPA prints an error and returns to DOS.
- Disk BASIC: keep `FROSTBIT.BAS`, `FROSTBIT.BIN` and `FBGFX.BIN` together on
  the disk. Run `RUN"FROSTBIT.BAS"`. The launcher sets `CLEAR 200,&H87FF`,
  loads the companion into VRAM with `BLOAD"FBGFX.BIN",S`, then starts the
  real executable at8800h with `BLOAD"FROSTBIT.BIN",R`.

The BASIC companion is required. Its purpose is to stage part of the compressed
input and graphics without overwriting BASIC's program or disk workspace.
Neither disk executable contains or depends on the Atari ROM, the old4MiB
cartridge or an emulator. After successful takeover **RESET exits/restarts**;
return to DOS/BASIC is not implemented. The game owns the64KiB RAM and VRAM.
Controls are the same as the accepted cartridge: joystick1 or cursor keys,
trigger/space; use the existing console controls documented in the release.

## Loader layout and guarantees

Cold RAM/VRAM are constructed from maintained initializers and exact qualified
assets, never from a captured emulator state. ZX0 backwards decoding uses the
audited source revision `ecde3a2ae05061fe06469ed46df81a33b7de7d86`, with its
licensed decoder under `src/third_party/zx0/`.

The ROM temporarily stages compressed input in VRAM and upper RAM. It exposes
its second Normal-ROM window through BIOS slot calls, identifies the actual
page3 RAM primary/subslot, then jumps to upper RAM before mapping page2 to RAM.
DOS/BASIC use the same slot identity and compressed game payload. No operating
system or BIOS service is called after takeover.

- Combined graphics/high payload expands at8000h..CC73h; its first16KiB go to
  VRAM, and its3188-byte high segment moves toF380h..FFF3h.
- The low62208-byte image is decoded backwards to0003h..F302h. Three bytes of
  measured overlap slack are mandatory. The14-byte relocator atF303h moves it
  down to0000h..F2FFh and enters the transient initializer atC400h.
- The69-byte decoder atF312h, slot flags atF360h..F362h and bootstrap stack at
  F380h remain outside the low decode destination. The initializer copies slot
  flags before any CALL can overwrite them.
- The transient initializer configures VDP/input/PSG, measures the actual video
  period, resets the original source machine, installs IM1 and starts the same
  original60Hz source scheduler. The game stack remainsF300h..F37Fh.
- Disk BASIC loads the first8192 compressed low bytes plus graphics/helpers
  into VRAM; the executable carries the remaining low bytes at8800h. The two
  FE-header BINs are executable/staging files, not renamed ROM images.

## Reproduction

Local original inputs are intentionally excluded from public CI. First
reproduce/qualify the hash-bound native graphic IRQ integration described in
`references/compact-delivery/issue-44-native-graphic-irq.json`; its4MiB artifact
is a **build/host-oracle input**, never the native delivered cartridge.

```sh
make native-delivery \
  NATIVE_BASE=outputs/compact/issue44-native-enemy-irq-game-02/build \
  NATIVE_CONTROL=outputs/presentation/credit-reference-at/build-final \
  NATIVE_OUT=outputs/compact/my-fresh-native-build \
  ZX0=../seaquest/.tools/zx0/zx0
```

The command independently proves70 P0 patterns,512 bear geometries and1280
NAME rows, allocates/links the whole game, creates cold images, compresses the
cartridge and produces genuine COM/BIN files. It archives maintained producer
sources and hashes. Builders intentionally do not self-certify game acceptance.
No previous output directory is overwritten. The ZX0 revision is checked and its executable hash is recorded;
the exact executable path is explicit and may be another audited local checkout.

For real native-cartridge qualification:

```sh
.venv/bin/python scripts/native_flat_takeover_check.py \
  --base outputs/compact/issue44-native-enemy-irq-game-02/build \
  --linked outputs/compact/my-fresh-native-build/linked \
  --cold outputs/compact/my-fresh-native-build/cold \
  --cartridge outputs/compact/my-fresh-native-build/cartridge/FROSTBIT.ROM \
  --mode ntsc --out outputs/compact/my-fresh-native-check/ntsc
```

Repeat modes `pal`, `bear-ntsc`, `bear-pal`, `matrix`. Natural runs use real
cold loading and input-only source routes. The matrix explicitly injects
controlled states after real initialization; it is a rendering-domain proof.
`native-takeover.json` binds the **executed native ROM hash** separately from
the historical host-oracle ROM referenced by inner inherited check receipts.
`--profile` adds passive CPU entry/return timers on natural routes.

Real disk qualification uses `scripts/native_disk_boot_check.py --disk ...
--cold ... --out ... --mode dos|basic --family ntsc|pal --dos1-disk PATH`.
Provide a local licensed DOS1 disk and installed Sony HB-701FD BIOS/firmware.
Optional `--machine-profile`, `--firmware-dir`, `--emulator` make those paths
explicit. The harness validates firmware hashes from the installed profile,
creates a fresh360KiB disk, and preserves the source DOS disk. It verifies the
actual loader entry, byte-exact complete cold RAM/VRAM and subsequent IRQ/render
execution. DOS/BIOS files are not copied into product releases.

Automated source/pixel/IRQ proofs, actual OS loading, manual listening/play and
physical MSX tests are separate evidence classes. Successful emulator loading
does not establish physical-hardware or owner acceptance.
