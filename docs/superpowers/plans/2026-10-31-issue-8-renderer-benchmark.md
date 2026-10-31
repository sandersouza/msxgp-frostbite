# SCREEN 2 renderer benchmark implementation plan

> **For agentic workers:** Use superpowers:executing-plans. The owner already
> approved native autonomous execution; do not repeat design/method approval.

**Goal:** Choose a measured renderer allocation with explicit headroom on standard
MSX1, keeping original simulation/collision coordinates independent of graphics.
**Architecture:** Synthetic, original-free 240-pixel SCREEN2 scene; four ice and
four threat strips use inactive pattern/color caches and a prepared name page.
Three player color layers and one bear layer use hardware sprites, split into
nonoverlapping vertical pieces where needed. Prepare offscreen, commit names/SAT
at VBlank. Independent host pixels and openMSX observations validate the code.
**Tech stack:** Existing pinned sjasmplus, Python stdlib/.venv, openMSX21.0,
isolated unexpanded C-BIOS profiles, synthetic public CI; no new dependencies.
**Spec:** approved docs/superpowers/specs/2026-10-31-frostbite-design.md, local p08,
docs/gameplay-contracts.md, docs/handoffs/issue-5.md and issue-7.md.

## Global constraints

- Standard-speed MSX1,64KiB RAM/16KiB VRAM,TMS9918-family/built-in PSG,no expansions.
- Atari ROM cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834
  remains untouched authority. Synthetic graphics are explicitly provisional.
- No gameplay/geometry changes to solve rendering. Renderer ABI never writes
  canonical128RAM or collision inputs. No native gameplay acceptance in this issue.
- Original ROMs/full disassembly/derived assets and .legacy remain ignored;
  final cleanup is17. Selected Seaquest harness ideas require a documented audit.
- Preserve existing diagnostic v0.0.1. A changed testable benchmark ROM gets its
  own versioned prerelease with exact tested bytes/hash/source and human checklist.
- Dedicated issue8 fork owns shared checkout/branch; focused reviewed PR, successful
  final CI and integration precede Done. New issue uses another fork.

## Review focus

1. All-X phases, right-edge clipping/wrap and SCREEN2 bank crossings must agree
   with independent pixels, not merely the same generated upload tables.
2. Three player colors/vertical splits, crowded landings and bear overlap must
   respect the actual four-sprites-per-line limit without flicker/hidden actors.
3. Worst pattern/color/name/igloo transitions and PAL double-step frames must
   have measured numeric margins; synthetic step reservations are not native proof.
4. VRAM spacing/visible-page stability, actual consecutive VDP frames and RAM/stack
   guards must be observed; a final screenshot/boot alone is insufficient.
5. Wrong/stale ROM/profile/results and deliberate pixel/occupancy/timing corruption
   must fail; public CI/artifacts and published ROM must remain original-free.

## Task 1: Renderer ABI, independent scene oracle and allocation

**Files:** scripts/render_model.py, tests/test_render_model.py,
references/renderer-contract.json, docs/renderer-design.md.
**Interfaces:** bounded synthetic scene dict -> immutable canonical input bytes;
independent pixel renderer/expected SAT/VRAM checks; generated phase tables and
allocation metadata for the Z80 build. Logical X0..159 maps8+floor(3X/2).

- [ ] Write failing tests for all160 X values,3 ice repeats at32-source-pixel
  spacing, up to3 threat copies with16/32 spacing, clipping and independent
  scanline occupancy. Require<=4 hybrid slots versus rejected all-sprite allocation.
  Run targeted unittest; Expected: FAIL before implementation.
- [ ] Implement source-independent synthetic masks/phase tables and pixel oracle
  separately. Explicitly reserve6144pattern/6144color bytes, two768-byte name
  pages,128-byte SAT and<=2048sprite patterns within16384VRAM; nonoverlap assertions.
  Keep canonical inputs immutable and cache/source coordinates distinct.
- [ ] Add rational scheduler tests for59736 source-equivalent cycles per step,
  NTSC59736 and PAL71364 presentation cycles, no lost required steps, max2; record
  that a measured10,000-cycle-per-step surrogate is a reservation, not native code.
- [ ] Run full suite/source gate, document viable alternatives/costs and commit.
  Expected: all tests pass without original inputs or emulator imports.

## Task 2: Z80 renderer ROM and measured emulator harness

**Files:** src/render.asm, src/render_benchmark.asm, scripts/render_build.py,
scripts/render_bench.py, scripts/render_bench.tcl, tests/test_render_bench.py,
Makefile targets render-build/render-bench; synthetic-only CI extension as needed.
**Interfaces:** Task1 ABI/tables feed a16/32KiB plain ROM; named symbols expose
prepare/commit/done/paced boundaries and buffers. Harness consumes immutable build
metadata plus isolated NTSC/PAL profiles and emits compact hashed evidence.

- [ ] Write failing build/result identity, hardware/profile, stale/incomplete
  capture, pixel/occupancy/budget-negative tests. Expected: FAIL before helpers.
- [ ] Implement original-free assembly renderer/caches/page flip, explicit safe
  VRAM loops, sprite layers/splits/clipped patterns and synthetic animated demo.
  Measure/justify smallest suitable plain ROM; do not inherit a banked layout.
- [ ] Build and run independent expected-pixel/SAT/VRAM/RAM comparisons over all-X,
  color/width/threat-copy phases, bank crossing/wrap/igloo transitions and dense
  player/bear overlap. Observe IO spacing and reject negative corruption controls.
- [ ] Run>=240 consecutive paced frames on NTSC and PAL, keeping dense transitions
  active and recording frame increments, commit window, max busy, step counts,
  RAM/stack guards. Charge measured10k step reservations; publish actual margins
  and limits. Optimize on measured failure, never relax the hardware/geometry gate.
- [ ] Capture/view a current screenshot, run full suite/source gate/CI build checks
  and commit immutable evidence producer. Expected: all workload gates pass;
  no emulator listening/physical/gameplay acceptance inferred.

## Task 3: Review, release and integration

**Files:** docs/renderer-feasibility.md, references/renderer-result.json,
docs/handoffs/issue-8.md, local p08, release tooling/notes and README navigation.
**Interfaces:** compact reports bind exact ROM/hash/commit/config/tool identity;
release package copies the exact tested ROM and reports without rebuilding it.

- [ ] Document measured decision/alternatives, limits, exact reproducible commands,
  future core/input/audio reservations, final mapper bounds and human test checklist.
- [ ] Move8 In review, open/attach focused PR, obtain one fresh whole-branch reviewer
  with the five Review Focus cases and ledger rulings. Reproduce material findings
  RED, fix once GREEN/full suite; no redundant re-review. Expected: no open material
  findings and successful exact-head public CI.
- [ ] Integrate reviewed delivery; verify clean main and exact benchmark ROM/tests.
  Publish new prerelease with exact tested ROM/hash/commit/current/next/human tests;
  download attachments and verify bytes. Expected: actual release readable and
  attachment hashes equal tested artifacts, with no replacement of previous binary.
- [ ] Close/Done8 only after its own acceptance/integration/release. Record durable
  handoff and transfer clean exclusive ownership to a dependency-ready successor
  in a new Frostbite fork; this chat stops editing after transfer.

Self-review: all p08 acceptance maps to tasks1–3. The prototype makes an explicit
renderer decision and performance reservation; later original graphics, native
mechanics, real input/audio and physical acceptance must independently remeasure.
