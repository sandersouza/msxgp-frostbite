# Prepared bear row metadata AM

Same owner-authorized autonomous Issue42/root sole writer, clean v24 runtime
48be6de/ROM4686...55c5be, delivery0f43049,186bound sources/52sealed roots.
Preserve source CPU/RAM/input/PSG/graphics/current palette and exact v24 rollback.
No new visual compromise; overall stable30NTSC acceptance remains open.

Passive v24 NTSC bear data (five natural buffers matched) show WORLD35,055cycles,
ai_entry20,184inclusive; ai_bulk18,322 includes7,277upload and1,780strided-ID
preparation. The remaining bulk work is certification, per-row geometry/address
arithmetic, clearing24key bytes, then rebuilding the same keys per cell. Whole
bear foreground74,126cycles and27.0953FPS; this is the next measured target.

Test lossless prepacked metadata instead of clear-then-rebuild. For each of96
actual v24 256B bear records compile192B: day72keybytes, night72, six original
strip indexes12, original12 padded logical IDs24, twelve padding bytes. Each24B
row holds four six-byte keys: all255 for empty/padded cells; otherwise IDlo/hi,
original bg136/129day or128/131night,clip0,color15,last0. Three-column records
keep nine IDs+three trailing zeros in p_geo_ids, but fourth key per row is FF.

Original132..143proposal is REJECTED before ROM writes: banks142..146 contain
LIVE enemy occupancy, explaining30of2115poison mismatches.149hasLIVEP0patterns;
150partialcontact/I allocations and151+unrepackedcontacttree are protected.
Use only132..141 (ten192Bpackets per2KiB tail,96total), subject to safe-only
poison proof. A96x3far directory in replacementbody112 maps originalrecordID
(bank67..78,H=B8..BF) to unaligned192B packet pointers. Do NOT use LDLoffset;
all row offsets use16-bit HL+DE. Body112 retains admission/certification/strip
upload/fallback; original body102/general paths unchanged. Rewrite only49B
helperEF78..EFA8 (bank115initializer mirror): HL+156 copies24IDs, then HL-36
copies12strips; metadata-copy helper maps/restores112. Estimate42B fits49;
ai_bulk_upload EFA9 is protected, RAMoccupancy1777/1792 unchanged. Each dirty
row uploads original64B strip before copying24key bytes; original nonzero NAME
loop retained, includingIXstrides andC50D where inexpensive. No new RAM/VRAM.
C500strips/marker andp_geo_ids scratch layout unchanged. Originalp_tf_cache/
p_tf_column retained. Caller/reg/scratch/mapper and hardware IRQ safety need
proof; no earlier frame-gain estimate applies until full measurement.

All frame/caller register liveness, mapper112 return, and actual hardware IRQ
boundaries require proof. Preserve harmless original IX scratch if inexpensive;
never change caller-dependent outputs on an assumption.

First audit exact packet semantics/retired tails/helper ABI with independent
read-only design review. RED→GREEN bounds/empty-key/source-layout tests, additive
builder/ASM/model/test186parentsunchanged. Internal finite and original matrix,
full NTSC/PALregular/bear profiles and all26landings before promotion. Reject
without useful whole-route gain. If qualified,593+tests/density/header/audio/
IRQ/negative/CI/cleanrebuild/nativeindependentreview; workbookAM preserves38tabs,
versioned release/WebMSX/exactROM/hash/source/human tests. Keep all prior assets,
Issue42/39/15/16 open, PR43draftstacked41. No stable/all-level/owner/hardware claim.
