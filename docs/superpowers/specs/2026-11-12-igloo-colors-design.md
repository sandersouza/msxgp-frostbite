# Igloo color-only update design

Owner authorization: 2026-11-12, implement igloo color-only updates, measure the
whole frame, update the workbook and publish a testable ROM. Execution remains
autonomous in the existing Issue #42 chat and checkout.

Base is exact v0.0.16, ROM SHA-256
`9d2ee2926bc8de7fd0d22b05e7ad334e76078141bfde997720adfb62414cc77b`.
Preserve all 151 parent sources through an additive builder/source pair.

Replace only the igloo driver's call to the generic fixed-role publisher.
The new handler derives the same inactive-page physical slot and metadata.
An exact key hit publishes NAME directly. A valid old igloo key with identical
masks, foreground and role can reuse PGT only if both backgrounds certify
PGT=FF and equal color nibbles other than14 on every line. It uploads an exact
precomputed eight-byte CGT and publishes the new key last. Cold, changed-shape,
nonuniform, invalid-context and forced-ID cases take the unchanged full path.

Use no new RAM or VRAM. A bounded resident bridge reclaims the remaining retired
typed-header continuation6212..6248, before live footer6249. The banked helper
and generated colors reclaim obsolete NAME-directory storage in bank119:B800..
BFFF. Native ice packets embed their page-specific far pointers; validate all
2560 pointers and the current header dictionary extent before reusing storage.
Return to bank1 through resident code; mapper shadow/IRQ restoration stays exact.

Alternatives: merely skipping PGT after generic construction saves less work;
rewriting the complete three-row igloo driver expands scope. The selected scoped
publisher keeps existing mask/layout generation, NAME rows and dirty semantics.
This implementation choice is the agent's, within the owner's authorized scope.

Whole-route NTSC/PAL source CPU/all128-RAM, pixels, owners, active-page protection,
IRQ boundaries, audio and density remain acceptance gates. Measure gaps and
landings as well as average FPS. No original-clock change or player-only update.
Publish only an exact-source qualified diagnostic; report any cadence regressions.
