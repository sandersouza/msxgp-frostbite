# Native floe edge program accumulation

Issue [#44](https://github.com/sandersouza/msxgp-frostbite/issues/44), source
`c7a08c188db55031006f1fa6d2f62d41c790bbb2` (the six bound source files are also
identical at322bd13). The component remains unlinked from accepted gameplay.

The complete captured native geometry corpus yields2,086distinct39-byte
programs: four masks for each of eight rows plus seven clipped visible masks.
The accumulator executes those programs with the original player glyphs.
Expected responses come directly from the accepted ROM's bit7 records, rather
than from the new row evaluator. Every program is tested with34Y values and
all228player views.

All **16,170,672 actual Z80 calls** match. Independent review reconstructed the
program classes, verified that all24,000geometry members retain identical source
responses within their classes, reproduced the complete expected corpus and
checked every final native output, recorded hash and frozen source. No blockers
were found in this declared component scope.

| Measurement | Result |
| --- | ---: |
| Accumulation wrapper | 126 bytes |
| Shared row evaluator | 101 bytes |
| Shared player data | 518 bytes |
| Program input / scratch frame | 39 / 11 bytes |
| Cycles, minimum / mean | 75 / 3,129.210546 |
| Cycles, P95 / maximum | 6,711 / 6,775 |

Y0 is an outside-actor sentinel. The eighth row has no regular visible pixels;
its clearing-line electrical masks still apply. IX/IY/SP and interrupt state
remain intact. CPU writes are confined to scratch and bounded stack; input
program bytes remain immutable, with no mapper/VDP access.

The first long run was deliberately stopped incomplete because write callbacks
for permitted scratch/stack writes made the planned corpus exceed its time
estimate. The revised observer watches exactly the same forbidden addresses,
verified over all65,536addresses.100k-case smoke outputs AND cycle bytes remain
identical. Four negative CPU writes independently trip the forbidden ranges.
This observer acceleration is not a game performance gain. Rejected/partial
evidence remains archived and separate from the final complete run.

```sh
.venv/bin/python scripts/compact_floe_contact_probe.py \
  --build outputs/presentation/credit-reference-at/build-final \
  --mask-proof outputs/compact/issue44-edge-native-full-01 \
  --out outputs/compact/my-edge-accumulation-proof
```

Use fresh ignored output directories. The mask proof must be complete and
hash-valid. `--limit N` is a smoke only. The generated32 KiB Normal fixture is
non-playable. See the [receipt](../references/compact-delivery/issue-44-edge-accumulation.json).

All qualified component code/data now totals7,996logical bytes with shared
player data counted once, before alignment and loaders. This does not prove
whole-game32 KiB fit. Fixture C800 program memory overlaps the current game's
NAME-page allocation and must not be treated as an approved integration layout.

Combined geometry calls, visible-mask preparation, bit6 shadow merge, actual
flat RAM placement and whole-frame IRQ/cadence remain integration gates. The
horizontal generator still costs up to24,969cycles before accumulation; a direct
query or other measured optimization may be needed. No compact game ROM, COM,
BIN or new whole-frame result is claimed. The accepted v0.0.30 remains unchanged.
