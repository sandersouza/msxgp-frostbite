# Compact edge row evaluator

Issue [#44](https://github.com/sandersouza/msxgp-frostbite/issues/44), source
`78c1d8a36563625f9c6b02c2f1536351b34b1ecf`.
This isolated evaluator consumes the masks from the separately qualified
[horizontal generator](compact-floe-edge-masks.md). It is unlinked from gameplay.

Five masks describe one row: old glyph, old-if-equal, new-if-different, exit and
visible. Equality compares complete bytes. Tag-1 reads glyph byte0 with the exit
mask. Tags0..18 select current and preceding glyph rows; at tag18 the preceding
byte is forced to zero. Every other byte tag misses. Reflection selects the
same source mirrored glyph page used by the preceding components.

The complete geometry corpus produces666distinct five-mask tuples. Every tuple
was executed with22tags(-2,-1,0..19) and all228player views. All **3,340,656 actual
Z80 calls** match. Independent review reconstructed the entire tuple domain from
captured native geometry, rather than trusting the tuple compiler, and verified
every native output, recorded hash and frozen source without blockers.

| Measurement | Result |
| --- | ---: |
| Code | 101 bytes |
| Shared player data | 518 bytes |
| New scratch RAM | 0 bytes |
| Cycles, minimum / mean | 99 / 341.089548 |
| Cycles, P95 / maximum | 419 / 419 |

The input frame is C790..C798: tag, pose, shift, reflection and the five masks.
The result is7/135. IX/IY/SP and interrupt state are preserved, with only bounded
stack writes and no mapper access. Cycles include the caller CALL and return
JP.641 synthetic host tests pass. The24,000-case horizontal-generator regression
retains identical ROM bytes and cycle statistics.

```sh
.venv/bin/python scripts/compact_floe_edge_probe.py \
  --build outputs/presentation/credit-reference-at/build-final \
  --out outputs/compact/my-edge-row-proof --stage row
```

Use a fresh ignored output path; `--limit N` is a smoke only. The generated
32 KiB Normal fixture is non-playable. See the
[hash-bound receipt](../references/compact-delivery/issue-44-edge-row.json).

Adding all preceding qualified components and counting player data once gives
7,870logical bytes, before alignment, callers and loaders. This is not a complete
game size. Eight-row accumulation, the combined geometry caller, electrical
shadow merge, enemy/shore edges and full-game cadence remain separate gates.
The accepted ROM remains unchanged; issue44 is In progress and PR45 is draft.
