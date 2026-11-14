# Compact ordinary-enemy contact component

Issue [#44](https://github.com/sandersouza/msxgp-frostbite/issues/44), source
`04a3454e4e05ae01a85c6526e6dfb3cf4ac9b1da`.
The component is isolated and unlinked from the accepted game. This is not a
complete mapperless ROM, a disk executable or a whole-frame performance result.

The implementation reads seven collision rows from the original enemy glyph,
rotates and masks each byte to implement the signed horizontal shift, and tests
it against the original player glyph. Player and enemy reflection are separate.
The eighth visual row remains visible: the earlier source latch read excludes
it from the common-profile collision response. The naive eight-row hypothesis
was rejected after 13,496 of 25,740 cells differed.

The exact scope is player X25..151, one original enemy copy, all33 shape offsets,
two enemy reflections, source Y36..61 and all15 signed distances. An outside-Y0
sentinel is included in native tests. Copy unions, edge coordinates, bear/shore
contacts and source-row dispatch remain separate work.

| Measurement | Result |
| --- | ---: |
| Code | 192 bytes |
| Data including shared player glyphs/offsets | 1,078 bytes |
| Shared data with the floe component | 518 bytes |
| Exact host cells, each with228 player views | 25,740 |
| Actual Z80 calls | 6,094,440 |
| Cycles, minimum / mean | 81 / 1,050.167082 |
| Cycles, P95 / maximum | 1,597 / 1,615 |

Cycle measurements include caller CALL and the return-path JP. They are
component costs, not a speedup versus the old game or a whole-frame cadence.
Expected bytes come from the accepted ROM's active ordinary common-profile
directory and electrical records. Every native output matches. IX/IY/SP and
the interrupt state are preserved as declared; guest writes stay within the
bounded stack, with no mapper access.

The unchanged floe fixture was requalified for1,193,944 calls. Its ROM bytes
and cycle statistics are identical to the preceding floe proof.633 synthetic
host tests pass. Independent review reproduced host assets and verified final
native outputs, recorded hashes and frozen sources for both components, with
no Critical/Important blockers.

Adding the two components' code/data and counting their shared518 bytes once
gives **4,085 bytes**, before integration alignment and loaders. That is a
component-storage ledger, not a linked whole-game image or a32 KiB achievement.
The accepted4 MiB v0.0.30 game remains unchanged.

```sh
.venv/bin/python scripts/compact_floe_probe.py \
  --build outputs/presentation/credit-reference-at/build-final \
  --out outputs/compact/my-ordinary-proof --component enemy
```

Use a fresh output path. `--limit N` is only a smoke test. The generated Normal
fixture is non-playable and used for automated calls, not a human ROM version.
The source and both input/reflection pages are frozen alongside the raw test.
Initial missing-entry/conditional-assembly failures remain archived locally;
they are not accepted evidence.

See [receipt](../references/compact-delivery/issue-44-ordinary-component.json)
and [floe component](compact-floe-component.md). Next: shore and edge equivalents,
then the flat runtime/loaders and actual whole-game regressions. Issue44 remains
In progress; PR45 remains draft.
