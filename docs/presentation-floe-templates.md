# Finite floe templates

Issue #14's private `--templates` profile integrates these tables with the fixed
renderer. It matches all 2,115 retained original observations and still exceeds
the frame budget. Ordered PSG and combined game acceptance remain pending.

`presentation_floe_templates.py` constructs masks directly from the original ROM's
seven-line motion pattern and ten accepted control pairs. It compiles all sixteen
horizontal phases and eight vertical phases: 1,280 templates. Each contains both
source segments and all three copies. These tables describe geometry; gameplay
state and inputs remain live.

A template retains all thirty world columns before translation. Adding sixteen
source pixels rotates its columns by three, modulo thirty. The renderer must
translate first and then omit NAME column 1. Omitting that column at compilation
would lose pixels that become visible after translation.

Complete strips use at most fourteen distinct masks. A program contains sixty
nibbles: two rows of thirty cells, with zero for an empty cell and 1–14 for local
mask slots. There are 218 distinct programs. Physical programs have a 32-byte
stride, including two padding bytes, so no program crosses a mapper window.

## Asset layout

The logical atlas retains the original 12,098 pattern IDs and adds 1,441 complete
union masks. Two indices into a dictionary of four-byte halves represent each
logical eight-byte pattern. Floes additionally have a raw pool for faster reads.

| Namespace | Count | Meaning of index zero |
| --- | ---: | --- |
| Logical patterns | 13,539 | Empty pattern |
| Complete raw floe masks | 2,049 | A valid nonempty mask |

Packed template records reference the raw floe namespace. It must have its own
typed constructor identity; these indices must never enter the logical reader.
The profile's typed tag 9 identifies this namespace, including valid index zero.
The ordinary logical-pattern constructor keeps its previous identity.

The packer preserves all 8,960 original row/bear grids and the static constructor
fragments. Complete floe programs replace the old primitive floe descriptors in
this layout. Its generic geometry lookup must reject that unused family.

All data fits in the same fourteen available asset banks, 3–13 and 253–255,
inside the 4 MiB ASCII16 cartridge. The prefix occupies 217,952 bytes and leaves
5,024 bytes before the reserved far-contact directory. That exact 6,400-byte
directory starts at bank 255:A700; its base table starts at B9C0 and ends at C000.
A future builder must use those addresses and preserve the packed bank contents.
The older `--fixed` control uses a different, independently validated bank-255
layout at 8000/92C0. The two profiles select their own complete layouts.

## Verification boundaries

The host checks compare all 12,800 world translations with the previous strip
walker, which was checked against the retained original rasters. The physical
asset check reopens every emitted bank and checks complete masks, grids, static
fragments and contact-directory bytes.

The standalone Z80 reader check covers all 13,539 logical patterns and 2,049 raw
floe masks, plus two invalid indices per namespace: 15,592 cases. It checks all
eight returned bytes, carry/error flags, canonical state, descriptor state,
CPU ABI, heap, stack, interrupt state, slots and unchanged VRAM. Measured maxima
including the RPC are 1,389 cycles for the dictionary reader and 592 for the raw
floe reader. These are component timings, not a frame deadline verdict.

Original-derived tables and proof artifacts remain ignored under `outputs/`.
No new human-testable ROM or release follows from these component checks.

The integrated checkpoint ROM SHA-256 is
`b8d78dfa4803b111b5fed9c84d957fac55210c055c94fe79e4543f742d5b20fb`.
Its 2,115 full-scene checks include published keys versus real PGT/CGT bytes,
both NAME pages and unchanged active-generation bytes. Separate CPU-only replay
passes all 24,820 checkpoints of twelve immutable original routes. A continuous
120-frame keyboard run still records 24 overruns and 87 skipped VDP frames.
These failures prevent real-time acceptance; CPU-only replay does not execute
paced rendering or PSG.

The next private checkpoint rotates cached complete NAME rows and draws floes
before objects. Their source pixel rows are disjoint; shared SCREEN2 cells retain
the exact two-color literal fusion. Cache identities are published only after
all masks and sixty cached names are complete. The 512-byte cache is exclusive
to the two generations at DE00–DFFF. A standalone Z80 check covers 7,691 rotations
and invalid parameters, including both cached rows of every owner at every root
and page; its maximum is 1,248 cycles including RPC. The original weaker probe
did not cover every source-owner context and is not used for that claim.

Tag 9 misses now stream the complete eight-byte mask directly from mapped ROM.
They retain a previous CGT only when its published background, clip, foreground
and type prove the same complete FG:4 color row. First publication and every
foreground change write all eight color bytes before publishing the key. A
stateful actual-Z80 component checks 4,306 operations against the whole 2,304-byte
metadata pool and 16 KiB VRAM, including every mask, both pages/water banks,
all fifteen foregrounds, repeated/replaced masks and invalid grammar. Its maximum
is 2,030 cycles including RPC. The refactored reader again passes all 15,592 cases;
its new raw-mask maximum is 603 cycles including RPC (dictionary maximum 1,389).

The resulting private ROM SHA-256 is
`022f2c9dc65cbdcd11c9fe32fdf4b6e1c616d34afcf262f3fd0db1595a027deb`.
All 2,115 original full-scene cases and physical key/NAME/active-generation guards
pass with no pixel differences. Its controlled maximum prepare cost is 707,553
cycles. The 120-frame real-keyboard run still fails: maximum busy cost 732,155
cycles, 24 overruns and 72 skipped VDP frames. Its last world component falls
from 248,291 cycles before cached rows to 184,448; this smaller component is
still not a complete-frame acceptance. PSG and final integrated delivery remain
pending. This failed timing candidate is private research, not a human release.

