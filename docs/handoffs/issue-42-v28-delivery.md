# Issue42 — viewport edge delivery

Same Issue42/root writer and `codex/feat/42-native-renderer`; no next issue,
checkout transfer, merge or close. PR43 stays draft/stacked on41. Owner feedback
after v27 reported premature P0 left clipping and right-enemy overflow at left.

- Runtime: `ece9a5aa395592ac143255dfd618ac46d1b14b4c`,225 source files.
- ROM: `e85b8bc13ebd07888b91d66fc76677ca3e7d210182d40c242cdd6c1a5c2dafd8`.
- Workbook: `9f0e92a73c40256ebca73cfcba6a6a8316bc67bf32e94a5884a0e55d6b67e949`.
- Native review: `6f6d838d9a9bef81cd48ff6139863d4dbfee0c6c09f6bfdbaf5172b113f8d592`.

P0 cut5 plus a physical SGT first-byte mask clips exactly at X16. Enemy native
rows stop at column31, while each separate copy still normalizes normally.
Standing shore programs are source-derived into the old120..126 reservation:
576 cases,239 patterns,134 records,max4 entries. Private P0 keys160..167 avoid
aliases. Public eligibility/AK code remains byte-identical. Helpers use52 bytes
of existing ECC0..ECFF padding. No new hardware or source mechanics changes.

The fallback-only prototype31f16d8 was rejected: correct pixels but75k-cycle
sprite preflight when the bear dragged P0 through X7/4/1. Its local build/profile
controls remain. Final artifact is `outputs/presentation/viewport-ar/build-prepared-final`;
the older `viewport-ar/build-final` is an unreleased rejected control.

Whole regular cadence32.6575→32.5982 NTSC/31.0586→30.9991 PAL (~0.2% overhead).
Bear29.6980→29.6978 NTSC/25.0791→25.0789 PAL is unchanged at0.01FPS precision.
Grounded24/26 NTSC and17/26 PAL, endpoint25/26 and24/26 remain unchanged.
NTSC consecutive Y runs261→260/286. Uniform/all-level30FPS and owner/physical
acceptance stay open. Different picture populations are not paired CPU savings.

619 host tests;2115 source/2115 density/2272 terminal-edge/54 header cases;
2115 exact ordered audio intervals; four source-exact natural routes and four
five-buffer-identical passive profiles pass. Independent review:2232 literal
packet-pixel cases,40960 P0 and131072 key calls,124 actor continuations,
1344 cache scenes/384 expected warm hits,16 real IRQ boundaries and rejectedAF2.
Clean rebuild and two exact-source CI checks pass. The43-tab workbook preserves
42 historical tabs/798479 cells/native parts,0 errors/2 mutations/5 views.

Raw/current evidence: `outputs/presentation/viewport-ar-research/qualification.json`
and `comparison-prepared-04.json`. Current native proof is sealed under
`viewport-ar-prepared-review/seal.json`; rejected native proof under
`viewport-ar-review/seal.json`. Their102/121 files are immutable. All73 prior
roots/21900 files were verified unchanged. New release/download/browser evidence
is recorded separately in `references/viewport-edges-delivery.json`.

See `docs/releases/v0.0.28-viewport-edges-diagnostic.md` for exact human tests.
After delivery, keep all published bytes and v27 rollback unchanged. Next work
remains WORLD/NAME and P0 spikes toward consistent presentation cadence. Do not
change source movement or shorten the complete-frame measurement route.

## Published delivery

[v0.0.28 prerelease](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.28-viewport-edges-diagnostic)
contains the exact ROM, workbook and four provenance/checksum files. All six
fresh root downloads and six independent downloads match the reviewed packet,
API digests and runtime tag. Documentation source is
`cde706e33701588b8e3ee57560847fa3980694c4`. v27 assets and notes are unchanged.

Independent prepublication receipt: `8da7d290fe55f0a8bf484fdb03426388d344f44a6aa81c0a4f0741998599cdbb`.
Independent postpublication receipt: `5e1b22a6cbc46dcb99a09e56d6a613f09090af77b83d6f0bb77f55ddeaafb14b`.
Actual desktop WebMSX loads the exact published ROM as ASCII16/MSX1A/60Hz and
displays the game after F1. The scoped browser is closed. This is launch-only
evidence; listening, fluidity, mobile, owner and physical acceptance remain open.

GitHub issue/PR bodies and Project7 were freshly checked. Issue42 is open,
In review; PR43 remains draft, unmerged and stacked on41. All independent
writers have stopped. New AR evidence roots are sealed separately from the
73 immutable predecessors; see `outputs/presentation/viewport-ar-seals.json`.
Exact public delivery receipt: `references/viewport-edges-delivery.json`.
