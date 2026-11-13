# Compact native formats: first measured inventory

Issue [#44](https://github.com/sandersouza/msxgp-frostbite/issues/44).
This is an inventory and equivalence investigation, not a compact release.
The owner-approved v0.0.30 ROM and its published bytes remain unchanged.

## Storage and tested coverage

| Measurement | Bytes / result |
| --- | ---: |
| Accepted ASCII16 cartridge | 4,194,304 |
| Bytes other than FF | 3,988,416 |
| Complete all-FF banks / duplicate banks | 0 / 0 |
| Whole image, host zlib9 / LZMA6 | 1,470,283 / 736,804 |
| Fetch/data bytes observed across four routes plus source matrix | 58,708 |
| Observed during runtime / only during startup | 52,597 / 6,111 |
| Observed physical banks | 129 |

The 58,708-byte set is a **coverage lower bound**, not a complete executable.
Even those runtime bytes exceed the 48 KiB below the existing upper-RAM work
area. Copying the touched bytes or changing mapper metadata cannot deliver the
new formats. Concatenating just the observed values compresses to 28,336 bytes
with host zlib9 or 24,620 with LZMA6; these figures omit address information,
relocation, unseen states and a target decoder. They do not predict ROM size.

Physical read accounting separates identical CPU addresses in different ROM
banks. A separate CPU fixture confirmed that openMSX `read_mem` includes opcode,
operand and data reads while debugger reads do not trigger it. The observer
records actual ASCII16 register writes, begins at cartridge entry and separates
startup from `native_reset_done` onward. Old outputs were not regenerated.

| Observed storage region | Bytes |
| --- | ---: |
| Resident code and data | 6,623 |
| Fragment code and data | 1,360 |
| Native core, original data and renderer in bank2 | 8,729 |
| Reused contact-bank tails: current code/programs/graphics | 33,966 |
| Graphics, geometry or auxiliary data in other banks | 5,532 |
| Contact records / blocks / pointer trees / root shadow | 159 / 460 / 1,443 / 436 |

These are physical-storage categories, not exclusive function costs or proof of
all-state reachability. In particular, the apparently old contact banks also
contain current renderer code/data in reclaimed tails. Removing whole banks
would destroy live functionality.

## Collision tables: an exact reduction path

The historical table manifest declares 239 banks and 3,905,197 occupied bytes.
Later builds repacked block indices and reused tails; that old total must not
be mistaken for the current exclusively-contact footprint. The active reader
still uses the table representation (`src/floe_visible.asm`,
`src/hazard_contacts.asm`, `src/presentation_contact14.asm`). These tables are
not established dead code.

The current codec has 10,716 records, 59,246 blocks and 104,849 rows. Reading
all records from the actual ROM produces 321,480 meaningful record bytes alone;
host LZMA6 still needs 43,668 bytes for that pool. Exact structural changes are
necessary; simply compressing the existing pools is insufficient.

Three finite experiments establish the first replacement boundary:

1. **Separate the electrical bit6 channel by control, Y and absolute floe X.**
   Four 160-bit maps plus a 340-byte directory require **420 bytes**. All
   **8,704,000 emitted floe cells** match, across ten controls, 160 player X,
   34 Y indices and 160 relative floe X. The existing outside-actor sentinel
   alone is insufficient: it differs in 27,360 near-actor cells. Preserve the
   Y key and all exceptions represented by the four maps.
2. **Use a geometric routine for the principal floe contact channel.** The
   visible seven-row ice geometry against literal original player glyphs
   matches all **54,400 cells × 228 views** at interior player X80. A separate
   complete directory comparison finds identical pure bit7 rows throughout
   player X25..134. This gives a concrete small-routine candidate. It does
   **not** establish edge, enemy or shore equivalence, nor Z80 execution cost.
3. **Reject an unrestricted glyph-OR shortcut.** It reconstructs 8,177 of the
   10,716 masks and fails on 2,539. Removing the remaining masks on this basis
   would change source collisions. Those cases remain explicit work.

The next implementation boundary is a compact collision/event routine, keeping
the original tables as its independent oracle. Prove edge, enemy and shore
behavior before eliminating their tables. Measure its actual Z80 IRQ/whole-frame
cost before integrating it; a host equivalence result is not a timing result.

## RAM, VRAM and loading constraints

The current cartridge exposes a resident 16 KiB bank at4000..7FFF and switches
the8000..BFFF bank. Upper RAM C000..FFFF holds canonical source state,
presentation caches, both NAME generations, staging, audio, IRQ code, snapshots
and stack. It cannot hold an expanded 4 MiB image. Historical `profile.ram`
guard reservations are superseded in part by later copied code and must not be
counted as free space. Keep the current64 KiB RAM requirement.

Known current reservations include NAME pages C800..CAFF/CD00..CFFF, keys
D000..D8FF, footer keys D900..DA07, staging DB00..DFFF, and fixed-clock state
E880..E8FF/code E900..EFFF. Later auxiliary code extends into high RAM. The
F000 source snapshot, F300..F37F stack/redzone and FFFF slot register need an
explicit final-layout audit; no flat payload address is assigned yet.

The existing16 KiB VRAM layout and both visible/hidden ownership generations
remain unchanged. VRAM scratch may be used during startup only after accounting
for restoration of patterns, colors, NAME pages, SAT and sprite patterns. There
is no new RAM/VRAM allocation or startup-cost change in this inventory stage.

Seaquest's `docs/native-delivery.md`, `scripts/build_disk.py` and
`src/disk/` provide audited loader precedents: startup-only backwards ZX0,
slot/subslot-safe RAM takeover, checksum/TPA checks for DOS and staged VRAM
loading. Frostbite needs its own flat layout and proofs; the Seaquest result is
not Frostbite evidence. COM needs a real disk-capable BIOS/DOS boot. BASIC BIN
needs a genuine FE/load/end/execute header and tested `BLOAD ...,R` entrypoint.

## Reproduction and evidence

Use fresh output names; existing output directories are rejected:

```sh
.venv/bin/python scripts/compact_inventory.py \
  --build outputs/presentation/credit-reference-at/build-final \
  --out outputs/compact/my-storage-audit
.venv/bin/python scripts/compact_live_probe.py \
  --build outputs/presentation/credit-reference-at/build-final \
  --out outputs/compact/my-ntsc-audit --mode ntsc \
  --baseline outputs/presentation/credit-reference-at-research/ntsc-final
.venv/bin/python -m unittest discover -s tests
```

Other observer modes are `pal`, `bear-ntsc`, `bear-pal` and `matrix`. The bear
route is the bounded620-step clean-start prefix before the unchanged one-player
guard at630; regular routes cover2252 steps. The matrix controls source RAM to
exercise2115 original scenes and is separate from natural-play evidence.

Four routes preserve byte-identical source CPU/RAM, owners, IRQ, picture timings
and captures versus sealed v30. The matrix preserves captures, ownership,
timing, scene and band buffers, with zero differing frames. These establish no
observer-induced gameplay or cadence change. They do not qualify a new loader,
all-state compact runtime or physical hardware.

The compact [receipt](../references/compact-delivery/issue-44-inventory.json)
binds the raw local results and producer hashes. Raw captures, originals,
generated bitmaps and intermediate geometry remain under ignored outputs.
Issue44 remains In progress. No compact ROM, COM, BIN or new release is claimed.
