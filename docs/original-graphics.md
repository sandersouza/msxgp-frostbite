# Original graphics and MSX1 asset fit — issue #9

The local extractor prepares original Frostbite graphics and an exact mapped-pixel
SCREEN 2 fit. It does **not** integrate them into the native cartridge. The latest
downloadable ROM remains the synthetic v0.0.2-renderer diagnostic, unchanged.
Offline asset fit is not real-time rendering, gameplay or hardware acceptance.

## Frozen original execution

Input:4096-byte supplied ROM, SHA-256
`cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834`.
Clean extractor/mapping producer:`82ac6a37447b65ef132c8d9b9370f85f95ae8e43`.
[Compact report](../references/graphics-result.json) binds every local helper and
contract to that Git revision and pins the ALE0.12.1 binary. Seed1,frame_skip1,
sticky probability0; two fresh emulator instances independently repeat every
fixture, full serialized state/RAM and exact source/target artifact hash.

Canonical local directory:`outputs/graphics/issue9-final/`.
Its `evidence.json` SHA-256 is
`10c41e91c7fea93b5c40997f7ab67ce3a23b2b9d71d7479f93cfd6ab4e75ec45`.
Each run retains its initial full state,544 raw TIA frames, before/after RAM,
full post-frame states, mapped pixels, actual16KiB VRAM and independently decoded
target pixels. The catalog and generated PNGs remain ignored/local. Public CI
uses synthetic tests and never fetches the original or publishes derived pixels.

| Controlled family | Cases per independent run |
|---|---:|
| Player selectors, reflection, terminal shape/color offsets | 296 |
| Bear animation and reflection | 16 |
| Four row kinds, both phases, bounded sway and reflection | 64 |
| Digits/temperature/reserves | 10 |
| Alternating player HUD and level20 symbol | 2 |
| Sixteen igloo stages and completed-door variants | 20 |
| Palette paths and sixteen floe shaping phases | 96 |
| Player/bear edge overlap | 8 |
| Row copies and floe wrap at eight edge positions | 32 |
| **Total** | **544 × 2 = 1,088 captured frames** |

These are controlled presentation fixtures, not a claim that every combination
is naturally reachable. There are398 decoded table views,382 nonblank raw-table
to-original-raster matches and4 explicitly blank views. Blank/font/footer raw
windows are additionally retained in the catalog; complex HUD/footer placement,
igloo/playfield and floe shapes come from actual original execution. No blanket
claim that raw tables alone reproduce raster placement is made.

## Extraction and observed anchors

`scripts/original_graphics.py` verifies the immutable ROM before decoding:

- Player shape pointers at FCAA and color pointers at FCB0; nineteen descending
  rows, six selectors, reflection and terminal EB/F0 offsets. Duplicate selectors
  are views, not distinct art. Terminal controlled combinations do not establish
  gameplay reachability.
- Bear pointers at FEE7, nineteen descending rows and NUSIZ double width.
- Row pointers at FD0A and colors at FD00, eight descending rows and bounded sway.
- Digit windows FF00–FF4F, blank/status views and footer windows FF68–FFBF.

The independent raw-mask check found player source anchor(64,88) for E6=64,E4=60,
bear(101,58) for E8=100 and logical row0 object(32,160) for D4=32. Logical rows
descend from3 at the top to0 at the bottom. These are measured interior anchors;
clipped/overlap fixtures retain the whole actual raster rather than assuming the
interior formula works across every TIA positioning phase. Gameplay/collision
coordinates and the original ROM are never changed by the mapping.

Igloo C0–C4 are prepared from CD in the previous overscan. A first candidate
changed the selector but captured the old construction:15 requested stages had
the same raster. That candidate was rejected. The final suite settles one source
frame for igloo fixtures, reapplies controlled selectors, and requires16 distinct
visible construction images. Day/night also requires actual sky/shore source
codes132/10 and128/2 for levels0/7; three source LSRs select level bit2. Intent or
RAM changes alone cannot count as visual coverage.

## Coordinate and palette adaptations

The [machine-readable contract](../references/graphics-contract.json) specifies:

- X:`8+floor(3*x/2)`, preserving all160 source columns through alternating1/2-pixel
  widths, with an8-pixel target border. The original HMOVE blanking in the raster
  is retained; it is separate from software collision coordinates.
