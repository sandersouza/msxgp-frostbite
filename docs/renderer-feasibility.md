# SCREEN 2 feasibility — issue #8

Decision: use the measured hybrid as the starting renderer contract. Ice and row
threats use background tiles; Bailey uses three color layers and the bear one
layer of hardware sprites. A maximum of four slots per line was observed, including
overlap. Vertical pieces have disjoint rectangles. This is a **synthetic renderer
diagnostic**, with no native Frostbite mechanics or original-graphics acceptance.

## Exact tested artifact and evidence

ROM source/capture producer: `b249373be1cc2382f87b5bb97caa865ae0c6641c`.
ROM: `frostbite-0.0.2-renderer.rom`, 32,768 bytes, Normal/plain32KiB.
SHA-256: `111ded95de3c91ff92093abe5fcee4b436150a99ee96a5a9634dfc9ebeffd4c7`.
The [compact report](../references/renderer-result.json) records exact build,
capture helper, assembler, emulator and isolated-profile hashes. Original Atari
inputs are not needed for this build or any renderer test. The older 16KiB
v0.0.1 diagnostic remains unchanged and separately available.

| Workload | Evidence | Maximum busy cycles | Budget | Margin |
|---|---|---:|---:|---:|
| Independent RPC scenes | 643 full pixel/SAT checks | 57,139 | 59,736 | 2,597 |
| Normal NTSC, both widths | 2 × 240 consecutive frames | 55,455 | 59,736 | 4,281 |
| Crossing NTSC, both widths | 2 × 240 consecutive frames | 58,989 | 59,736 | 747 |
| NTSC SPACE transitions | 240 consecutive frames | 58,971 | 59,736 | 765 |
| Normal PAL, both widths | 2 × 240 consecutive frames | 65,426 | 71,364 | 5,938 |
| Crossing PAL, both widths | 2 × 240 consecutive frames | 68,995 | 71,364 | 2,369 |
| PAL SPACE transitions | 240 consecutive frames | 68,786 | 71,364 | 2,578 |

All costs include a 10,018-cycle synthetic source-step call; PAL charges two when
required. The surrogate body is exactly 10,000 cycles, with CALL overhead measured.
NTSC preserved 240 required reservations and PAL 286 over 240 presentations. This
is a reservation, **not measured native game-core performance**. Real mechanics,
input/audio integration and physical timing must fit and be remeasured later.
The narrow 747-cycle worst paced stress margin cannot silently fund new work.

The RPC matrix covers both layouts, both ice widths and all 160 logical X values,
plus absent/one/two-threat cases; ordinary cases use three threats per row. It
compares independent source-pixel placement against decoded actual VRAM, exact
SAT, sprite patterns and visible-page invariance during prepare. It includes
all pixel phases/parities, clipping, wrapping, color/igloo changes, crowded actors
and the Y128 pattern-bank crossing. The normal layout's measured maximum is
53,555 cycles; the 57,139-cycle maximum belongs to the crossing stress layout.

Paced tests cover every layout/width combination and actual SPACE-driven
transitions on NTSC and PAL: ten streams of 240 frames, 2,400 frames total.
They verify actual per-frame mode samples and keep all rows active and changing. They check actual frame increments,
busy intervals, source-reservation counts, status-port fifth-sprite flags and SAT
scanline occupancy. They do not compare every paced framebuffer pixel. Commits
take at most 1,205 cycles and start/end in VBlank. Observed periods are
59,705–59,768 NTSC and 71,333–71,395 PAL cycles, with polling jitter. A pending
initial VBlank flag is discarded before full-period calibration.

All RPC cases produced 617,827 observed data writes at a minimum 29-cycle spacing.
The VDP too-fast callback and actual IO watchpoint remain enabled. Five real fault
injections reject changed pixels, changed SAT, a fifth slot, RAM corruption and a
12-cycle VRAM gap; failure must match the expected cause. Emulated keyboard tests
verify Left/Right, SPACE edge, held SPACE and release/re-press.

## Independent review and correction

