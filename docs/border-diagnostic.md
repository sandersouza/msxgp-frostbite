# Aligned sea border diagnostic

The owner tested v0.0.18 as stable with very small visual changes and authorized
option 3, continued autonomous work toward 29.97/30 NTSC, and WebMSX test links.
The border diagnostic keeps v18 as an exact rollback control.

## Change

Seven black sprites formerly covered target X16..19 at Y64..175. Each consumed a
hardware sprite rectangle on its scanlines. The new version replaces them with
NAME column 2=black128 on rows 8..21, coveringX16..23. This crops four extra target
pixels at the sea edge only. Header/bear rows0..7 and the footer are unchanged.
P0 retains its original colors, grid24 translation, priority and mechanics;
as foreground, it can overhang that extra four-pixel border near the edge.

Cold and cached SAT append paths both omit the seven mask records. Full
eligibility and certified reuse clip enemy sprites at target X24/source X11.
Multi-copy boundary cases retain the exact tile fallback. NormalizedX0/raw160
cannot become the no-clipping sentinel. The obsolete mask rectangle is removed
from the scanline count; actual 16-row P0 rectangles and global SAT limits remain.

The border helper uses retired resident F57E..F5D1. Eleven left masks occupy the
retired 69E0 mask data; right masks A70B remain unchanged. Only the inactive CPU
NAME buffer is edited, followed by the existing dirty-row upload. No added RAM
or VRAM. All 160 v18 source files remain unchanged.

## Whole-route measurements

| Measurement | v18 NTSC | v19 NTSC | v18 PAL | v19 PAL |
|---|---:|---:|---:|---:|
| Active complete pictures/s | 27.7427 | 28.9237 | 25.3762 | 26.2082 |
| Whole foreground mean, cycles | 62,612 | 60,254 | 65,685 | 63,693 |
| Foreground P95, cycles | 118,873 | 114,027 | 120,888 | 113,949 |
| Foreground maximum, cycles | 163,083 | 162,793 | 150,225 | 162,982 |
| Complete ISR mean, cycles | 22,227 | 21,890 | 26,280 | 25,908 |
| Picture-gap P95, ms | 66.720 | 50.129 | 59.841 | 59.811 |
| Longest gap, ms | 83.441 | 83.441 | 79.779 | 79.778 |
| Grounded landings shown /26 | 15 | 17 | 13 | 13 |
| Endpoint Y shown /26 | 23 | 25 | 20 | 22 |

The underlying JSON/workbook keep all 26 arcs and exact counts. Throughput improves
4.26% NTSC /3.28% PAL; foreground means decrease 3.77%/3.03%. Stage populations
differ, so observed stage means are not paired CPU savings. Complete ISR includes
RETI. PAL's sampled maximum foreground rises 8.49%; long presentation gaps remain.

NTSC grounded coverage gains arcs 2/13/22 and loses 4. PAL gains 7/8/13 and
loses 5/15/16. Endpoint coverage gains 5/6/20 and loses 24 NTSC; PAL gains 2/6/8 and
loses 16. Consecutive Y runs shown rise 220 to 232 NTSC and 215 to 221 PAL. Landing-age
P95 improves 5 to 3 steps NTSC and 5 to 4 PAL. These are presentation differences;
original CPU/allRAM, source collision/jump rules, input and sound order remain.

The 620-step live bear prefix stays 14.7859 NTSC and improves 13.7033 to 13.9619 PAL
(+1.89%). Its level 4/all 8 poses/122 X active window is not all-level acceptance.
Stable 30 FPS and original fluidity remain unmet.

A second private variant reused preflight-invalid decisions. Its NTSC cadence
remained 28.923685 versus 28.923688 for the simpler A, so it is not promoted.
Both sources, exact ROMs and rejected attempts remain local. No atlas is part
of v19; an immutable white-ice table is the next measured research direction.

## Verification and delivery

579 host tests, 2,115 source scenes, 2,040 derived density/edge/P0 scenes,54header
cases and 2,115 ordered-audio intervals pass. Natural NTSC/expanded-PAL compares
4,507 CPU/allRAM checkpoints and 2,658 coherent pictures against the declared view;
owners and active-page protection pass. Independent review rebuilds all 165 source
files and passes 6,336 actual Z80 sprite/cache cases, four actual NAME cases and
10,560 original-glyph finite clipping cases. Synthetic rawX160 tests remain
separate from the unchanged source-view guard, which correctly rejects it.

Nine generic and two border/clipping real-IRQ targets per mode pass; AF2
corruption is rejected. Directed IRQ timings are excluded from FPS. Final
clean-source natural runs reproduce all five measurement buffers per mode.
Exact-source CI passes. The AG workbook preserves all 32 AF sheets and adds the
complete costs and 26 landings per TV mode. Native Excel is not exercised.

Source:`c863310fae363d561520dfd2138d07dc1948cefc`.
ROM SHA256:`26260606e1ecbdeed0a8c0d3ae7ef4eb37658341da3a0ab02cd52ac8a5286ac9`.
4 MiB ASCII16, standard-speed MSX1/64 KiB RAM/16 KiB VRAM/TMS9918/PSG.
All prior releases and 22 sealed evidence roots are preserved. Read
[validation](../references/border-result.json) and
[human/WebMSX tests](releases/v0.0.19-border-diagnostic.md).

For immediate rollback, reload the unchanged
[v18 ROM](https://github.com/sandersouza/msxgp-frostbite/releases/download/v0.0.18-grid24-diagnostic/frostbite-0.0.18-grid24-diagnostic.rom)
and restart. SHA256:`6677bb8ccc9caaf440b24df6a69fe9ecd7d206743645d738623e6cfedc8a219a`.
`scripts/build_border.py --mode original` copies those exact bytes. Use a fresh
output directory with the sealed v18 `--base`; never overwrite old evidence.

Issues 42/39/15/16 remain open. Owner border preference, manual listening,
all-level, original-fluidity and physical MSX1 acceptance remain distinct from
the automated checks. Continue native ice work toward the owner's target without
changing mechanics or reducing colors.
