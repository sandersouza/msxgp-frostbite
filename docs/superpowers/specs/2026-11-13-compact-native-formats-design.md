# Compact native formats — measured migration

Issue: #44. Accepted control: v0.0.30, ROM SHA-256
`e75535923a5751e3f4924dc7a3a2f762041b825efb7a5336650d35890cd3ff1d`.

The owner authorized autonomous execution, a complete 32 KiB mapperless
cartridge attempt, and real MSX-DOS COM / BASIC BLOAD BIN delivery. Preserve
accepted graphics, mechanics, input, PSG and cadence on a standard MSX1 with
64 KiB RAM / 16 KiB VRAM. The accepted ROM and sealed evidence stay immutable.

## Approaches and engineering decision

Changing the mapper label or removing trailing FF cannot convert this runtime:
its banked pointers are executable dependencies. Compressing the entire banked
image also leaves the decompressed working set and bank-switching unresolved.

Use a shared flat runtime, following audited Seaquest loader principles, after
measuring its required data. Reduce live tables through exact representations
or equivalent routines; use startup decompression only when the expanded
ROM/RAM/VRAM budget fits. This is an engineering choice within the owner's
authorized scope, not a claim that 32 KiB is already feasible.

## Inventory before runtime changes

1. Bind image, metadata, symbols, source files and tools to exact hashes.
2. Count padding and duplication, separating stored size from semantic data.
3. Passively trace physical ROM reads and mapper selections during fresh
   regular/bear NTSC/PAL routes. Compare source, ownership and timing buffers
   with the sealed control to detect observer effects. Tested reads are a lower
   bound, never proof that unobserved bytes are dead.
4. Audit the contact decoder and renderer table formats independently of route
   coverage. Derive ROM/RAM/VRAM budgets and identify startup-only data.
5. Define the concrete flat layout and replacement equivalence gates from that
   inventory. Do not remove a table on trace absence alone.

## Delivery gates

A Normal ROM contains the complete game within 32,768 bytes and has no mapper
dependency. COM and BIN execute the same runtime, with real DOS/BASIC loading,
documented slot/stack ownership and reset/exit behavior. Original-derived
outputs remain ignored. Public tests use synthetic inputs. Testable candidates
receive versioned prereleases, exact hashes/source and human loading tests.
No release is needed for read-only inventory work.

Source-state/input/audio equivalence, physical picture ownership and NTSC/PAL
whole-frame timing must pass before promotion. Emulator and physical-hardware
acceptance remain distinct. A size miss remains open and explicitly measured.