Complete floe NAME rows also make their earlier background fill redundant. A
read-only predicate skips only those rows owned by a visible floe, using the
actual palette mapping and coarse phase. Its actual Z80 proof covers 24,772
operations: all rows, both phases, 256 synthetic color indices and blank states,
plus independently visible floe rows and invalid selectors. Whole RAM/VRAM and
stack/interrupt/slot invariance pass; maximum 277 cycles including RPC. The
initial 24,580-case probe used equal colors for all floes, so the expanded proof
adds isolated owners to distinguish a wrong source-row lookup.

Private ROM `5b104b0d715073aceaeccef339a0786bdbaddfb9d2d27df468c3162fe0e12bd8`
passes all 2,115 full-scene and physical-ownership cases; controlled maximum
prepare is 705,448 cycles. The last measured background component drops from
17,079 to 12,000 cycles while world content is unchanged. Its 120-frame keyboard
run still fails timing (maximum 729,297 busy cycles, 24 overruns, 70 skipped VDP
frames). This is another private optimization proof, not delivery acceptance.

The owned-strip publisher validates page, source row, count and foreground once,
then advances within that row's exclusive metadata and tile range. Individual
MISS uploads still validate raw IDs; each six-byte key follows its completed IO.
The standalone stateful proof passes 2,960 actual Z80 operations: every raw mask
in every row role and both generations, lengths 1–14, all foregrounds, shortened
and replaced strips and invalid bounds/IDs. It compares all metadata and VRAM,
including untouched slots. A later invalid ID leaves earlier offscreen keys
complete but returns failure; the driver cannot publish its strip identity.
The individual checked uploader separately retains its 4,306-case pass.

Private ROM `794dfdd2284567a1a23183f9c4830f082f3dc9f8bc2da2d8757c648a0cd3c2ed`
passes all 2,115 full-scene/ownership/active-byte cases (controlled prepare maximum
678,880 cycles). Its 120-frame keyboard run still fails: maximum 703,622 busy
cycles, 24 overruns and 64 skipped frames. The last world component is 155,406
cycles, including four floe strips at 103,482 cycles. Host suite: 449 tests pass.
This is measured progress inside Task 3; real-time acceptance and PSG remain open.

The raw reader now uses its two proved physical banks directly, with assembly
assertions on that layout, and an unrolled fixed-length copy. All 15,592 actual
reader cases pass; the raw maximum falls from 603 to 442 cycles including RPC.
The intermediate 488-cycle reader failed the 450-cycle component target and is
retained separately. All 61,480 raw typed-constructor cases pass again, maximum
1,296 cycles including RPC. Owned-strip publication passes again with this reader.

A 16-byte code table at E600–E60F expands a packed program once per cache MISS.
The pure decoder validates the destination owner and CID range before writes.
Its 40,967-case actual Z80 proof crosses every packed-byte phase, all eight cache
owners, ten CID bases and both water IDs, then invalid destinations/bases. Every
cache/table byte, carry flag and canonical/C6/heap/program/VRAM/SP/IFF/slot guard
passes; maximum 3,721 cycles including RPC. Compiler code grammar remains a
separate proof.

Private ROM `f3e25df1ba6fa8bc6a956a78f45c3bbcf17b27e40001ec56b9a2879e346ba5f9`
passes all 2,115 original full-scene/ownership/active-byte cases (controlled
prepare maximum 667,237 cycles). The fresh default control remains byte-identical
`0b98f3cb89e99f6e79ad9f1a3fb237c2cbfadebcd5759025a123ce33e09fcf78`.
The 120-frame keyboard probe still fails: maximum 689,076 busy cycles, 24 overruns
and 58 skipped VDP frames. Added inclusive cost counters reproduce the same
timing and identify the remaining work: last world 141,042 cycles, including
four strips at 89,118, publication 41,902, decode 14,768 and seven NAME copies
8,419. Nested costs must not be added together. Cold/header transitions and
player MISSes also exceed the budget. These artifacts remain private research.
## Fixed-owner packed NAME lookup (issue14)

The template profile now expands a packed byte with two immutable 256-byte
pages for each of its eight fixed generation/row owners. The 4,096-byte table
preserves every water/local-code result, original pattern ID, full strip and
VRAM transfer. It occupies existing bank255 space before the unchanged contact
shadow, leaving768 bytes. Cartridge size and the14 asset banks are unchanged.
Other valid first-CID/water combinations retain the generic decoder.

Actual Z80 checking passes40,967 complete cache/code-table/carry operations,
including all256 packed bytes for every owner and invalid destinations. The
2,048 fixed-role cases reach at most2,749 cycles including RPC against a
3,000-cycle microbudget. The generic path's maximum is3,879; this microbudget
does not apply to it or imply a complete-frame deadline. The checker requires
the actual optimized entry to have been assembled; a missing-path negative
rejects a table-only build. The isolated mapper unit maps page2 explicitly,
matching the game's actual ASCII16 window rather than reading unmapped RAM.

Combined private ROMe8661659cf383827d70a031e960db8c0b83a42a79d518535d742f3257715649d
passes all2,115 source-backed full-scene/physical ownership cases with zero
different images, maximum592,187 preparation cycles. Its actual source-audio
integration also passes all3,499 ordered source writes and2,472 PSG writes.
The120-frame keyboard probe improves571,692→567,804 maximum busy cycles and
48→47 skipped frames;22 frames still exceed59,736 cycles. Last-frame world
cost falls141,042→137,154. This remains private research that fails real-time
acceptance. The default control remains byte-identical0b98f3cb89e99f6e79ad9f1a3fb237c2cbfadebcd5759025a123ce33e09fcf78;
489 original-free host tests pass.
