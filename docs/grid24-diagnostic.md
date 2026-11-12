# Tile-aligned playfield diagnostic

The owner approved testing visual option 1 with easy rollback. This experiment
changes the presentation grid, keeping the supplied Atari 2600 ROM as the
authority for simulation, collisions, input and ordered sound events.

## Presentation change

Eight independent sea bands use a 24-pixel pitch instead of 26. Bottom-to-top
enemy anchors become 152/128/104/80 and ice anchors 168/144/120/96. Ordinary
anchors move by at most seven target pixels. Artwork, colors, counts, horizontal
motion and the black left mask are retained. The bear remains in tiles.

Bailey's complete sprite group receives one vertical translation. A monotone
contact lookup maps the original shore/ice/footer contacts to the new anchors,
including the source coarse offset. Pose-specific foot offsets are preserved;
no sprite is stretched or recolored. This is a declared presentation adaptation,
not a change to original jump physics or collision coordinates. The source clock
continues to run at about 59.92 steps/s.

## Implementation and allocation

The original v0.0.17 source closure, all 154 files, is unchanged. The additive
builder supports `--layout original|grid24`; original mode copies the exact
sealed v17 bytes. `--name-mode translated|prepared` preserves both measured grid
implementations. The prepared variant is the human-test candidate.

- Ice uses the original phase-zero patterns and owner records in banks 35..44.
  Each complete band occupies one NAME row; background coverage and old-SAT
  restoration masks use the new rows.
- 1,280 pretranslated 32-byte NAME slots occupy only banks 45..64:B800..BFFF,
  retired nonzero-phase ice-packet storage. The lower 14 KiB of each bank is
  unchanged. A speculative contact-decoder B800 read contributes only masked-off
  bits; an independent 5,120-case check confirms its output is unchanged.
- NAME selection occurs after complete pattern/color/owner publication. The
  original `x_name_row` routine performs horizontal rotation and edge clipping.
- Ice code stays within F43D..F5D1. The player bridge uses 6235..6244 before the
  live footer at6249. Its helper/512-byte lookup uses119:BC91..BFFF, after the
  igloo helper. No additional RAM or VRAM is allocated.

## Whole-route result against v0.0.17

| Measurement | v17 NTSC | Grid NTSC | v17 PAL | Grid PAL |
|---|---:|---:|---:|---:|
| Active complete pictures/s | 25.9009 | 27.7427 | 23.1226 | 25.3762 |
| Complete foreground mean, cycles | 69,756 | 62,612 | 74,907 | 65,685 |
| Foreground P95, cycles | 123,363 | 118,873 | 134,044 | 120,888 |
| Foreground maximum, cycles | 173,397 | 163,083 | 172,891 | 150,225 |
| WORLD mean, cycles | 26,010 | 21,563 | 28,461 | 23,213 |
| Complete ISR mean, cycles | 22,152 | 22,227 | 26,174 | 26,280 |
| Picture-gap P95, ms | 66.752 | 66.720 | 59.843 | 59.841 |
| Longest gap, ms | 83.442 | 83.441 | 79.780 | 79.779 |
| Grounded landings shown /26 | 14 | 15 | 13 | 13 |
| Endpoint Y shown /26 | 21 | 23 | 20 | 20 |
| Consecutive Y runs shown /286 | 209 | 220 | 198 | 215 |

Active throughput rises 7.11% NTSC /9.75% PAL; observed whole foreground falls
10.24%/12.31%. These use complete natural routes, not isolated helper costs.
Stage populations differ, so stage means are not paired CPU savings. Complete
ISR includes the final RETI and rises slightly. Long gaps barely change.

NTSC grounded coverage gains arcs 4/16/18/21 but loses 5/7/15; endpoint coverage
gains 12/16/23/24 and loses 5/20. PAL grounded coverage gains 15/19 and loses 7/13;
endpoints are unchanged. First post-landing age P95 improves 6 to 5 source steps
NTSC and stays 5 PAL. All 26 arcs remain in the workbook, including regressions.

A separate clean-start 620-step bear-chase prefix measures 14.2057 to 14.7859 NTSC
(+4.08%) and 13.7033 to 13.7033 PAL (no material gain). Its active window includes
level 4, 122 bear X values and all 8 poses. The unchanged one-player guard limits
valid coverage before step 630; this is not full 702-step or all-level acceptance.

The first grid variant converted NAME IDs at runtime and reached only
26.3158/24.0688 pictures/s. Prepared programs provide the additional gain.
Both variants and their evidence remain local and reproducible.

## Verification and remaining limits

575 host tests pass. The final ROM passes 2,115 source scenes, 1,920 derived density
scenes, 54 header cases and 2,115 ordered-audio intervals (3,499 source / 2,472 PSG writes).
Full NTSC/expanded-RAM PAL routes compare original CPU / all 128 RAM bytes, declared grid
pixels, physical owners and active-page protection. Generic 9 IRQ boundaries per
mode, 2 new-helper boundaries per mode and a rejected AF2-corruption control pass.
Directed IRQ runs deliberately delay rendering and are excluded from FPS.

Independent review rebuilds all three modes and checks 1,280 NAME slots,
12,800 rotations, 512 literal contact deltas, 5,256 ordinary player rectangles and
the contact spill cases. Separate natural before/after SAT checks cover 539
translations. The pixel oracle shares the declared layout model; the literal
lookup/SAT comparisons constrain that common-mode risk. They do not constitute
exhaustive death/fallback/all-level or physical-hardware acceptance.

Original fluidity and stable 30 FPS remain unmet. Manual controller/listening,
visual-layout preference and physical MSX1 checks remain pending. This candidate
is a reversible diagnostic, not permanent adoption of a visual compromise.

## Reproduction and rollback

Use new output directories; never overwrite a sealed evidence root:

```sh
.venv/bin/python scripts/build_grid24.py --base outputs/presentation/igloo-colors-ad/build-release --out outputs/presentation/grid24-local/build
.venv/bin/python scripts/presentation_grid24_check.py outputs/presentation/grid24-local/build outputs/presentation/grid24-local/ntsc ntsc
.venv/bin/python scripts/presentation_grid24_check.py outputs/presentation/grid24-local/build outputs/presentation/grid24-local/pal pal
.venv/bin/python scripts/presentation_grid24_check.py outputs/presentation/grid24-local/build outputs/presentation/grid24-local/matrix matrix 2115
.venv/bin/python scripts/build_grid24.py --base outputs/presentation/igloo-colors-ad/build-release --out outputs/presentation/grid24-local/original --layout original
```

For immediate player rollback, reload the unchanged
[v0.0.17 ROM](https://github.com/sandersouza/msxgp-frostbite/releases/download/v0.0.17-igloo-colors-diagnostic/frostbite-0.0.17-igloo-colors-diagnostic.rom)
and restart. Expected SHA256:
`c50a3131df056011af9a037b58624d9de84930b3474579b24d2137d736e9d562`.
No save conversion or installation is required. Runtime changes are isolated in
commit`fa26b79fece16b8b9bbc293523792aa31d4a40ed`; its parent and local backup tag
`codex/backup/42-before-grid24-20261112` preserve the prior source.

Read [human tests](releases/v0.0.18-grid24-diagnostic.md) and
[validation](../references/grid24-result.json). Evidence is under new
`outputs/presentation/grid24-af{,-research,-review}/`; the AF workbook appends
one sheet and preserves all 31 AE sheets / 775,979 cells and native features.
Issues 42/39/15/16 stay open. Next work targets remaining WORLD cost and long
preparation tails while tracking each landing, subject to the owner's layout test.
