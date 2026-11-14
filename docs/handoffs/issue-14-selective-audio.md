# Issue 14 — selective audio delivery checkpoint

The owner requested louder drowning, freezing and bear-pursuit effects through
the issue44 chat. This superseded the temporary return to issue39 research.
Issue14 is the sole writer; issue39 and44 are not editing this checkout.

Implementation commit: `001f802f9589c826d5e0463834b6b09ca8dc6329`.
Branch: `codex/test/14-native-presentation-acceptance`; PR46 references #14
without closing it. Release notes: `docs/releases/v0.0.32-selective-audio-diagnostic.md`.
PR46 merged at `71d4e824b66cf1a1fa3b28920614630c8c7d698f`. The prerelease is
published; all seven assets were freshly downloaded and verified byte-for-byte.
Local publication receipt: `outputs/releases/v0.0.32-publication.json`.

The requested1.25 amplitude factor is quantized to PSG4->5, nominal sqrt(2),
approximately+41.4%. Do not describe the result as exact25%. All four original
store sites are attributed independently; other source writes/latches and
mechanics remain unchanged. No sticky gain flag, extra voice or dithering.

Selected delivery: `outputs/compact/issue14-effect-gain-delivery-04`.
All five files match tested build03 byte-for-byte. ROM32KiB Normal SHA256:
`cfce4fe274165e1cd0be0a0ba76ef0a48e38c7ed7fec10de84c673335c2b82b4`.
The default builder without `--effect-gain` still reproduces v31 cold images;
retain the explicit option for reproducing v32. v31 and prior artifacts stay
immutable. Build01 failed contiguous allocation; build02 failed cartridge size;
neither is positive delivery evidence. Build03 has only ten payload padding
bytes. Do not claim room for another feature without measuring compression.

Public evidence receipt: `references/compact-delivery/issue-14-selective-gain.json`.
It seals14 positive results, including new qualifier-source hashes checked
before/after execution. Raw original routes/capsules/derived data remain ignored.
Fresh build04 archives the maintained sources of the implementation and checkers.

Passed:5724 actual-ROM callbacks including256 clear entries;2115 original
CPU/audio intervals;2115 image cases;1920 density scenes;NTSC/PAL IRQ boundaries;
continuous705-state bear route with source/physical audio;2257-state regular
route in both families;four actual DOS/BASIC boots. Regular picture cadence
decreases about0.20% NTSC/0.21% PAL; bear cadence is effectively unchanged.
This is not original picture-cadence parity or human listening acceptance.

## Preserved pending work

- Unrelated `scripts/build_compact_grid_experiment.py` remains untracked and
  untouched. Never stage it with the delivery.
- `tests/test_native_console_route.py` remains untracked, from the earlier
  unfinished console/attract work. It imports `native_console_route`, which
  has not yet been implemented. Full local discovery ran729 tests with this
  single import error; the other728 passed. This draft test is not part of
  the delivered commit. Original-free GitHub CI covers the committed suite.
- The previous continuous-audio draft is now implemented, committed and used
  by this gain qualification; its source observer still supports unmodified
  original captures and exact complete-capsule comparison.
- The earlier24-route native batch on v31 is complete at
  `outputs/compact/issue14-native-acceptance-03/batch.json` (all24 exit0).
  Those results do not certify live audio on all12 routes or physical ports.

## Remaining gates

Record v32 human A/B listening for all three effects, ordinary sounds and
silence. Finish bounded attract/re-entry and console/opposite-input acceptance
without modifying gameplay by inference. Keep #14 open/In review while those
gates remain; do not fork/close #15, #16 or cleanup #17 automatically.
#39 still owns the unmet numerical original-cadence objective. The historical
masked4MiB baseline is not the current accepted product.
