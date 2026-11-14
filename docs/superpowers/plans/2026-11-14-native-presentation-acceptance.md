# Issue14 acceptance on the accepted native product

Baseline: merged main d445942; published v0.0.31 Normal32KiB ROM SHA-256
4ddec8fb72c6e744982864a997688f0de9a9f27e8221dd488083ab7d8f5ba04d.
Owner-approved fluency is retained. No runtime/default/format/performance change
is planned. This reconciles the historical issue14 plan with issues42/44.

## Remaining work

1. Verify existing exact-ROM matrix, header/density, IRQ and controlled audio
   receipts. Preserve their explicit limits and independently checked hashes.
2. Extend the qualification harness to retained original routes, including
   source-selected player input and complete terminal/restart predicates.
   Keep native loader/immutable memory/source CPU/all128RAM/graphics/ownership
   guards; prove adapter hook drift fails closed. No source-state injection in
   natural runs. Physical joystick ports are a separate test.
3. Exercise all retained natural routes in NTSC/PAL. Reserve actual independently
   captured tail points for PAL double steps; never fabricate padding states.
   Add original bounded attract/re-entry and simultaneous-input coverage.
4. Capture continuous source-event/physical-PSG histories against independent
   source replay, including PAL double steps. Controlled audio alone is not
   this claim. Keep manual listening separately pending the requested owner test.
5. Obtain focused independent review; run full host tests/source policy; publish
   a focused linked PR and accurate evidence ledger. No new ROM release for
   qualification-only changes. Close14 only when its own gates are met.

Implementation files: scripts/native_presentation_routes.py and its tests add
route selection without changing historical pinned producers. New evidence goes
under fresh ignored outputs/compact/issue14-native-acceptance-* directories.
The unrelated untracked build_compact_grid_experiment.py is not owned by14.

Issue39 retains numerical cadence parity;15 final timing qualification;16 final
full-game/hardware acceptance;17 legacy cleanup. These issues are not closed or
implemented here. Manual listening request refers to the exact publishedv31.
