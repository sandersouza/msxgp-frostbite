# Direct enemy bands — issue #42

P-C is a correct private checkpoint, not original-speed acceptance. Relative to
M-C it improves active source cadence4.87% NTSC /5.35% PAL. Ice preparation falls
19957→14255 NTSC cycles, while enemy primitive work remains21499. Replace that
whole band path next, preserving pixels, actors, mechanics, source/input/audio
order, SCREEN2 roles and player/mask. P-C remains sealed as the control.

## Representation

Keep the original source copy driver, dirty predicates, cached geometry lookup,
I's exact horizontal/vertical packet generator and generic overlap constructor.
Replace enemy primitive traversal/publication with a fixed-row transaction.

Each page/lane retains an exact group/variant/color identity. The group byte
covers0..65 (33 source groups times2 reflection states). On a changed identity,
generate all six normalized mono masks once and publish two24-byte PGT
segments. Publish complete CGT segments only when the owner color changes. Build
and publish the six existing typed metadata keys after required IO, then publish
the new owner identity. No per-cell dictionary lookup is needed for mono names.

Fixed segments (bank,first ID before PAGE offset): lane0=(2,3)/(2,6),
lane1=(1,16)/(2,0), lane2=(1,10)/(1,13), lane3=(1,4)/(1,7).
Lane1 coarse1 starts atY128: normalize its first source packet row into the lower
physical segment, with a zero upper segment. This also initializes upper CGT and
metadata coherently across later color/height changes. Pad missing third columns
and absent rows with the verified zero geometry pattern; do not invent pixels.

For each copy, select row context once, traverse nonzero descriptor cells, clip
column1 and wrap31→1 exactly. Mono cells write their fixed physical NAME ID
directly; cells already containing ice call the unchanged fusion path with exact
descriptor ID, copy ordinal and local column. Retain object ordinal marking.
Skip clean rows completely, including untouched NAME owners. Bear/UI/footer
paths retain their existing implementation.

## ABI, memory and measurement

New cache/work occupiesE800..E87F (128 bytes), previously guarded. Remaining
E880..F33F stays guarded; source RAM, C6 ABI, stack, DI and slot state remain
unchanged. Reclaim only documented obsolete J code for resident mapper wrappers;
append banked code after P's code within certified unused bank7 space and below
the unconditional F footer breakpoint atA800. Every mapper-changing call returns
through a resident bank7-restoring wrapper. Restore primitive-active flags.

Keep the existing independent fixed-role metadata/active-page checks, P's lazy
ice checker and the original CPU/pixel oracles. Prove geometry normalization,
all eight owners, phase/count changes and fused/boundary/dense scenes. Whole
NTSC/PAL frame costs include extra zero-slot writes and cache management. Extend
direct-CGT event accounting from fixed128-byte P fills to actual positive B
counts; the measured MSX loop is33 cycles/byte plus55, including M1 waits.

No original-cadence promise follows from a faster component. Review the whole
frame and tails before a human-test candidate or release decision.

## Measured revision: lazy actor keys

Q-C preserves every tested image/state but is3.71% slower than P-C in active
NTSC and3.56% slower in PAL. Per-tile typed metadata construction outweighs
the generic traversal savings. Retain this rejected experiment as evidence.

Ruling: Q-D/E retain only the complete per-owner group/variant/coarse/color
identity, published after both required physical planes. The selected template
profile draws floes before objects; its object fusion reads an old ice key,
never an old mono-actor key. Actor roles stay exclusive and are not queried by
the unchanged bear/header/footer paths. The old actor metadata remains FF.
The independent auditor reconstructs all six keys from each physical owner's
saved identity and the live immutable ROM directory, then verifies actual
PGT/CGT bytes and strict NAME generation just as before. Active-page guards
are unchanged. If a later renderer reads old actor keys, it must add a runtime
decoder or restore their eager publication before using this representation.

Coarse is encoded in identity variant bit7. This makes the Y128 bank split
explicit even in component cases outside the live source Y127/128 pair. The
archived complete geometry pool retains pre-compaction directory offsets;
the lazy auditor must read the live ROM roots/classes rather than those old
offsets. Original pixels remain an independent source-based oracle.
