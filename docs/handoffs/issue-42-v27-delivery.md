# Issue42 — v27 open playfield delivery

The owner resumed after the historical v26 stop and added the drowning-color
correction. Same Frostbite Issue42 chat/root writer and shared checkout on
`codex/feat/42-native-renderer`. No new issue, writer transfer, merge or close.
PR43 remains draft/stacked on41. Requested testable release is v0.0.27.

- Runtime source: `e42b737f0def8dd70be9b31712b776d83258fadd`,220 bound files.
- ROM: `78090dde8429a5bc6097e02cfaf278539e05ff68b9582d65e16d430d04334c8a`.
- Workbook: `1b5291b199c12e34548210e83b2c62193b02f546093a8f5f3f2ac8a21d6deadc`.
- Independent native review:
  `1a9493ba4f2046b40d49675a652f0649f68e758c1e03aba0be400a1d452ea754`.

Left stripe removed: native edge X24→16, both background programs normalized,
source-hidden X0 enemy copies skipped and X158/159 hardware wraps fall back to
native tiles. Immutable credit appends `- Retroworks` beside the original logo.
Its9 NAME cells are set only on dirty row23. Original adapted hat/skin/body
palette also applies during sinking; source silhouette and blue fade retained.
Five general planes occupy E780..E7F7; colors C4EB..EF avoid cache keys/mapping.
Normal recipe packet scratch C480 remains. No additional MSX hardware required.

AP skips one repeated native cache default; retired clipping work and redundant
credit publication removed. Whole regular NTSC/PAL cadence31.8277→32.6575 and
30.4636→31.0586. Foreground means51265→50075/52543→51258 cycles. NTSC grounded
landings22→24/26, PAL17/26; no previous landing/endpoint lost. Bear NTSC mean
62257→61535, but cadence29.8305→29.6980 with two long intervals instead of one.
PAL bear25.0791 unchanged. Stable/all-level30FPS, owner and physical acceptance
remain open. Population changes mean costs are observed, not paired savings.

615 host tests;2115 source scenes;2088 dense/edge cases;54 header transitions;
2115 exact ordered audio intervals; four complete natural/passive routes with
all5 buffers matching;1811 independent native calls and9 real IRQ boundaries;
AF2 and5760 credit corruption controls pass. Two exact-source CI runs succeed.
Clean two-stage rebuild matches the tested ROM. One trailing ASM blank line
was removed after measurements; the ROM bytes remain identical. The42-tab
workbook preserves41 historical tabs/796499 cells/18 native parts,0 errors,
2 mutation/restore tests and5 rendered views. Native Excel was not exercised.

Local evidence: `outputs/presentation/open-view-aq-research/qualification.json`,
`comparison.json`, four raw routes/profiles and retained failed internal probes.
Final build: `outputs/presentation/open-view-aq/build-final`. Independent review:
`outputs/presentation/open-view-aq-review`. Workbook: ignored outputs path ending
`-AQ/Frostbite-performance-budget-AQ.xlsx`. Earlier v26 and67 sealed roots are
read-only. No copied Seaquest evidence is treated as Frostbite acceptance.

Publish/retrieve verification and launch outcome are recorded separately in
`references/open-playfield-delivery.json`. Release notes/human tests are in
`docs/releases/v0.0.27-open-playfield-diagnostic.md`. Read those records before
continuing. Next: WORLD/NAME peak at source343→345 in the620-step bear prefix,
plus the remaining source318→320 gap and general player/WORLD spikes. Keep the
new border/palette/credit fixes, original source mechanics/PSG and exact v26
rollback. No further ROM should be released without full-frame measurement.
