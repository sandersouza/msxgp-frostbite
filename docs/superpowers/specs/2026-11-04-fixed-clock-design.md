# Fixed source clock with coherent render snapshots — issue42

R preserves the tested graphics/state but improves whole-game cadence only1.03%
NTSC /0.73% PAL over Q. Continuing small renderer patches does not address the
architectural coupling: one expensive prepare postpones the next gameplay step.
Owner approved architecture replacement, original-speed gameplay, and a30fps
presentation test. This diagnostic separates those clocks; it never claims60fps
graphics, all-level timing or final delivery acceptance from a60Hz logic result.

## Selected architecture

Run the unchanged scheduler/charge_steps/native_step from each VDP interrupt.
NTSC advances one source step per VBlank; the existing PAL accumulator retains
the exact1/2-step order and average source rate. Input sampling and ordered PSG
writes stay inside their original source step. Main rendering consumes a stable
128-byte source snapshot atF000 instead of liveC000. Only renderer read/address
operands are relocated; gameplay/native/audio source accesses stay atC000.

The existing renderer prepares one complete inactive frame. Once ready, it waits.
At VBlank the handler commits a pending SAT/NAME flip before gameplay work, then
advances the source. No commit occurs during prepare, and no new prepare starts
while a frame is pending. Admit at most one commit per two VBlanks: nominal
29.96 NTSC /25.08 PAL presentations per second when CPU budget permits. Actual
presentation cadence is measured separately and can be lower. No source step
is intentionally dropped or reduced. A late-interrupt counter is an explicit
qualification failure; source and visual timing claims remain separate.

## Standard MSX1 execution

All post-boot input/audio paths already use direct MSX ports. After the original
BIOS screen/slot initialization, map page0 to the same built-in64KiB RAM slot
as page3, preserving other primary/secondary slot fields. Install JP handler at
0038, use IM1, and enable VDP R1 interrupt bit. No BIOS call or interrupt handler
is used after takeover. This uses existing RAM, not an expansion. Explicitly
test expanded-slot RAM as well as the simple isolated profile before portability
claims. The original boot/SCREEN2 path remains unchanged until takeover.

Every actual LD(7000),A instruction is inventoried from public assembler listings
and replaced by a same-size CALL to a resident mapper tracker. It preserves all
registers/flags and records the selected bank. Interrupt entry saves all primary,
index and alternate registers and the mapper, and restores them before EI/RETI.
Only actual emitted instructions are patched, never byte-pattern searches over
assets. Known overwritten predecessor instructions are filtered against the
authenticated Q bytes. Snapshot operands are likewise selected from renderer
instruction provenance; C080 player metadata and all source/native/audio code
are excluded. P/Q and inherited L instructions are covered as well as canonical F.

## VDP transactions and initialization

Common vdp_write and pk_fill select the VDP address with interrupts disabled,
then resume interrupts only when the clock is enabled and outside its handler.
Their data streams may be interrupted: the handler never touches VRAM data
unless a complete frame is pending, and pending implies main is waiting. VDP
status acknowledgement therefore cannot split a two-byte address latch. IRQ
commit remains DI, including its SAT stream and R2 control pair. No unprotected
post-takeover control writer is admitted.

Code is copied once toE900..EFFF (<=1792 bytes) from an authenticated reclaimed
tail; variables useE880..E8FF. SnapshotF000..F07F; guardF080..F2FF; stack
F300..F37F with SP F380. Bootstrap initializes clock-enable before any new gate
can execute. A prepare gate snapshots under DI, records the source-step number,
restores the original register/mapper contract, and leaves boot/component tests
DI while the clock is disabled. Region R is retained as rejected evidence;
this diagnostic starts from reproduced Q, avoiding unnecessary RAM code.

## Evidence gates

First prove mapping/snapshot instruction inventory, exact patch bytes, untouched
assets and corresponding public source. Retain the2115 source/1920 density pixel
matrices with clock disabled, coherent snapshot/code/VRAM/ABI guards. A new
clock-route harness drives original hardware inputs per native step, compares
every original CPU/all128RAM checkpoint and checks each rendered snapshot against
its own source state. Record every VBlank/source entry/commit/prepare interval,
late count, commit scanline, maximum source-handler cycles and real presentations.
Do not reuse the old render-driven frame-count denominator or sum inclusive IRQ
time twice. Add interrupt injection around address/data/bank/snapshot boundaries
and verify source-clock/active-display invariants. Review before selecting a
human ROM, then publish a new diagnostic prerelease with exact ROM/hash/source,
explicit visual cadence/limitations and original-speed/control/audio human tests.
