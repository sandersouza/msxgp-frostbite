# Equivalent rendering optimizations — issue #14

[v0.0.9-performance-preview](releases/v0.0.9-performance-preview.md) is published
from source `12e204e6ecf6403fed63fd0e2f8c602ef84099a4`. Its exact 4MiB ASCII16
ROM has SHA-256 `838b67ae6ba4c7cbed72f643f64f78b45bb404a1e43b395f36331343f6656ae6`.
All four fresh public downloads match the sealed package; the 0.0.8 ROM is
freshly downloaded and unchanged. [Validation](../references/presentation-performance-result.json),
[publication receipt](../references/presentation-performance-delivery.json) and
[bounded performance research](../references/presentation-performance-research.json)
retain the exact identities and separate evidence scopes.

**Original-speed gameplay remains unfinished.** This continues issue #14 on its
existing exclusive branch/chat. It does not close the issue, transfer ownership,
merge to main, qualify full gameplay or start #15. The original mechanics,
complete graphics and standard MSX1 hardware requirements remain binding.

## Changes and independent component checks

- Retain ten complete 16-byte font-mask pairs with 60 bytes of validity/glyph/
  fragment metadata at E700..E73B. Color and header band changes reuse identical
  masks. Validity is published after the complete replacement; initial cleared
  metadata cannot turn zero glyphs into a false hit. The independent synthetic
  font proof checks 17,641 whole cache/tile/metadata/carry/error cases, including
  all glyph pairs and bands. Repeated masks peak at 1,615 cycles versus the
  previous approximately 3,954-cycle mask-and-tile operation.
- Select already validated bear/object roles using a resident PAGE/screen-row
  context table, then compare the complete six-byte key without a loop. The
  public resolver keeps its bounds checks; physical IDs, fusion ordinals and
  complete tile transfers are unchanged. The native publication proof checks
  1,488 whole metadata/VRAM/NAME/ordinal cases, with 138 covered cache hits at
  most 1,098 cycles, below the 1,100-cycle component budget.
- Compile 384 resident background flags. A fast igloo merge is allowed only
  when all eight PGT rows are FF, every CGT row has identical nibbles and neither
  nibble is 14. Edge/mixed/foreground-14 backgrounds retain the generic merge.
  A zero-mask half retains its original bytes. Global background uniformity was
  explicitly disproved before implementation. The native typed proof checks
  10,033 whole cases, including 5,924 igloo cases across all uniform background
  identities and every mask byte. Igloo peaks at 1,748 cycles versus 3,564;
  the attempted generic direct-address variant still failed the 2,000-cycle
  budget and was superseded by the certified uniform path.

These are isolated component costs, not frame qualification. Fresh integration
uses the canonical ROM with rebuilt contact tables and no exploratory reuse.
No actors, source updates, visible geometry, audio events or required VRAM data
were removed. All expected 16-byte tile payloads remain exact.

## Integrated evidence and limits

501 original-free tests and exact-source CI41646324578 pass. The ROM passes
all 2,115 complete source images/physical ownership cases, independent sea4/
ice5 contrast, 24,820 complete original CPU/all128RAM checkpoints across twelve
input-only routes, and 3,499 ordered source/2,472 physical PSG writes. Zero
canonical state injections are used in those native routes. The extra-audio-event
negative is rejected. The fresh previous progression control stays byte-identical
to 0.0.6 at `1223931972bd7e0ec02a8c66805cb30ac0defaad1abd71dd67c9c8a7746be5f6`.

Controlled whole-scene preparation peaks at 553,107 cycles versus 599,614 in
0.0.8. Both 600-frame standard keyboard probes still fail cadence; exact
overruns, skipped VDP frames, visible commits and budgets remain in the attached
validation and release notes. The fixed mapped-image proof is separate from
real-time display behavior; slowdown and tearing are not resolved.

The separate private original-input-only research sequence reaches 430 NTSC /
390 PAL blue-floe frames in 600 outputs. Every 601/717 source CPU/all128RAM prefix
checkpoint matches; all per-output logical-step counts equal the previous ROM.
NTSC improves from 37.91 to 38.78 source updates/s (+2.30%); PAL from 39.20 to
40.18 (+2.51%). Rates use logical steps over the measured commit intervals,
excluding the unmeasured first interval. These modest sequence-specific gains
are not universal speed ratios, completed-game evidence, simultaneous full-view/
audio qualification, manual play or hardware acceptance. The measured new rates
remain about two thirds of original speed. Both PAL updates remain ordered.

## Reproduction and continuation

Original inputs and derived captures remain local/ignored. The canonical build
is `outputs/presentation/performance-canonical-a`; its source fingerprints bind
all producers to the tagged commit. Local receipts use the `performance-` prefix:
matrix-a, contrast-a, audio-a, cpu-a, pace-{ntsc,pal}-a and seal-a. The seal's
private manifest binds the raw artifacts; only ROM/build.json/validation.json/
SHA256SUMS are published as release assets. The research adapters and raw traces
are separately hashed in the public research summary and are not canonical
all-view delivery producers.

Run the existing build/matrix/audio/CPU/pace/contrast tools against the supplied
local catalogs, then seal with `presentation_preview_delivery.py` and the local
`performance-config-a.json`. Public CI uses synthetic inputs only. Never replace
this version's bytes; another useful test ROM requires a new tag and release.

Next work remains equivalent complete floe/world/player preparation and complete
combined original-route/view/controller/PSG cadence acceptance on NTSC and PAL.
Tasks 3/4 remain open; final acceptance and the single final independent review/
integration remain pending. Human visual/listening/physical feedback is requested
in the release, not inferred from automation. Legacy cleanup remains #17.
