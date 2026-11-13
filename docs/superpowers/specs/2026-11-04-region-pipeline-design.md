# Native region preparation — issue42 continuation

Owner authorization covers replacing architecture autonomously while preserving
graphics and exact original mechanics. Q-E is the sealed control. New inclusive
probes on the identical ROM reproduce every Q timing/state/VRAM byte: active
NTSC player lookup4115 cycles (variant search1714), dirty comparisons2870,
header keys1129 and header driver4213 (including igloo), igloo2504. Header
updates are infrequent but reach85271 cycles. Colour-only header updates do not
occur in this route; they must still remain correct. Earlier colour-only cost
was a hypothesis, not the measured cause of this route's slowdown.

## Approach and scope

More enemy-only work cannot solve the full budget; zero world leaves66928
NTSC cycles. Another global residency manager was measured slower. Select
fixed physical region transactions and prepared ROM data, following Seaquest's
separation of character/palette work and resident sprite reuse. This iteration
changes the header/igloo preparation and exact player-cache lookup together;
all simulation, input/audio, viewport, player sprites and black mask remain.

Keep the existing typed physical keys and independent pixel/owner auditors.
Header: a96-byte two-page region signature caches the40 packed column bytes and
three colour bytes already produced by the existing source selector. Restore
the fixed ten NAME IDs in each of three rows by contiguous copies. Rebuild typed
keys and invoke the existing checked publisher only for changed columns; force
all columns when the page's colour tuple changes. Publish the43-byte region
identity only after every required table write. Cold/invalid identities rebuild
all columns. The source selector/complete masks remain the original implementation.

Igloo: derive and prove all12 reachable interior background tiles × three
horizontal mask classes ×16 upper/lower bit pairs as exact16-byte PGT/CGT records,
using the independent constructor. A27-byte remap rejects unsupported edge
backgrounds: the builder check found176 three-colour failures in the broader
1296-combination proposal. No invalid records are fabricated. Each dirty igloo
row derives its six bit-pair choices and physical
roles directly. Zero masks leave the restored background NAME alone. Nonzero
cells compare their exact existing typed key, upload only on a miss, publish
the six-byte key after both planes, then set their exclusive NAME ID. Generic
typed constructors remain unchanged. Palette/aurora layering is baked into each
background-specific record, not approximated by a uniform colour.

Player: try the previous successful physical cache way for the exact seven-byte
key, then retain the original full search/replacement order on a miss. Keep
page validation, validity, six-pattern/band limits, static sprite ownership and
every existing fallback. This changes lookup cost, not sprite representation.

## Memory, mapping and bounds

Code executes from standard page3 RAM atE900..EFFF (maximum1792 bytes), loaded
once from a reclaimed contact-bank tail. This allows unchanged mapper-changing
helpers to return safely without consuming the remaining small bank7 code hole.
Region cache/scratch usesE880..E8FF128 bytes; Q retainsE800..E87F. Guard
F000..F33F832 bytes plus existing stack/ABI/source guards. Compare RAM code bytes
against the immutable ROM image during target proofs. No low-page RAM or BIOS
remapping assumption. Initializer restores bank1 and the C080 continuation ABI.

Use only fully reclaimed tails115..149, eachB800..BFFF, after authenticating the
contact14 arena. Bank115 holds code;116 onward hold the9216-byte reachable igloo table.
Every record is16-byte aligned; no record crosses a2KiB slab or16KiB mapper bank.
Assert all inherited I allocations and every byte outside explicit patch/data
ranges unchanged. Never use the partially occupied last contact bank150.

## Verification and delivery

TDD host tests pin region change masks, compiled igloo records, safe RAM guards
and cache lookup semantics. Actual Z80 checks cover cold/hit/one-column/palette
changes on both pages, all backgrounds/classes/bit pairs and repeated/cross-way
player hits. Then source matrix2115, dense1920 and matched NTSC/PAL full routes
retain original CPU/all-RAM/pixels, active VRAM/sprites, IO spacing and deadlines.
Use strict ROM/probe/raw-artifact binding, and measure the whole frame and tails.
Update a new workbook and preserve all predecessors. Integrate reproducible
source, review and select a useful versioned prerelease with exact human tests.
Do not stop work merely because one measured checkpoint has been recorded.
