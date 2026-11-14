# Compact floe contact component

Issue [#44](https://github.com/sandersouza/msxgp-frostbite/issues/44), component
source `3370af7b3217ece06a113088df28310cf30b4c25`.
This component is **not linked into the playable game**. The accepted v0.0.30
cartridge is unchanged. ROM size, native COM/BIN delivery and whole-frame
cadence are not established by this test.

## Implementation and exact domain

The assembly uses 147 shared seven-byte ice footprints, a 1,600-byte directory,
two 256-byte normal/reflected glyph pages and six original glyph offsets.
The uniform electrical bit6 channel reduces from the initial 420-byte dictionary
to a scalar rule, retaining its Y and absolute-X exceptions. Total component:
**186 bytes of code + 3,147 bytes of data = 3,333 bytes**. Glyph storage may be
shared later; the present count does not assume that saving.

The bit7 geometry is proved for player X9..153. Coordinates 0..8 and154..159,
enemy contacts and shore contacts retain the old oracle and remain unsolved.
Do not clamp coordinates or remove those paths: the source can move actors
through boundary states. The bit6 rule covers every emitted floe coordinate.

The host proof checks:

- All 8,704,000 emitted floe cells for both the independent bit6 factor and its
  scalar replacement, including exceptional Y/absolute-X cases.
- All 7,888,000 interior cells for exact pure bit7 equality to the reference
  rows; each cell contains all 228 literal player views.
- The geometric footprint construction across 54,400 cells and all 228 views.

The original ROM's emitted contact records are the independent output oracle.
Expected native outputs are read from those records, not calculated by the new
assembly or its convolution helper.

## Actual Z80 qualification

The separate, non-playable Normal-ROM fixture executes on a standard-speed
64 KiB MSX1 profile. It exercises every shared footprint/Y/literal-view class
and every control/Y/absolute-X shadow entry: **1,193,944 actual Z80 calls**.
This is the declared equivalence-class corpus, not 1.8 billion native calls.

All output bytes match. IX/IY/SP remain intact; interrupts stay disabled for
this component harness. CPU write watchpoints admit only the bounded stack;
no mapper or other guest writes occur. Host fixture inputs are loaded while
execution is paused and the guest-write guard is suspended, then the guard is
restored before continuing the CPU. Frozen source copies, tools, profile,
inputs, expected bytes, actual bytes and exact hashes accompany the receipt.

| Cost including caller CALL and return-path JP | MSX CPU cycles |
| --- | ---: |
| Minimum | 141 |
| Mean | 656.410467 |
| P95 | 1,084 |
| Maximum | 1,227 |

These are isolated component costs. They do not include source-row dispatch or
the renderer and must not be presented as a whole-frame performance gain.
The first 10,000-case write-guard run was rejected because debugger input writes
trigger `write_mem`; the guard was corrected before the 20,000-case smoke and
full qualification. The earlier 215-byte dictionary version was also retained
locally. Rejected runs are not acceptance evidence.

631 synthetic host tests pass. Independent review reproduced the host assets,
verified all frozen sources and final native hashes/outputs/cycles, and found
no Critical/Important blockers for this component's stated scope. Physical
hardware, new-format loading and whole-game integration remain untested.

## Reproduction and next boundary

```sh
.venv/bin/python scripts/compact_floe_probe.py \
  --build outputs/presentation/credit-reference-at/build-final \
  --out outputs/compact/my-floe-component-proof
.venv/bin/python -m unittest discover -s tests
```

The output name must be fresh. `--limit N` is a smoke test and explicitly sets
`complete_native_domain=false` unless it reaches the whole corpus. The fixture
ROM exists for automated component calls, displays no playable game and is not
a candidate to send to the human. No new Frostbite game version was generated.

Next, derive exact boundary/enemy/shore routines and check their complete source
domains. A separate preliminary ordinary-enemy convolution experiment matches
25,740 common-profile cells ×228 views only when it uses **seven collision
rows**. The naive eight-row version differs in 13,496 cells. Rendering still
uses eight visual rows; that distinction follows the source collision-read
timing and must be preserved. This enemy finding is a host hypothesis check,
not a qualified Z80 enemy implementation.

After the remaining contact representations are proved, remove their banked
dependencies, audit graphics/prepared-program data and define the shared flat
layout. Only then build the complete 32 KiB cartridge, COM and BASIC BIN and
rerun full-density NTSC/PAL source/picture/audio/whole-frame comparisons.

See [native receipt](../references/compact-delivery/issue-44-floe-component.json)
and [initial inventory](compact-native-inventory.md). Issue44 stays In progress.
