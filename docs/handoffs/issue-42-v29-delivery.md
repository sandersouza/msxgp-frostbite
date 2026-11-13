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
