# Issue42 — aligned credit

Same Issue42/root writer, checkout and `codex/feat/42-native-renderer` branch.
The owner requests RETROWORKS at the right playfield edge, matching Activision's
height/baseline and lettering style; the later instruction explicitly removes
the hyphen. No new issue, checkout transfer, merge or closure.

Runtime `5ac94c5fb282596a20cb5a5dc8bd93064e9fdb22`; ROM SHA-256
`94e4ee71f2ef4021e9ec16c960fa258cae6d27d660c11f3005dde0d51d0473d3`.
Canonical build: `outputs/presentation/credit-as/build-final-06`.
229 source files retain all 225 v28 parents unchanged. Earlier AS prototypes
and their failures remain local controls; only candidate06 is delivered.

Fourteen prepared tiles use free bank2 IDs134..143/250..253, adding80 bytes
inside existing VRAM. X247 is the right edge; Y182..188 shifts to183..189 with
the original footer. The displayed phase occupies one byte from existing
reserved RAM, DA08; metadata splits DA09..DAFF as still reserved. Shared tiles
track the last displayed phase, independent of either page's dirty history.
PGT and seven CGT bytes change only during VBlank on an actual phase change.
The fast gate avoids mapper swaps otherwise. Source mechanics and audio are
unchanged. The fixed66AA..66F9 padding and bank65 tail are guarded allocations.

Evidence: `outputs/presentation/credit-as-research/qualification.json`,
`comparison-06.json`, four natural/passive routes and full native matrices.
Independent native review is in `outputs/presentation/credit-as-review`.
The v29 release includes PERFORMANCE.json; v28's43-tab workbook stays intact
as historical evidence. Uniform/all-level30FPS, owner and physical acceptance
remain open. Follow the release's focused footer tests before visual acceptance.

After publication, record exact downloads, tag/source/notes and rollback in
`references/aligned-credit-delivery.json`. Keep PR43 draft/stacked on41 and
Issue42 open/In review. Continue existing WORLD/NAME work after this delivery.

## Verified publication

[v0.0.29](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.29-aligned-credit-diagnostic)
contains the exact tested ROM and five provenance/performance/checksum files.
All six root downloads and six independent downloads match the frozen packet,
API digests, runtime tag and immutable documentation0f04560c. v28's six assets,
notes and historical workbook are unchanged. Native review is sealed with179
files, receipt `aee012607a8db874a23518064a4a43fdab2b17d0f8d441cca0fad38a1bd06500`.
Prepublication review: `13146c99b472bc26cb2099b3665e13602aaa572c13372b9040b7ae2bb9809f08`.
Postpublication review: `8a2d7ea02e908c08d4cb02193fc4b5e0788975d1d23a2d21c5ee29656a2f9ac4`.

Actual desktop WebMSX loads the exact published ROM as ASCII16/MSX1A/60Hz,
showing the game and aligned footer after F1. The scoped browser is closed.
This is launch-only evidence, separate from human/mobile/listening/physical
acceptance. Fresh GitHub issue/PR bodies and Project7 status were checked:
Issue42 open/In review, PR43 draft/stacked on41/unmerged. All writers stopped;
new AS evidence is sealed under `outputs/presentation/credit-as-seals.json`.
Public receipt: `references/aligned-credit-delivery.json`.