- Y:source7–185 maps to0–178;189–201 maps to179–191, both1:1. Only source0–6,
 186–188 and202–209 are omitted, and every omitted row must be completely black.
 Three blank separator rows are removed. A naive7–198 crop lost the footer's
 line199 in a right-edge fixture and was rejected. Main gameplay is not scaled
 or forced onto the benchmark's eight-pixel band grid.
- Palette:use measured indexed-frame RGB. Chromatic colors choose the nearest
 nominal TMS color excluding black/gray/white; this keeps dark water blue.
 Achromatic colors use contrast bins:<128 black1,128–175 gray14,>=176 white15.
 This retains dark bear, gray igloo and white shore/ice. The shore brightens and
 source grayscale levels merge; it avoids a gray igloo becoming magenta or
 disappearing into an equally mapped shore. These are deliberate adaptations,
 not identical Atari/TMS RGB or physical composite color acceptance.

The source and decoded target previews were inspected locally. Source RGB depends
on emulator palette configuration; see [Stella palette documentation](https://stella-emu.github.io/docs/index.html#Palette).
TMS constraints follow the [TI data manual](https://computers.baffa.tec.br/pages/datasheet/TMS9918A_TMS9928A_TMS9929A_Video_Display_Processors_Data_Manual_Nov82.pdf).

## Actual VRAM resource fit

The compiler uses the measured #8 address layout:patterns0000,colors2000,
name pages1800/1C00,SAT1B00 and SPT3800. It reserves the complete16KiB image,
deduplicates each64-line bank independently and enforces at most192tile IDs/bank.
The maxima are45/31/47tile IDs in the three banks,3sprite rectangles per scanline
and352sprite-pattern bytes. Across544frames,6,032displaced background pixels
were repaired; final mapped-pixel loss is zero. The same address layout
does **not** imply compatibility with #8's cache-ID families or dynamic update ABI.

SCREEN2 background bytes permit two colors per eight-pixel row. Keep the two
most frequent colors, then restore every displaced mapped pixel through bounded
16×16 sprite color planes. Count full sprite rectangles on each scanline, including
transparent parts; reject a fifth slot or more than32sprites. Both the new decoder
and #8's existing independent VRAM decoder must equal the mapped original pixels.
This preserves every final mapped pixel in all1,088 frames; palette adaptation
and the explicitly black-row crop remain the presentation differences.

No source-core/input/audio cost, upload cadence, live framebuffer, listening or
physical MSX result is inferred. The compiler packs complete static snapshots;
it is not a feasible proposal to upload16KiB per game frame. The synthetic #8
worst NTSC margin remains747cycles and cannot fund unmeasured native integration.

Original bear width is16 source pixels/24 target pixels; #8's synthetic bear was
narrower. Its all2048resident sprite bytes, cache phase tables and few ROM padding
bytes cannot silently accommodate all original variants. A native adapter must
choose background bear/active pattern uploads or another measured allocation,
retain original source collision geometry, and rerun every layout/width/SPACE,
NTSC/PAL, prepare invariance, VRAM spacing and guard gate. Fused-row compositing
remains unmeasured; no impossibility of exact original Y placement is claimed.

## Reproduce and inspect

Use the existing pinned `.venv`; no new package installation is needed.

```sh
make source-check
make test
# Commit intended helper/contract changes before canonical execution.
.venv/bin/python -B scripts/graphics_reference.py --out outputs/graphics/my-fresh-run
# Or choose a fresh ignored destination automatically:
make graphics-check
make ci-verify
```

Each destination must be fresh and stay below ignored outputs/. Canonical execution
refuses a dirty producer, verifies all helper Git blobs before/after capture,
rechecks the ROM/backend, reads saved artifacts back and compares full independent
runs. The six deliberate failures cover source-frame identity, actual requested
state, saved source pixels, table pixels, target VRAM pixels and a fifth sprite.
Host tests additionally reject missing initial states, bad crops, invalid colors,
bank boundaries and unrecorded over-color loss. Unknown raw fields are excluded
from the compact report.

No new ROM was built or offered by this issue, so no new release is created.
For human runtime tests continue using the immutable
[v0.0.2-renderer release and its controls/checklist](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.2-renderer).
Original/target preview PNGs are local research artifacts, not accepted manual
emulator or physical evidence. The next native step is [#10](https://github.com/sandersouza/msxgp-frostbite/issues/10).
