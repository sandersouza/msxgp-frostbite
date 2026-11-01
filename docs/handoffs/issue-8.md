# Issue #8 handoff — measured synthetic renderer

Issue: https://github.com/sandersouza/msxgp-frostbite/issues/8.
Branch: `codex/feat/8-screen2-renderer-benchmark`; base
`fd1ee97a557f5642f1f845364f1ca41279781375`. Delivery PR, exact-head CI, merge and
release readbacks are linked from the issue. Review/publication remain pending at
this documentation checkpoint. The dedicated issue8 chat owns the checkout until
explicit transfer; no successor implementation starts here.

## Frozen artifact and reproduction

ROM and capture producer: `dd7c46563252b6c3910777458bae5e9ca87eef75`.
ROM: `frostbite-0.0.2-renderer.rom`,32768bytes,Normal/plain32KiB.
SHA-256 `f311480240f5f6f52a1baea835264e4cb06e5aeb05795174564c059ea15155d4`.
Used30674/padding2094. It is original-free/synthetic, not a playable port.
The [report](../../references/renderer-result.json), [operations/limits](../renderer-feasibility.md),
[design](../renderer-design.md) and [human test notes](../releases/v0.0.2-renderer.md)
carry exact identities and boundaries. Publisher/tool producer is separate from
the measured ROM producer; never relabel captures as produced by later docs code.

```sh
make source-check
make test
make render-build
.venv/bin/python -B scripts/render_bench.py --suite --preview
.venv/bin/python -B scripts/render_delivery.py report
.venv/bin/python -B scripts/render_delivery.py package
make ci-verify
```

Canonical private suite/build metadata live under outputs/render/. Producerdd7c465
has clean build and harness snapshots. Raw captures: rpc-ntsc-348ybpqy,
pace-ntsc-81n2qsl3,pace-pal-1i8iggqc,controls-ntsc-qnq1vcgn. The preview under the
NTSC directory is an actual-VRAM reconstruction, SHA-256
0925757d32708f9fbda30d2fd0cda73580154f441959aa31049c44f58a7d4a03, not a framebuffer
capture. Original inputs were not used. Source files/helpers and binary/profile
hashes are independently audited against producer Git commits before publication.

## Verified evidence

- 125 host tests at the capture checkpoint; delivery adds three more.
- 643 full pixel/SAT scenes, both layouts/widths/all160X values, wrapping/right
 clipping, absent/partial/dense threats, color/igloo transitions and bank crossing.
 Visible state is unchanged through prepare; all sprite patterns/SAT are checked.
- 597347 RPC data writes, minimum29cycles; actual peak4slots/line. Changed pixels,
 SAT, fifth slot, heap guard and12cycleVRAMstream each fail for the expected cause.
- RPC max58409/59736; normal layout max53555. NTSC240consecutiveframes max55455,
 margin4281. PAL240 max65426/71364,margin5938,286required reservations preserved.
 The charged step is a10000cycle body/10018withCALL, not native game performance.
- Commitmax1205cycles insideVBlank; RAM/source/input guards and stacklowF374 pass.
 Controls exercise actual emulated matrix Left/Right and SPACE edge/hold/repress.
- Public CI builds both original-free diagnostic cartridges; no original is
 downloaded. Existing uploaded reports remain a named allowlist, not ROM blobs.

## Decisions and limits for issue9

- Exclusive checkout/native execution follows the owner's approval. Cost:
 branch isolation relies on one writer; old issue chat stops after transfer.
- New masks/font and a10k step reservation are intentionally synthetic. Cost:
 original assets/core/input/audio must remeasure; these passes are not native proof.
- Seaquest supplied only audited harness concepts (breakpoints, timing, VRAM and
 guards); implementation is fresh. Cost: new infrastructure needed independent
 negative controls; old Seaquest success certifies nothing here.
- Grid-aligned bands avoid competing name cells; maximum4displaypixel shift from
 the investigated layout. The unaligned independent-strip prototype failed pixels
 and cost97k. A fused-row compositor was not measured, so it remains an option;
 no fundamental impossibility is claimed. Cost: issue9 must assess source mapping
 and visible quantization without changing logical collisions/simulation.
- Separate layout/frame cache families preserve zero padding. Local band IDs share
 only distinct banks/upper-lower halves. Cost: arbitrary future Y layouts or larger
 masks require allocation/alias tests, not silent reuse.
- Plain32KiB follows the20480byte table footprint and measured30674total. Cost:
 only2094bytes remain; full game mapper/capacity is still open. Expanded-slot path
 is implemented through BIOS but not physically accepted.
- All2048sprite-pattern bytes are used. Three player colors plus bear occupy4
 scanline slots; 19pixel actors split into disjoint16line pieces. Cost: original
 palettes/animations/clipping bounds may force a new allocation in9.
- The live graphical backend stalled twice under bounded watchdogs. Use the
 explicitly labeled VRAM preview. Cost: GUI/framebuffer/manual/physical acceptance
 remains pending, including expanded cartridge slots and human verdicts.
- Capture helper revisions/hashes are separate from build revisions. Cost: only
 clean committed manifests feed release tooling; changed helpers require fresh
 captures, not retrospective relabeling.
- Operational benchmark documentation is outside service C4/Backstage generation.
 Cost: no service-catalog output is produced.

The renderer clobbers Z80 registers/alternateAF and temporarily uses SP. Native
callers must save logical6502 registers/flags and keep interrupts disabled while
rendering. CanonicalC000–C07F and inputC100–C11F remain immutable during calls.
The frame scheduler currently charges surrogates; native per-step input/collision/
audio ordering and exact source time are later integration contracts.

## Delivery and continuation

Independent review disposition, final-head CI and publication/readback are recorded
with the delivery PR and issue after verification. Publish prereleasev0.0.2-renderer
only with the exact tested ROM and source above; never overwrite v0.0.1 assets.
Future changed testable ROMs need new versioned releases with human instructions.

After accepted integration and verified release, close/Done8 and fork/reuse
`Frostbite — ISSUE #9` in the Frostbite project. Transfer clean exclusive ownership,
issue URL, source/ROM identities, limitations and pending human checks. No pending
implementation files should transfer. Original ROM/disassembly/derived assets,
.legacy/seaquest and the verified external snapshot stay local/intact; final legacy
cleanup is17 after functional replacement acceptance.
