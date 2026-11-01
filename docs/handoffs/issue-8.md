# Issue #8 handoff — measured synthetic renderer

Issue: https://github.com/sandersouza/msxgp-frostbite/issues/8.
Branch: `codex/feat/8-screen2-renderer-benchmark`; base
`fd1ee97a557f5642f1f845364f1ca41279781375`. Delivery PR [#27](https://github.com/sandersouza/msxgp-frostbite/pull/27), exact-head
CI, merge and release readbacks are linked from the issue. Independent review, the one correction pass, integration and publication are
complete. This handoff receipt records the delivered bytes; the dedicated issue8
chat owns the checkout until its explicit transfer to the prepared issue9 fork.

## Frozen artifact and reproduction

ROM and capture producer: `b249373be1cc2382f87b5bb97caa865ae0c6641c`.
ROM: `frostbite-0.0.2-renderer.rom`,32768bytes,Normal/plain32KiB.
SHA-256 `111ded95de3c91ff92093abe5fcee4b436150a99ee96a5a9634dfc9ebeffd4c7`.
Used30848/padding1920. It is original-free/synthetic, not a playable port.
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
.venv/bin/python -B scripts/render_delivery.py package --destination outputs/releases/v0.0.2-renderer-reviewed
make ci-verify
```

Canonical private suite/build metadata live under outputs/render/. Producer
b249373 has clean build and harness snapshots for all twelve captures:

- `rpc`: `outputs/render/rpc-ntsc-rsthuzr4`.
- `ntsc`: `outputs/render/pace-ntsc-y9efz1ii`.
- `ntsc_layout0_width1`: `outputs/render/pace-ntsc-ufm8vqqy`.
- `ntsc_layout1_width0`: `outputs/render/pace-ntsc-rbj3oy6v`.
- `ntsc_layout1_width1`: `outputs/render/pace-ntsc-ggxtsi43`.
- `pal`: `outputs/render/pace-pal-5fta98w9`.
- `pal_layout0_width1`: `outputs/render/pace-pal-hi7hh_pc`.
- `pal_layout1_width0`: `outputs/render/pace-pal-umguede8`.
- `pal_layout1_width1`: `outputs/render/pace-pal-v541ir2w`.
- `ntsc_transitions`: `outputs/render/pace-ntsc-w5tf60cu`.
- `pal_transitions`: `outputs/render/pace-pal-pa2ursx1`.
- `controls`: `outputs/render/controls-ntsc-4v3fkc8x`.

The NTSC preview is an actual-VRAM reconstruction, SHA-256
0925757d32708f9fbda30d2fd0cda73580154f441959aa31049c44f58a7d4a03, not a framebuffer
capture. Original inputs were not used. Source files/helpers and binary/profile
hashes are independently audited against producer Git commits before publication.
The reviewed package is `outputs/releases/v0.0.2-renderer-reviewed`.
The old default package with f3114802 bytes was rejected before publication;
retain it only as local review history and never upload it.

## Verified evidence

- 129 host tests at the final capture checkpoint.
- 643 full pixel/SAT scenes, both layouts/widths/all160X values, wrapping/right
 clipping, absent/partial/dense threats, color/igloo transitions and bank crossing.
 Visible state is unchanged through prepare; all sprite patterns/SAT are checked.
- 617827 RPC data writes, minimum29cycles; actual peak4slots/line. Changed pixels,
 SAT, fifth slot, heap guard and12cycleVRAMstream each fail for the expected cause.
- RPC max57139/59736,margin2597; normal layout max53555. All ten paced streams
 pass240consecutiveframes each. NormalNTSC55455/PAL65426; crossingNTSC58989
 (margin747)/PAL68995(margin2369). SPACEtransitionsNTSC58971/PAL68786.
 Each PAL stream preserves286required reservations; NTSC240.
 The charged step is a10000cycle body/10018withCALL, not native game performance.
- Commitmax1205cycles insideVBlank; RAM/source/input guards and stacklowF372 pass.
 Controls exercise actual emulated matrix Left/Right and SPACE edge/hold/repress.
- Public CI builds both original-free diagnostic cartridges; no original is
 downloaded. Existing uploaded reports remain a named allowlist, not ROM blobs.

## Review disposition

One fresh read-only reviewer independently checked the old 643 pixel cases,
preparation invariance, provenance and 128 host tests. Important: SPACE crossing
mode exceeded NTSC (60259/59736), skipped/repeated VDP frames and committed in
active display. The old normal-only pace gate missed it. An owned probe reproduced
RED; one fix pass uses bulk crossing halves and adds all eight fixed layout/width/
standard combinations plus two actual SPACE-transition streams as strict gates.
New mode-sample and publisher rejection tests passed RED to GREEN. The complete
clean b249373 suite and 129 host tests pass without relaxing timing/VBlank gates.
Minor stack transcription F374 was corrected to the overall F372. No material
finding remains open; no second review was requested.

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
- Bulk crossing halves add64data bytes/frame to reduce CPU overhead. Cost:
 the narrow747cycleNTSCmargin and higher VRAM traffic require fresh integration
 measurements; this is not spare native game/audio capacity.
- Plain32KiB follows the20480byte table footprint and measured30848total. Cost:
 only1920bytes remain; full game mapper/capacity is still open. Expanded-slot path
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
The tag targets the integrated snapshot including later docs/report; verify all
build/harness blobs match the frozen b249373 producer. Record both identities.
Download all six published assets into a fresh directory and verify SHA256SUMS
before declaring delivery. The reviewer did not certify future publication.
Future changed testable ROMs need new versioned releases with human instructions.

After accepted integration and verified release, close/Done8 and fork/reuse
`Frostbite — ISSUE #9` in the Frostbite project. Transfer clean exclusive ownership,
issue URL, source/ROM identities, limitations and pending human checks. No pending
implementation files should transfer. Original ROM/disassembly/derived assets,
.legacy/seaquest and the verified external snapshot stay local/intact; final legacy
cleanup is17 after functional replacement acceptance.


## Verified delivery receipt

- Implementation PR27 merged as `0e17316b2c98898cf13d0b05ff9afe996d65bda8`.
  [Exact-head CI41257975158](https://github.com/sandersouza/msxgp-frostbite/actions/runs/41257975158)
  and [merged CI41258059183](https://github.com/sandersouza/msxgp-frostbite/actions/runs/41258059183)
  passed; all129host tests pass locally after merge. The downloaded PR CI artifact
  contains only the three allowed reports,129tests and zero skipped results.
  CI built the same renderer ROM hash. Source-policy and repeated older diagnostic
  byte-identity checks also pass. Integrated build/helper blobs equal frozen b249373.
- [Published prerelease v0.0.2-renderer](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.2-renderer),
  not draft; annotated tag targets integration0e17316, including evidence/docs.
  Frozen ROM/capture source remains b249373. Six assets were downloaded into
  `outputs/issue8/published-v0.0.2-renderer` and compared byte-for-byte with the
  reviewed immutable package: ROM, build.json, renderer-result.json,
  release-notes.md, preview-vram.png and SHA256SUMS. All five manifest checks pass.
  ROM SHA-256 remains111ded95de3c91ff92093abe5fcee4b436150a99ee96a5a9634dfc9ebeffd4c7.
- The previous v0.0.1-diagnostic ROM was downloaded again; its SHA-256 remains
  d46320aec4b148c3b885d54de051bc078539b65a7a8bf739bb4e9e956c2028ca.
  No existing published asset was replaced. No manual/physical verdict is inferred.
- The final documentation receipt PR is linked from issue8. Close/Done follows
  that receipt's integration; issue9 start follows the explicit ownership transfer.

Prepared successor: `Frostbite — ISSUE #9`, thread
`01a19491-87f2-7130-94b8-d51d96adcfc5`, Frostbite project
`0fd5a899-599e-40d4-988e-46b3d31433dd`, same workspace. Goal: original graphic
extraction, deterministic source frames and coordinate/palette mapping, dependencies
3 and8 delivered. It must verify the clean main branch/commit, read this handoff,
its own local issue copy and approved design, move9 In progress, and take a scoped
branch before edits. No implementation files are pending. Only ignored original
inputs, generated outputs, legacy and private evidence remain local. Issue8 stops
all checkout edits after the transfer message. Future changed testable ROM bytes
require a new version/release; never reuse0.0.2-renderer for changed bytes.
