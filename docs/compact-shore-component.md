# Compact shore contact component

Issue [#44](https://github.com/sandersouza/msxgp-frostbite/issues/44), source
`3d9a17341023ae207d24fa4f893d8a23670b3e35`.
The isolated shore/bear kernel is unlinked from the accepted game. It is not a
complete compact cartridge, COM/BIN executable or whole-frame timing result.

The compiler reflects each original eight-bit bear row before doubling its
pixels, clips the result against the player and shares the resulting17-row
footprints. The original19-row visual glyph remains intact: its final two rows
are verified blank in every source alias used here. The electrical shadow
channel is zero across the qualified domain.

The caller must enforce player X25..151. Distance is `playerX - bodyX`, where
`bodyX = (bearX + (bearX < 15 ? 6 : 1)) % 160`. This source positioning quirk
must survive integration. Native inputs are mode0..5, Y0 or12..46, distance+7
in0..22, player pose0..5, shift0..18, player reflection and an unused zero byte.
The result is7 or135. IX/IY/SP and interrupt state are preserved.

| Measurement | Result |
| --- | ---: |
| Code | 137 bytes |
| Data including shared player glyphs/offsets | 2,747 bytes |
| Shared player data | 518 bytes |
| Distinct17-row footprints | 123 |
| Host cells, each with228 player views | 4,267,200 |
| Actual Z80 calls | 1,132,704 |
| Cycles, minimum / mean | 81 / 827.225277 |
| Cycles, P95 / maximum | 1,362 / 1,540 |

Expected outputs come independently from the accepted ROM's active shore
directories and electrical records. All native outputs match; write guards
admit only the bounded stack. There is no mapper access. Cycles include the
caller CALL and return-path JP and are component costs, not a game speedup.
635 synthetic host tests pass. Independent review verified the complete native
result, all recorded hashes and frozen sources without Critical/Important blockers.

The floe and ordinary-enemy fixtures rebuild with byte-identical ROMs. These
rebuild checks each execute one native case; their earlier complete native
proofs remain distinct. Adding all three components and counting shared data
once gives **6,451 logical bytes**, before alignment, callers or loaders. The
accepted4 MiB game and all232 baseline sources remain unchanged.

```sh
.venv/bin/python scripts/compact_floe_probe.py \
  --build outputs/presentation/credit-reference-at/build-final \
  --out outputs/compact/my-shore-proof --component bear
```

Use a fresh ignored output directory. The generated32 KiB Normal fixture is
non-playable and exists only for automated component calls. Initial missing-entry
failure and smoke evidence remain local and are separate from the final corpus.
See the [hash-bound receipt](../references/compact-delivery/issue-44-shore-component.json).

Edge contacts, copy/row dispatch, flat runtime layout, cartridge/DOS/BASIC loading
and whole-game qualification remain pending. Issue44 stays In progress and PR45
stays draft. The current component result does not justify a new human ROM release.
