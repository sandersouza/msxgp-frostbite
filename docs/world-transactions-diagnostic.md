# Final ice NAME and compact enemy transactions

The T diagnostic fixed the source clock but did not meet original presentation
cadence. Passive whole-route profiling identified world preparation as the largest
foreground cost. Ice used52148cycles per active snapshot, enemy primitives40251,
while fusion used only1615. Optimizing fusion alone would address the wrong cost.
The Seaquest reference uses prepared lane patterns and short NAME publication;
this implementation applies that separation to Frostbite's original geometry.

The V builder consumes exact T and explicit public-chain K/I companions. It
compiles692final60-byte NAME programs for the four legal lane/coarse phase pairs
and both generations. Four directory tails occupy banks116–119; data occupy
120–141. All missing entries remain zero and fail closed. The original K identity
cache remains; packed30-byte scratch loading becomes unnecessary.

A byte per group/variant encodes the exact2/3columns,1/2rows and nonzero atlas IDs:
8448entries occupy banks142–146. The new cursor retains original wrap/left clipping
and zero-cell advancement. A shared cell performs the original full lookup and
fusion using the exact row-local ordinal, current NAME pointer and geometry ID.
Removed ordinal-map writes have no live consumer in the compiled template-first
path; the generic floe emitter is excluded. Both physical generations and all
active PGT/CGT/SGT/SAT/NAME protection remain unchanged.

New scratchE834/E835 lies inside the already declared Q region. The code appends
to T's initialized and guarded RAM image, which now totals688bytes. New mapper
writes call the existing IRQ-safe tracker. The source IRQ, PSG order, snapshot,
commit cap, player sprites and left mask are unchanged. Every modified tail was
verified empty; all inherited live I allocations are checked byte-for-byte.

Source `a43e2f1b265ef956ee154e82a198a17f9831a220` builds ROM
`fbf81a5eafa536f95497be22c787812046cf59a38eb962ee28230b3fc8f9ec99`.
Reproduce using the public canonical F→Q chain and T builder documented in
[fixed-clock diagnostic](fixed-clock-diagnostic.md), then:

```sh
.venv/bin/python scripts/build_world_transactions.py --base T_BUILD --chain PUBLIC_CHAIN --out NEW_BUILD
```

The finite-domain independent review found one Important error path: a failed
full geometry lookup branched before restoring three saved register pairs.
`presentation_world_fault_check.py` deliberately forces carry at the real lookup
return. It rejects the previous ROM and accepts the reordered POP/conditional
jump. POP preserves flags, so normal-path size, addresses and cycle count remain
the same. Final proofs and hashes bind the corrected artifact. No second review
or acceptance is inferred from a normal-input domain that never hits that error.

Whole-route and active-picture rates, disjoint foreground costs, gap statistics,
receipt hashes and workbook identity are in
[world-transactions-result.json](../references/world-transactions-result.json).
The gain is modest and the original presentation target remains unmet. Human,
audio, controller and physical acceptance remain separate. Issue42stays open;
publication is a diagnostic delivery, not a merge or gameplay acceptance.
