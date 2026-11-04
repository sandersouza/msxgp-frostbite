# Prepared band packets — issue #42 architectural ruling

The shared residency implementation O-B passes 3840 target lifecycle cases,
2115 source scenes, 1920 density scenes and both original-input routes. Its
manager makes complete gameplay slower. Reject it as a delivery architecture;
preserve all evidence and M-C. The host miss model did not predict CPU costs.

Next representation: prepared ROM packets and fixed band destinations. Preserve
the existing pixels, fixed physical roles, source logic/input/audio, all actors,
phases, colors and original cadence objective. No player tile conversion.

## ROM capacity without extra hardware

The existing contact codec stores16 record indices of at most10715 in32 bytes.
Pack each index into14 bits (28 bytes per block), retaining each bank's512-block
index range. A bank-local slot address becomes28*(id&511). All record values and
the root/tree indices remain exact. A resident decoder extracts the selected
14-bit field. This changes storage and lookup cost, never collision semantics.

Each of115 full block banks gains a contiguous2KiB tail; the partial last bank
reclaims1464 bytes while preserving its inherited I allocations. Use80 full tails for1280 fixed
128-byte floe packets: physical bank35+phase*10+delta_index, addressB800+root*128.
Each packet includes up to112 original PGT bytes, count/program, and a far pointer
to its original raw-key list. Original contact records/roots and live asset banks
remain independently verifiable. New decoder cost counts in the whole-frame
ledger; this is not a free-space or free-CPU assumption.

## Fixed band transactions

Retain complete tuple identities and fixed NAME roles; remove per-tile ice cache
resolution/publication. Publish the ready contiguous PGT strip in one transfer.
Retain a color identity per page/row and publish the complete16-slot CGT interval
only on color changes. Stale unreferenced PGT cells remain harmless.

Replace full per-slot ice metadata writes with a per-owner pointer/count record.
Enemy fusion reads the original raw key lazily using the physical ID's fixed row
and generation, then uses the unchanged pattern/overlap constructors. Non-ice
metadata and role rules stay intact. Independent audits reconstruct all referenced
ice masks from exact source-derived packet records, protect active PGT/CGT/SAT/
SGT, validate source CPU/all128RAM and compare complete original pixels.

Start with a lossless contact-codec target harness before combining renderer
changes. Measure complete-frame costs, including decoder overhead, before
deciding whether the prepared-band representation merits a human candidate.
