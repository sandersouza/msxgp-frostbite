# Compact floe edge masks

Issue [#44](https://github.com/sandersouza/msxgp-frostbite/issues/44), source
`c79bfb2c3bbd5513b07f7e2acdc0360e98681935`.
This is an isolated horizontal mask generator, unlinked from accepted gameplay.
Its native proof does not yet include player-view/Y convolution or combined
electrical outputs. It is not a compact game cartridge or a disk executable.

The source clock model reproduces hidden HMOVE samples, stopped counters,
adjacent-byte equality and delayed GRP/ENAM writes. It adds these effects to
the existing floe footprint clipped to visible clocks X8..159. The first exact
explicit lookup/DAG experiment needed51,159bytes and was rejected. The analytic
replacement uses a universal160-entry rectangle-window table plus small masks,
control clocks and a generic bit-reversal page.

The native input is control0..9, relative floe X and absolute floe X in the
existing seven-byte component frame. It derives player X and writes four masks
for each of eight rows: old glyph, old-if-equal, new-if-different and final-glyph
exit. The declared edge domain is player X0..8 and154..159, all10controls and
all160absolute floe positions. Mask generation is independent of player Y/view.

| Measurement | Result |
| --- | ---: |
| Code | 652 bytes |
| Data | 666 bytes |
| Reserved scratch / mask output | 32 / 32 bytes |
| Native horizontal cases | 24,000 |
| Output per native case | 32 exact bytes |
| Host edge cells, each with228 views | 816,000 |
| Cycles, minimum / mean | 19,352 / 20,766.211625 |
| Cycles, P95 / maximum | 23,104 / 24,969 |

Host proof compares every declared edge cell against the accepted ROM, including
the existing visible footprint and separate scalar shadow proof. Three earlier
host representations agree: a complete source-clock model, a sparse-event
version and the analytic masks. An initial clock model missed the one-color-clock
GRP/ENAM write delay and differed in726horizontal columns; that rejected result
remains archived and is not accepted evidence.

Every actual Z80 mask output matches. Guards admit writes only in declared
scratch/output memory and the bounded stack. IX/IY/SP and interrupt state remain
intact, with no mapper or VDP access.640 synthetic host tests pass. Independent
review reproduced all host assets and masks and verified the final native
outputs, recorded hashes and frozen sources without correctness blockers.

Timing includes the caller CALL and return-path JP. Maximum cost is about
**6.98 ms before convolution**. This is substantial: accepted-game promotion
requires measured whole-frame IRQ/cadence equivalence and may need optimization
or caching. Small storage alone is insufficient. No whole-game performance gain
or preservation is claimed by this component proof.

```sh
.venv/bin/python scripts/compact_floe_edge_probe.py \
  --build outputs/presentation/credit-reference-at/build-final \
  --out outputs/compact/my-edge-mask-proof
```

Use a fresh ignored output path. `--limit N` is a smoke check only. The generated
32 KiB Normal fixture is non-playable and used for automated component calls,
so it is not a new human-testable game ROM version. See the
[hash-bound receipt](../references/compact-delivery/issue-44-edge-masks.json).

Next gates: native view/Y evaluator, combined floe electrical output, equivalent
enemy/shore edges and copy dispatch, flat runtime/loaders, complete size ledger
and full NTSC/PAL regressions. The accepted v0.0.30 remains unchanged. Issue44
is In progress; PR45 remains draft.
