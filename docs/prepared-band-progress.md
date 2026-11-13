# Native renderer progress — issue #42

The owner authorized architecture replacement and resuming GitHub. Original
mechanics, pixels, actors, input/audio order and the unexpanded MSX1 target remain
the contract. Original speed is unfinished; #39/#15/#16 remain open.

## Decisions from real Z80 measurements

| Active original-input route | M-C NTSC | O-B NTSC | P-C NTSC | M-C PAL | O-B PAL | P-C PAL |
|---|---:|---:|---:|---:|---:|---:|
| Source updates/s |31.1855|29.0318|32.7029|32.4926|30.2506|34.2321|
| Mean complete busy cycles |111564|119890|106046|126631|136515|120046|
| P95 busy cycles |248515|284265|227532|267670|307368|247099|
| Worst active busy cycles |343145|421591|321144|367922|442361|349974|

O-B shared residency is correct but rejected: −6.91% NTSC /−6.90% PAL cadence.
Its lookup and lifetime work outweighed the offline model's reduced misses.
Keep the model as a hypothesis and the measured rejection as evidence.

P-C replaces per-tile ice resolution with immutable ROM band packets and lazy
physical-owner keys. It improves cadence4.87% NTSC /5.35% PAL. Ice preparation
falls19957→14255 NTSC cycles. The complete run still reaches481664 cycles; no
stable30/60Hz, original-time or physical acceptance follows. It remains an
internal architectural checkpoint rather than a selected human delivery.

Lossless14-bit contact indices reclaim236984 bytes inside the same4MiB ASCII16
cartridge. Eighty full bank tails hold1280 prepared packets. The partial last
contact bank also contains protected I enemy data; the repacker now preserves it
and both builders assert every inherited I allocation unchanged. The contact
algorithm/record values are unchanged; its measured decoder overhead is included.

## Verification on the exact P-C bytes

ROM SHA-256: `923219216c217c11b1eeed03d19c80e2c1a6702b369624c03cbda63b8269e0eb`.
This is a private patch experiment atop sealed M-C; inherited manifest commit
fields identify ancestors. Patch source hashes identify the actual experiment.
Public canonical-build integration is still required before release delivery.

- 947936 actual Z80 contact-field queries match sealed M-C, including non-FF packet
 tails at the last packed field. Direct32→28-byte packing is lossless.
- 30720 target strip cases cover1280 templates, eight physical owners and all15
 colors, including cold/hit/color/count transitions and full16-slot CGT growth.
- 2115 original-source scenes and1920 dense synthetic scenes have zero pixel
 differences, with source/ABI/VDP spacing/active NAME/PGT/CGT/SAT/SGT guards.
- 2253 NTSC /1886 PAL original-input presentations match every one of2254 source
 CPU/all128RAM checkpoints per route; all4139 original-model images match.
- Direct CGT event counters account for actual writes and setup. Standard stream
 cost is29 cycles/byte plus53 per call; constant fill is33 plus55 with MSX waits.
 Measured complete-frame costs include both paths and the extra contact decoder.

These are automated bounded routes and fixtures, not all-game, owner, listening
or hardware acceptance. Synthetic density is not natural highest-level evidence.
Original/generated assets and raw traces remain local/ignored.

## Evidence and next work

Private roots: `outputs/presentation/shared-ice-o/` and
`outputs/presentation/prepared-bands-p/`. Complete reports bind actual ROM,
CPU/RAM traces, timing, traffic, source fixture and physical-audit receipts.
P's final routes are `ntsc-c-io`/`pal-c-io`; they add explicit fill events without
changing the ROM. Failed early builds and diagnostics are retained.

The new O/P workbook preserves the historical M workbook as a separate immutable
file. Importing the complete history exceeded4GiB and8GiB authoring heaps, so the
focused continuation contains8278 paired frame rows,424 stage/function rows,
formula-backed summaries and an editable native chart. No historic file changed.

Next: direct enemy bands. Enemy primitive work remains21499 NTSC cycles/frame,
larger than the remaining ice cost. Retain exact copy/wrap/dirty/fusion behavior
while replacing generic mono-cell publication with fixed band transactions.
Then reassess the whole frame, including dirty-state9179, header6426,
sprites15207 and NAME/preparation5513 mean cycles. A useful candidate needs
independent review, canonical source integration and the versioned release tests.
