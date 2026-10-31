# Atari reference reconstruction and reviewed state map

Issue [#3](https://github.com/sandersouza/msxgp-frostbite/issues/3), reviewed
against the canonical 4096-byte image, SHA-256
`cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834`.
Addresses below use the $F000–$FFFF mirrored disassembly window. The 6507
cartridge bus window is $1000–$1FFF; RIOT RAM is $80–$FF, also mirrored into
the stack page. See [inventory](reference-inventory.md) for identity/timing
limits and [machine-readable map](../references/disassembly-map.json) for
every RAM region and all 19 distinct JSR entry addresses/34 call sites.

## Reproduce the exact bytes

From the repository root, with the local canonical ROM and tools present:

```sh
python3 -B -m unittest discover -s tests -v
python3 -B scripts/reference_inventory.py
python3 -B scripts/reference_rebuild.py
```

The final command validates the immutable manifest **before** invoking tools,
stages a verified input.bin in a fresh ignored outputs/reference-rebuild/run-*/,
runs DiStella `-paf`, then DASM `-f3` (raw binary), and compares all bytes.
A successful assembler exit is insufficient: changed size or any changed byte
fails. The input is verified again after execution. Each tool has a 120-second
timeout; tool stdout/stderr, source, listing, symbols and rebuilt binary stay
local. `--distella`, `--dasm`, `--rom`, `--manifest` and compact `--output` are
explicit overrides; normal execution uses the committed canonical manifest.
Never rebaseline authority to make a mismatch pass. Failed runs remain local
for diagnosis and do not write a success report.

The [recorded run](../references/rebuild.json) contains exact commands, binary
hashes and generated-file hashes. A second fresh run produced the same 4096
bytes. Full generated-source hashes need not repeat: DiStella embeds time in
its header and DASM listings contain host paths. Their byte equality, not
textual reproducibility, is the reconstruction gate. Public metadata contains
no source listing, ROM bytes or original graphic tables.

Tool provenance checked locally:

| Tool | Source/build identity | Observed detail |
|---|---|---|
| DiStella | [johnkharvey/distella](https://github.com/johnkharvey/distella/tree/1015ae53b2d222320eb706c220186305fcac55dd), commit 1015ae53b2d222320eb706c220186305fcac55dd | Banner 3.02-SNAPSHOT; tracked source clean, untracked debugger symbols only |
| DASM | Homebrew Cellar dasm/2.20.17, exact executable hash in report | Executable banner says 2.20.16; record both, do not infer build identity from the directory alone |

No MADS or Atari 800 dependency was reused. The utility is new Frostbite code;
the Seaquest rebuild tool was rejected because it assumes different inputs.
DiStella's [documented heuristics](https://github.com/johnkharvey/distella/blob/1015ae53b2d222320eb706c220186305fcac55dd/README.md)
are evidence to review, not semantic proof. Do not use `-r`: relocating mirrored
references can change bytes. The pinned tool's source has `char file[50]` and
an unchecked filename copy (source/distella.c:91,217); an absolute input path
here reproducibly trapped. The short, verified private input name avoids that
backend limitation; the CLI regression covers long host paths.

## Classification and control flow

Static review walked the complete listing and cross-checked the five code
ranges with an independent py65 6502 decoder. All 1,769 instructions decode on
instruction boundaries, cover 3,374 bytes, and have valid direct branch/call/jump
targets. The other 722 bytes are data/trailing words. These are static facts
about this partition, not exhaustive executed-path coverage.

| Inclusive range | Reviewed use |
|---|---|
| F000–FBFF | Reset, visible kernels, overscan/audio, sync/input, gameplay and shared state routines |
| FC00–FCE9 | Actor image/color planes; pointer lows FCAA/FCB0; sky FCB6–FCBF; trajectory FCC0–FCDE; segment masks FCDF–FCE9 |
| FCEA–FCFA | Carry-selected coordinate arithmetic and normalization call |
| FCFB–FDEF | Unclassified-use byte FCFB; row masks FCFC; colors FD00; initial state FD04–FD09; graphic pointer lows FD0A–FD11; graphics and construction-index table FD4E–FD5D; animation FDC2, motion FDD2, packed speed/score FDD7, fine-motion FDE0 |
| FDF0–FEE6 | Animation delay, shifts/delays, display helper, player swap, RNG, row initialization/derived display values |
| FEE7–FF5A | Bear pointer lows FEE7; row initial state FEEF; graphic/status data FEF3; decimal glyph/blank data around FF00–FF57 and small footer data |
| FF5B–FF67 | Wrapped coordinate normalization |
| FF68–FFCF | Footer graphics/color planes FF68/FF70/FF78/FF80/FF88/FFC0 and row width/position table FFC8 |
| FFD0–FFE8 | Packed integer/fractional step generation |
| FFE9–FFFF | Igloo construction masks, player-color bytes and trailing words |

Table names follow actual readers, not pattern recognition alone: FCAA/FCB0
at F0C2/F0CA; FD0A at F890; FCC0 at F9C2; FCDF at F93C; FD4E/FFE9 at
F5E6/F5E9; FDD7 at F5D9/FEC8; FFC8 at FECC/FED6. Dynamic index bounds,
all alternate graphics states and any missed dual use remain contracts to
prove. FFF9 and FFFA supply player colors at F04C; FFFA–FFFB simultaneously
occupy the unused NMI-word position. That overlap must not become executable
NMI code. Reset and raw IRQ-position words at FFFC/FFFE both contain F000.
The 6507 exposes neither interrupt pin.

No indirect `JMP`, BRK/RTI dispatcher, self-modifying code or synthesized return
dispatch was found in reviewed code. Indirect-Y operands read the six RAM
pointer pairs $85:$86 through $8F:$90 as data. Direct tail jumps matter:
FBFD → FE9B → FEA6 → FEB8 → FEE6 returns to F856's caller; FCF0 → FCF7
joins coordinate normalization. Shared entries FE00/FE03/FE04 implement four
shifts/one shift/RTS-only respectively; FE05 initializes a counter before FE09.
Treating each label as an independent function would lose live flags, delay
cycles and fall-through effects. Initialization reaches **three simultaneous
JSRs**: F00C → FB3B (fall through FB57) → FB78 → FEA6 (fall through FEB8) →
FEC2 → FE00. Return bytes occupy **FA–FF**, mirrored at 01FA–01FF. FA/FB overlap
their later scratch/fire-edge roles; they are not exclusively gameplay state.
A bounded py65 reset-to-F019 probe corroborated this path (1387 instructions,
minimum SP=F9, FEC2 taken for all four row initializations). This CPU probe uses
flat zeroed memory, not cycle-exact Atari hardware; it establishes the concrete
stack path, not complete-game stack coverage.

## Frame order and hardware boundary

The loop wraps from FAE7 to F019. These phase boundaries are the starting
instrumentation points for #4/#7, rather than inferred equal-duration tasks:

| Phase | Source sites | State/hardware effect |
|---|---|---|
| Prepare/wait | F019–F058 | Score pointers, palette and wait for INTIM from the previous blank interval |
| Visible status and playfield | F05A–F479 | WSYNC/HMOVE positioning, score/temperature/reserves, player/bear, alternating object/floe bands, footer; collision reads occur during drawing |
| Overscan setup | F47C/F47F | TIM64T receives 1F, VBLANK receives 82; clear graphics/enable outputs |
| Overscan work | F48B–F5FE | Conditional player swap, igloo buffer, audio **and score events**, collision reduction, fractional steps, selected fire edge, presentation data, periodic RNG |
| Sync wait/pulse | F5FF–F610 | Wait INTIM=0, WSYNC, assert VSYNC then three WSYNC waits before deassertion |
| Frame clock and input | F612–F6AA | Increment frame counter, slow flags/inactivity; TIM64T=30 at F62D; SWCHA sample, console Reset/Select |
| Gameplay and return | F6AB–FAE9 | Delays/state dispatch, actor/row movement, collision decisions, activation/reversal, temperature, bear; return to F019 |

Issue #2 measured stable 262 scanlines/19,912 CPU cycles per observed source
frame; this review adds program boundaries, not new physical timing evidence.
WSYNC stalls, horizontal reset/fine motion, NUSIZ replication and vertical
delay all influence the collision pixels. A generic MSX VDP overlap bit cannot
replace these contracts. Preserve collision work even if rendering is skipped.

Read and write TIA registers share addresses but **different meanings**. The
automatic listing uses write aliases, which are misleading at these reads:

| Read PC | Address and real read meaning | Consumer |
|---|---|---|
| F244 | 07 = CXPPMM, bit 7 P0–P1 | If negative, F248 stores sticky shore collision ED |
| F331 | 07 = CXPPMM | Odd B0+X object samples, X=7,5,3,1 |
| F3BE/F3C0 | 07 CXPPMM OR 01 CXM1P (bit 7 M1–P0) | Even B0+X floe samples, X=6,4,2,0 |
| F5AD | 0C+X = INPT4/INPT5, X=C7 | Selected controller button, prior value AF and falling-edge latch FB |
| F053/F5FF | 0284 = INTIM | Two distinct frame waits |
| F630 | 0280 = SWCHA | Both joystick nibbles; FE00 selects the high nibble for player zero |
| F665 | 0282 = SWCHB | Active-low Reset bit 0 and Select bit 1; no difficulty read used by this path |

All three direct collision-clear sites and the intervening reads are significant:

| CXCLR write | Window ending/read | Storage/lifetime |
|---|---|---|
| F1FC | Bear band until F244 | ED is updated only on negative collision; it persists until other gameplay code clears it, e.g. F9D6 |
| F25F | Start of row positioning | Intermediate positioning window; superseded by F307 before row samples |
| F307 on each row-band iteration | Odd band F331 or even band F3BE/F3C0 | Per-band B0–B7 samples; F566 reduces signs into B8/B9 indexes |

F307 executes inside the loop; reset's indexed clear at F006 can also address
CXCLR when its index traverses 2C.
The F25F reset separates shore and row positioning; F307 resets again after
positioning, so treating a whole frame as one collision window is incorrect.
The reduction visits rows from high to low and overwrites indexes, making
low-index priority observable. #4/#7 must test simultaneous contacts and exact
latched geometry before promoting these static findings to gameplay oracles.

## State, reset and arithmetic that must survive translation

The JSON covers all 128 physical RAM bytes without gaps. Ranges describe
reviewed uses, not exclusive C-style ownership: pointers and F8–FA scratch
change roles between phases, and initialization-time returns overlap FA/FB.
No scratch value is meaningful without its PC/phase.

Reset is not simply a full RAM clear every time. F000 sets SEI/CLD and X=0;
F006 clears indexed zero-page addresses, updates SP with TXS, and wraps X.
Console Reset takes F66B with X=BF into F004, clearing BF–FF while preserving
80–BE. The inactivity path enters with X=D4, preserving player records too.
FB3B initializes both reserve/progress records and falls into FB57's row/actor
initialization. FE77 swaps exactly C8–CD with CE–D3 and toggles C7; this is the
alternating-player storage boundary, not a second full actor-state copy.

| Site | Reviewed constraint | Remaining proof |
|---|---|---|
| FB95–FBC0 | SED score addition CA→C9→C8 with propagated carry; C5 bit 7 gates addition; C9 comparisons and CC<9 gate reserve increment; CLD exit | NMOS decimal flags, rollover/award cases and event ordering |
| FBC1–FBCA | SED/SEC/SBC decrements E5; CLD returns without replacing Z | Zero/borrow boundary and FA9D's immediate BNE dependence |
| FCEA–FCFA / FF5B–FF67 | Incoming carry selects ADC or SBC; CMP-generated carry controls normalization subtraction | Wrap values and returned flags including overflow |
| FFD0–FFE8 | High nibble becomes integer step; low nibble accumulates modulo 16 and conditionally increments integer step | Long sequence/fractional carry at every level |
| FE8B–FE9A | Three feedback iterations of byte 82; one iteration shifts left and appends old bit 4 XOR old bit 7 | Initial seed/aligned replay; zero seed repair and call order |
| F9BC–F9D9 | Vertical table update on alternating frame-counter parity; trajectory index is EA and position is E4 | All arc, shore-entry and airborne-steering boundaries |
| F8CD–F91B | Landing/activation and reversal alter AB+row, CD, audio state and flags under several gates | Simultaneous events, completed igloo, held fire versus edge |
| F6CB–F763 | F1 is a multi-bit dispatcher (BIT uses both N and V, later tests bits 5/4/3) | Full transition matrix, death causes, completion and restart |

Do not substitute Z80 DAA for NMOS decimal ADC/SBC without flag-level proof.
BIT, CMP, shift and arithmetic flag lifetimes cross labels/calls; signed
sentinels use bit 7 and must stay eight-bit. Visual/audio updates include score
mutation at F4F7: removing "presentation" code wholesale would change mechanics.
Some state names (bear/igloo/temperature) are source-use associations, while
precise progression and collision contracts intentionally remain open in #4.
ALE's F1 terminal predicate cannot replace this dispatcher or validate all modes.

## Delivered evidence and next checks

Automated evidence: original-free CLI regressions, canonical identity, two
fresh byte-identical tool runs, static decoded-range/call/target checks and
publication-boundary checks. Review includes the complete listing, data users,
all RAM ranges, hardware access sites and shared entries. The committed map
does not include original bytes, complete instructions or graphic tables.

No complete-game replay, native Z80 comparison, manual emulator gameplay or
physical MSX result is claimed. Source timing captures from #2 do not establish
full-state determinism. Issue #4 must build explicit mechanics/phase contracts
from these sites, and #7 must resolve initialization, aligned input/RNG and
independent reference traces. No MSX ROM was generated, so this issue creates
no testable-ROM release. The mandatory prerelease policy applies as soon as a
useful diagnostic or playable MSX binary exists.

Hardware read names follow the Stella [debugger documentation](https://stella-emu.github.io/docs/debugger.html)
and the [upstream TIA implementation](https://github.com/stella-emu/stella/blob/d55b1aec0d067a4c901a6dcdf81cb8f579685659/src/emucore/tia/TIA.cxx).
The ROM/listing remains the authority for which sites use them. No previously
copied Seaquest success was used as Frostbite evidence.