One fresh whole-branch review found that SPACE-selected crossing mode exceeded
the NTSC budget (60,259 / 59,736 cycles), skipped/repeated frames and committed
during active display. The old normal-only paced suite had missed this. An owned
probe reproduced the failure before the fix. Bulk 32-byte crossing-half uploads
removed per-byte preparation overhead; crossing frames now write 64 extra VRAM
data bytes while preserving zero pattern padding and the same decoded pixels.
All fixed modes and real SPACE transitions are mandatory publication gates.
The unchanged strict cadence/VBlank/budget gates now pass on the frozen ROM.
The review also caught a stack transcription error: overall low-water is F372,
whereas F374 described only the normal paced path. The refreshed report/docs
use the overall value. No second review was requested.

## Representation, footprint and limits

See the [design/tradeoffs](renderer-design.md) and
[ABI/allocation](../references/renderer-contract.json). The initial unaligned
independent strips overwrote shared name cells and cost roughly 97k cycles; they
were rejected. The chosen normal layout quantizes bands to eight-pixel rows,
at most four display pixels from that investigated proposal. It changes no
canonical simulation/collision coordinates. A fused-row compositor remains an
unmeasured alternative; the failed independent-strip prototype is not proof that
every unquantized approach is impossible. Issue #9 owns original mapping/fidelity.

Both layouts have separate two-frame cache families. Prepare writes inactive
patterns/colors/names; commit updates SAT, name-page selection and backdrop.
The renderer clobbers Z80 registers, including alternate AF, and temporarily uses
SP for fast clearing. Call with interrupts disabled; a future native adapter must
save logical source registers/flags and preserve this boundary. Canonical
C000–C07F and presentation ABI C100–C11F are unchanged by renderer calls.

| Resource | Used / bound |
|---|---|
| VRAM | 16,000 / 16,384 bytes; 384 free |
| ROM | 30,848 / 32,768 bytes; 1,920 padding |
| RAM state extent including holes | C000–CAFF, 2,816 bytes |
| Observed stack low-water | F372; initial SP F380; guard threshold F340 |
| Sprite pattern table | all 2,048 bytes, including parity/right-edge variants |

The 20,480-byte phase/vertical-shift table rules out a 16KiB ROM for this strategy.
Plain32KiB requires no mapper or expanded system RAM; page2 is mapped through BIOS
primary/secondary slot handling. The expanded-slot path remains a human hardware
check. Later code/assets may require a mapper or smaller tables; 1,920 padding
bytes are not a capacity promise for the full game.

The source RAM, presentation input, heap guard and stack guard passed. These are
bounded synthetic workloads, not natural source-game reachability or complete-game
proof. All masks and font are newly written. Original graphics, full logical
adapter, collision windows, gameplay, PSG, latency and physical acceptance remain
their subsystem gates. The Seaquest quarantine and external snapshot are untouched.

## Reproduce

Use the existing `.venv` and pinned tool setup from [toolchain](toolchain.md).

```sh
make source-check
make test
make render-build
.venv/bin/python -B scripts/render_bench.py --suite --preview
.venv/bin/python -B scripts/render_delivery.py report
.venv/bin/python -B scripts/render_delivery.py package --destination outputs/releases/v0.0.2-renderer-reviewed
make ci-verify
```

Commit intended renderer/harness dependencies before canonical captures. The
publisher refuses dirty or mismatched producer/helper snapshots. A later docs
commit does not relabel the recorded ROM/capture producer. The package copies
the exact tested ROM without rebuilding, stages atomically, and refuses changed
bytes in an existing version directory. Public CI builds both original-free
diagnostics; it does not run emulators or publish/re-upload a ROM automatically.

`--preview` reconstructs a PNG from actual emulated VRAM/register dumps with an
approximate RGB palette. It was viewed. The live graphical capture path stalled
in two bounded attempts on this host; neither produced accepted evidence. No
framebuffer/manual-emulator, listening or physical result is inferred. Human
setup/actions/expected results are in the [release notes](releases/v0.0.2-renderer.md).
