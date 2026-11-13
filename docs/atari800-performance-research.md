# Atari 400/800 reference: why its presentation is inexpensive

Issue: [#39](https://github.com/sandersouza/msxgp-frostbite/issues/39).
The selected MSX baseline remains the masked v0.0.9 ROM, SHA-256
`838b67ae6ba4c7cbed72f643f64f78b45bb404a1e43b395f36331343f6656ae6`.
No MSX runtime or graphics change accompanies this research checkpoint.

## Identity and primary evidence

The owner-supplied file is a valid type1 standard 8KiB CAR: 16-byte header,
8192-byte payload, matching additive checksum, run/init vectors in A000–BFFF.
Whole-file SHA-256:
`e3fc0fd44748810def7f3313720ed65f320624ec1cc832d087d983d00e947243`.
The [Atari800 cartridge specification](https://github.com/atari800/atari800/blob/98cc2dc749867c9c7317a0271ba062a6c797f886/DOC/cart.txt)
defines the container. Original input, disassembly and captures remain ignored.

Glurk's [release post](https://forums.atariage.com/topic/328758-frostbite-400-for-christmas/)
describes an 8KiB cartridge running in 8KiB RAM. His
[implementation explanation](https://forums.atariage.com/topic/328758-frostbite-400-for-christmas/page/3/)
states that the aim is to run the original 2600 game loop unchanged, using the
similarity of the hardware. This corrects the hypothesis that speed came from
replacing the game's mechanics with a newly invented engine. It is an author
statement, not independent full-equivalence proof. The supplied bytes have not
been matched to his attachment: direct attachment retrieval returned an HTML
challenge. No corresponding source archive or reuse license was located in the
three release-topic pages inspected. Do not infer permission to copy code.

## Observed execution

Built Atari800 commit `98cc2dc749867c9c7317a0271ba062a6c797f886` as
libatari800, using its bundled Altirra replacement OS. Applied a read-only event
logger for ANTIC register writes and GTIA reads/writes. Its PC field is a CPU-slice
sample, **not** an exact store-instruction trace. The authoritative register
offset definitions are in that revision's `src/antic.h` and `src/gtia.h`.

Two isolated runs use Atari400/800 machine type, actual 8KiB RAM, normal emulated
clock, 1200 output frames each; Start at frame180, then alternating up/down and
fire from240. Every frame's mapped cartridge bytes match the supplied payload.
Initial unconfigured-display-list diagnostics occur during5 NTSC/4 PAL boot
frames; only that specific diagnostic is allowed before frame61. No later errors.
The configured emulator rate is not a measured physical oscillator or host FPS.

| Evidence | NTSC | PAL |
|---|---:|---:|
| Nominal emulated output rate | 59.922745Hz | 49.860760Hz |
| Adjacent sample intervals, frames300–1199 | 899 | 899 |
| Counter81 increments per sample interval | exactly1 in all899 | exactly1 in all899 |

Local inspection identifies the loop's counter increment and its wait for a
change in the OS clock. Counter cadence is demonstrated for these inputs;
complete mechanics, dense high levels, game-over/restart and physical hardware
are not qualified. A counter tick alone does not prove every gameplay event.
PAL executes one loop per50Hz output in this sample. It does not demonstrate
NTSC-speed simulation on PAL; the author's original post also acknowledges a
slower PAL50 version. Our original-source timing requirements remain binding.

## What actually saves work

1. **Eight bands use ANTIC fine scrolling.** In sampled execution HSCROL writes
   occur at scanlines103/117/129/143/155/169/181/195, with additional top-region
   setup. The CPU changes scroll registers during display-list interrupts.
   The display list also selects coarse screen addresses. Moving a band does
   not require rebuilding every shifted pixel on the CPU.
2. **Characters remain in ROM.** CHBASE alternates between BA and BC during the
   bands, within the mapped cartridge. Mode6 character entries are visible in
   the live display list. The screen draws those glyphs through ANTIC DMA;
   per-band fine movement does not require transferring them to a separate VDP.
3. **GTIA supplies raster collision evidence.** Across900 sampled frames there
   are8100 reads of D004 (P0PF),3600 of D005 (P1PF), and9000 writes to D01E
   (HITCLR). The program collects/clears collision latches at successive bands.
   The logger records read events, not returned values; no collision-fidelity
   claim follows from those counts.
4. **The CPU family is shared.** Original6502 instructions can execute directly
   on the A8. The MSX requires Z80 implementations of their behavior and the
   relevant TIA-visible results. No timing ratio between CPUs is inferred here.

In the NTSC post-startup sample, the256-byte A00–AFF region is unchanged between
every adjacent snapshot. The 1024-byte600–9FF region changes on average0.251
bytes/interval, maximum4. These are end-of-frame byte differences, **not counts
of stores**: writes restoring an old value are invisible to this method.

## What transfers to MSX1

The TMS9918 has no ANTIC display list, per-band HSCROL/VSCROL, shared CPU/video ROM
address space or player-versus-background collision latches equivalent to GTIA.
Its sprite-collision flag cannot replace our original floe/enemy contacts.
Changing SCREEN2 to SCREEN1 supplies none of those features.

The transferable design principle is to retain immutable patterns and organize
movement as small band-specific state changes. v0.0.9 already uses ROM-derived
geometry and floe NAME-row rotation. Repeating those features is not a new fix.
The earlier local C experiment retained per-tile composition/publication costs;
its lack of speed gain is consistent with that remaining work.

Two bounded offline probes prevent premature implementation:

- A complete permanent atlas for just one normal floe control delta needs129–148
  distinct masks per SCREEN2 bank across its two row phases; retaining both
  white and touched-blue CGTs would take258–296 tile identities. There are only
  256 per bank, shared with every other element. Some other legal deltas need
  up to222 masks before the second color. A naive all-phase/all-color atlas
  cannot fit while preserving the current image.
- An idealized shared28-slot pool per bank/generation, using2254 original route
  states, reduces estimated floe pattern misses from7081 to6376 (9.96%). This
  omits management/fusion/scheduling costs and is not an actual-ROM speed result.
  With floe raw upload only about8066 cycles in the existing active preparation
  breakdown, this does not justify a new ROM by itself.

## First recommended MSX experiment

Prototype **one native enemy-band renderer that emits final tile data directly**
from canonical glyph/position/reflection/color state. Keep the player, black mask,
floes, screen geometry and original contacts unchanged. This isolates the cost
of the generic descriptor/resolver/constructor path, which fine scrolling on A8
bypasses. It differs from merely translating a descriptor row or using sprites.

Before integrating, compare the complete band against original-derived pixels
over all positions, glyph phases, copy modes, clips and floe-overlap conditions;
include active-VRAM/ownership guards. Measure the **entire band path including
clearing, composition, metadata and PGT/CGT/NAME transfer**, not only expansion.
Then measure the unchanged natural input route on standard MSX1 NTSC/PAL.
Only retain it if the gain warrants the complexity; do not claim a path to60Hz
from a component microbenchmark. The present mean costs require improvements
across several stages, not one isolated conversion.

## Reproduction

Research utilities: `scripts/atari800_reference.py`,
`tools/atari800-reference-probe.c`, `tools/atari800-antic-trace.patch`.
Build the pinned emulator locally with autoconf/automake, `./autogen.sh`,
`./configure --target=libatari800`, then
`make -j4 CFLAGS='-O2 -Wno-error=macro-redefined'`. The warning override addresses
an upstream ULONG macro redefinition under Apple clang; it changes no emulation
logic. Apply the trace patch with `git apply --unidiff-zero <patch>` before the
final build and link the probe against
`src/libatari800.a -lz -lm`. Record the compiler and binary hashes.

Use a private config containing `MACHINE_TYPE=Atari 400/800` and `RAM_SIZE=8`.
Run from a fresh ignored capture directory with `FB_ANTIC_TRACE=antic.tsv` and
`FB_GTIA_TRACE=gtia.tsv`; pass `-config <private-config> -ntsc` (or `-pal`),
`-800-rev altirra -cart <owner-input>`. Do not pass `-atari`, which resets RAM
to48KiB in this emulator revision. Capture tool checks mapped payload each frame.
Analyze with the project venv:

```sh
.venv/bin/python -B scripts/atari800_reference.py \
  --car references/roms/frostbite_atari800.car \
  --capture outputs/atari800-research/ntsc-hardware \
  --out outputs/atari800-research/ntsc-hardware/research.json
```

Public metadata: `references/atari800-research-result.json`. Raw captures and
offline exploratory models stay under ignored `outputs/atari800-research/`.
