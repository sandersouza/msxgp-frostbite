# Finite floe templates

Issue #14's fixed renderer is pixel-correct on the retained original observations
and still exceeds the frame budget. This optional compiler and its native asset
readers prepare a smaller amount of runtime work. Game integration and timing
acceptance remain pending.

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
The existing game constructor has not yet been extended for these records.

The packer preserves all 8,960 original row/bear grids and the static constructor
fragments. Complete floe programs replace the old primitive floe descriptors in
this layout. Its generic geometry lookup must reject that unused family.

All data fits in the same fourteen available asset banks, 3–13 and 253–255,
inside the 4 MiB ASCII16 cartridge. The prefix occupies 217,952 bytes and leaves
5,024 bytes before the reserved far-contact directory. That exact 6,400-byte
directory starts at bank 255:A700; its base table starts at B9C0 and ends at C000.
A future builder must use those addresses and preserve the packed bank contents.
The current fixed game uses a different, independently validated bank-255 layout.

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
