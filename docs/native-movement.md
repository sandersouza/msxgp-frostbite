# Native movement diagnostic

Issue 10 delivers native Z80 execution of the original post-visible phase
F476→F019, real MSX controls and a measured synthetic display. The supplied ROM
remains the mechanics authority. This boundary is narrower than a complete
original frame: visible-kernel preparation/acquisition, natural collisions,
original graphics/audio and whole-game acceptance remain pending.

The [CPU contract](../references/native-contract.json),
[compact frozen result](../references/native-result.json),
[post-review integrity audit](../references/native-integrity-result.json) and
[release instructions](releases/v0.0.3-movement.md) distinguish these scopes.
Old Seaquest evidence is never an acceptance input.

## Native CPU and input

The audited static translator emits source-addressed Z80 code, with original
carry, overflow, NMOS decimal arithmetic, 6507 read/write decoding and physical
source return-byte writes. No 6502 interpreter or complete Atari ROM ships.
Generic slices expose their declared observable stops and SP 86..FF ABI. Every
published mechanics case is required; losing a label fails instead of silently
reducing coverage. Isolated palette/magic-fish fragments do not make the visible
kernel part of the runtime contract.

The faster whole-phase path exposes only F000 cold reset and F476 with D=0,
SP=FF, ending at F019. Finite X/D/C domains and NZCV/IY liveness follow real
bounded call contexts. Proved non-wrapping indexed RAM uses IY=C000+X. Source
return words still reach the canonical stack mirrors; internal source SP is
implicit in call depth, with no TSX allowed and TXS restricted to the proved
top-level zero-clear loop. Unsupported entries/modes/stacks/stops reject.
The complete F019 CPU/RAM state remains observable and independently compared.

F5AD samples fire before source81 increments; F630 samples directions/console
afterward. The raw PSG/PPI adapter retains opposing directions and joins the
keyboard only to the source-selected C7=0/1 port. It preserves AF/BC/DE/HL/IX/IY/SP,
DI, slots, full PSG15 outputs and PPI-C. Trigger lines are released and common
pins lowered during reads, then exact prior outputs are restored. F1/F2 remain
held Reset/Select levels. F3/F4 are separate diagnostic view selectors.
The [MSX Technical Data Book](https://map.grauw.nl/resources/system/msxtech.pdf),
section1.7.12, specifies the PSG pin assignment; actual emulated devices validate
the implementation rather than preloaded expected mirrors.

## Display and timing

The 256 KiB ASCII16 cartridge uses bank0 resident code, bank1 startup assets,
bank2 native code/data, banks3..13 complete synthetic name rows and two padding
banks. Its 174080-byte row catalog plus code/assets exceeds 128 KiB. This trades
cartridge ROM for CPU time while retaining 64 KiB RAM/16KiB VRAM and standard speed.
No expansion, disk, turbo or additional sound device is used.

Ordinary colored tiles are shared between SCREEN2 banks. The crossing floe band
has 228 possible colored tiles in its top bank; the bottom has 260 candidates,
using 248 static IDs plus four dynamic slots for each inactive name page.
Only those page-specific slots may be patched. All other pattern/color data is
immutable during active frames. Complete 32-cell rows cover 34 variants, 160 X
positions, both widths/colors, wrap/clip and threat counts0..3. Name preparation
cannot alter the visible frame; SAT/page/backdrop commit is confined to VBlank.

The display follows native state through a read-only adapter. It reverses logical
row 0..3 to top/bottom display order, maps X using8+floor(3X/2), and uses the earlier
synthetic grid/masks. It is not the original-raster mapping prepared in9.
The coarse igloo and position/palette HUD are diagnostic. Changing presentation
does not change canonical coordinates or contact geometry.

`scripted_contacts` supplies only B0..B9/ED: no contacts in air; declared grounded
rows at E4=53/79/105/131. There is no X-overlap collision approximation. These
stimuli enable movement testing but cannot certify natural landings or a game.
Issue 11 needs genuine floe contacts for its build/entry route; issue 12 owns full
hazards/RNG/TIA-derived semantics. Visible-phase side effects must be reconciled,
not inferred from the post-visible continuous chains.

The measured frame includes real native steps, both input samples, mapper
changes, contacts, scene adapter, selectors, preparation and commit. NTSC/PAL
scheduling retains all required logical steps. No 10k surrogate or synthetic CPU
reservation is accepted as native timing evidence.

## Reproduce

Use the existing [macOS setup](toolchain.md), pinned tools and `.venv`. Keep the
4096-byte original at ignored `references/roms/frostbite.bin` with SHA-256
`cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834`.
Commit producer changes before canonical captures; `--explore` marks WIP results
and cannot produce a release package.

```sh
make environment-check
make source-check
make test
make ci-verify
make render-build
make native-check
make native-phase-check
make native-input-check
make movement-check
.venv/bin/python -B scripts/movement_delivery.py capture --out outputs/movement/issue10-final
.venv/bin/python -B scripts/movement_delivery.py integrity --frozen outputs/movement/issue10-final
.venv/bin/python -B scripts/movement_delivery.py audit --frozen outputs/movement/issue10-final
.venv/bin/python -B scripts/movement_delivery.py package --frozen outputs/movement/issue10-final
```

The individual commands support investigation; the final capture driver repeats
the complete canonical sequence, binds clean source/build/helper/backend/profile
identities and freezes exact bytes. Later documentation/tag commits do not relabel
that producer. Existing version packages refuse changed files or contents.

For this frozen delivery the runtime/proof producer is `64c2cec6d37e5b988b0b86bc1d57836dbe43498a`.
The separate auditor producer is `fa128da6a0fe8babf6c6644ad84acf2050baff89`.
`outputs/movement/issue10-integrity/` seals complete raw artifact sets, including
machine profiles, OMR/device mirrors and structured receipts for all six injected
failures. Each failure is checked against its actual log or raw comparison and
expected stage/cause. Empty/subset manifests, missing files and fabricated
failure details reject. This audits the unchanged original captures, rather than
claiming a new runtime capture. The immutable primary bundle remains untouched.
The public six-file package is `outputs/releases/v0.0.3-movement-verified/`;
its `movement-integrity.json` links this audit to the original producer and ROM.
To inspect an existing seal, run `audit`; `integrity` creates a new immutable seal
and will refuse a changed producer or changed evidence at an existing path.

The generic CPU proof has 4497 cases including all 101 published mechanics cases;
the specialized phase proof has 1793. Both generic and specialized input paths
have 1354 actual-device cases / 2708 source-phase samples, including continuous
chains, poisoned mirrors and preserved peripheral/CPU state. An inverted port2
fire input must fail. Eleven 240-frame captures check every presented pixel,
native CPU / all 128 RAM bytes, source-state continuity, adapter values, visible
preparation invariance, SAT, 29-cycle I/O spacing, four slots, stack/heap, source
counts, consecutive frames and VBlank commits. Five injected pipeline faults
must be rejected for their intended reasons.

Raw source-derived assembly/data, native RPC cartridges, OMR snapshots and full
capture records remain local/ignored. Public CI runs synthetic unit/atlas tests
and unchanged original-free builds; it cannot reproduce the private runtime
proof without the supplied original. Manual viewing/listening, expanded slots,
physical compatibility and complete-game routes are separate pending evidence.
