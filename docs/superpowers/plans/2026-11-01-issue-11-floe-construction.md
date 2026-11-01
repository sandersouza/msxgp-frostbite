# Floe contacts and build-and-enter loop implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. The owner has already chosen autonomous inline execution in the exclusive issue checkout.

**Goal:** Deliver exact floe activation/reversal/construction/temperature behavior and a continuous natural construction→entry→next-level route.

**Architecture:** Retain the audited native post-visible core and real input. Add an explicit visible-phase adapter: original-clock literal-view floe collision tables, exact palette/sticky-state and final scratch/CPU effects. Compare that reduction against unmodified original instruction execution and an independent Atari backend. Keep synthetic presentation separate; measure the complete real pipeline again.

**Tech Stack:** Existing pinned Python/py65/ALE/Stella, sjasmplus Z80, openMSX, SCREEN2/ASCII16.

**Spec:** docs/superpowers/specs/2026-10-31-frostbite-design.md; .github/issues/frostbite/p11-port-floes-igloo-and-temperature.md; docs/handoffs/issue-10.md.

## Global constraints

- Standard-speed MSX1, 64 KiB RAM, 16 KiB VRAM, TMS9918-family VDP and built-in PSG; no expansions.
- Authority SHA256 cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834; source RAM80..FF remains canonical.
- Preserve instruction ordering, flags, decimal behavior, logical cadence and real input boundaries. Never infer contacts from synthetic MSX geometry or skip required source steps.
- Original ROM, complete disassembly, derived mask/code/data and raw full states remain local/ignored. Preserve legacy and frozen issue10 bundles/releases.
- New human ROM is a new version with its own clean producer, complete captures and prerelease; do not relabel 0.0.3.
- Floe acquisition and the natural first-level route belong11. Full hazard/RNG/TIA semantics belong12; natural route must not inject RAM/contact outcomes or disable real source hazards.

## Review focus

1. Left/right edges, copy overlap, shape phase and reflected/shifted player patterns: collision is the actual original TIA latch, including hidden clocks and data-dependent update events. Visible raster overlap alone was experimentally rejected.
2. Sticky ED and every128-byte phase effect: a visually successful landing must not hide omitted palette/scratch/return-byte changes or forged target continuity.
3. Landing with fire/timeout, completed-igloo cost, rearm and low-index priority: preserve the actual native source dispatch and before/after order.
4. PAL catch-up with real contacts and crowded layout/width transitions: no dropped source steps, visible preparation writes, late commit, extra sprites or stale timing margin.
5. Natural construction/entry/level change and stale evidence: independent original execution, explicit success/failure predicate, real device replay, complete immutable files/producers and targeted corruptions.

### Task 1: Original-raster floe and visible-state contract

**Files:** scripts/floe_reference.py, scripts/floe_model.py, tests/test_floe_model.py, references/floe-contract.json, ignored outputs/floes/.

**Interfaces:** `visible_reference(rom,ram,registers,contacts)->CPU/RAM` executes original F019→F476 with declared per-window electrical samples. `visible_state(rom,ram,registers,contacts)->CPU/RAM` is its explicit native-adapter specification. `floe_contacts(rom,ram,catalog)->bytes[8]` will query complete original-clock truth for all228 literal player views; inactive object bytes retain the source electrical low bits. `floe_catalog.capture(...)` freezes the complete controlled domain and source identity locally. scripts/stella_floe.py builds the pinned observation-only backend; scripts/floe_observer_check.py compares unchanged original CPU/RAM/latches and cached/full execution.

- [ ] RED→GREEN host tests: mask clipping/wrap/empty/reflection, exact phase write set/CPU return, shape domain and complete case/manifest requirements. No original bytes enter unit fixtures.
- [x] Capture all160 floe positions ×16 shaping phases ×7 lines in independent ALE executions; compare all four row windows. Raster-only collision inference rejected by electrical edge probes.
- [ ] Capture all160 player positions ×160 floe positions ×10 legal control pairs ×34 vertical samples ×228 literal views, with both original latch channels. Deduplicate complete records/profiles only byte-exactly. Validate all four windows, outside-Y sentinel, blanking, header/view invariance and cached/full equivalence against unchanged original execution.
- [ ] Compare exact full visible CPU/RAM reduction against original py65 instruction execution, plus independent Stella phase checkpoints and actual per-window contacts for seeded boundary/landing cases. Keep unsupported full hazard acquisition explicit.
- [ ] Full suite; commit clean helpers and capture canonical evidence with exact backend/tool/provenance identities.

### Task 2: Native visible adapter and natural loop

**Files:** src/floes.asm, scripts/floe_build.py, scripts/floe_check.py/.tcl, tests/test_floe_build.py, scripts/floe_routes.py, references/floe-routes.json.

**Interfaces:** `visible_step` consumes target-owned canonical RAM and generates contacts/visible final state without source snapshots. `frame_step` then executes existing native F476→F019 with genuine MSX input. Build output lives under ignored outputs/floes; version0.0.4-buildloop/ASCII16 capacity is measured. Route policy consumes current state and emits only controller/console pins; acceptance compares independent source/target full states.

- [ ] RED→GREEN translation/build tests pin ROM identity, mask-bank bounds, visible adapter ownership and source cadence. Implement Z80 bitwise contact queries and exact phase state; retain source gameplay core and input semantics.
- [ ] Actual openMSX differential cases cover activation/rearm/wrap, fire costs/hold/air gates, igloo boundaries and timeout/landing ordering, all published mechanics regressions, CPU/RAM guards and negative controls.
- [ ] Develop a bounded natural first-level route using only input from reset. Require construction completion, actual entry and next-level transition; preserve target-owned continuity and compare with independent original execution and replay. A seeded route is a separate boundary test, never the natural route.
- [ ] Full suite and exact native tests; commit clean producer before canonical capture.

### Task 3: Integrated testable ROM and timing

**Files:** scripts/floe_build.py, scripts/floe_bench.py/.tcl, src/floes.asm, selected renderer modules only if measured need, tests/test_floe_build.py.

**Interfaces:** Reuse prepare/commit mapper ABI and read-only presentation adapter. Real `frame_step` replaces scripted contacts. Pixel oracle remains independent of gameplay geometry. Package freezes the exact ROM/captures; no synthetic CPU reserve.

- [ ] Integrate the new adapter and core into a clearly labeled build-loop diagnostic. Keep original graphics/audio/full hazard acceptance explicitly pending.
- [ ] Remeasure every layout/width, held/repressed selectors, focused0/1/2 counts and NTSC/PAL active frames with actual new contact/core work; compare every pixel, all native state, uninterrupted source count,29cycle spacing,4slots,stack/heap, visible invariance and VBlank commit.
- [ ] Inject actual contact/state/pixel/device/guard faults and require their intended gates. Optimize only demonstrated bottlenecks; never omit simulation or relax gates.
- [ ] Freeze a complete immutable version package after clean canonical captures; full host suite and old published ROM identities pass.

### Task 4: Review, release and dedicated successor

**Files:** docs/floe-loop.md, references/floe-result.json, docs/releases/v0.0.4-buildloop.md, docs/handoffs/issue-11.md, local p11, README.

- [ ] One fresh read-only whole-branch review on the most capable reviewer, five focus classes and ledger rulings. Regrade material findings; one owned RED→GREEN fix pass/full suite, no review loop.
- [ ] Exact-head CI, focused linked PR and clean merged-main checks. Publish prerelease with exact tested ROM/SHA/source/current/next/human tests; download and verify every asset before close/Done.
- [ ] Durable handoff of hashes, limits and exclusive ownership to a separate Frostbite issue12 fork. Stop editing this checkout after transfer; keep legacy deletion for17.

Self-review: Tasks1/2 establish real floe acquisition plus original state effects and all11mechanics; Task2 owns the natural completion predicate; Task3 owns whole-pipeline timing; Task4 owns integration/release. Full hazards and original graphics/audio are not inferred from these checks. The approved autonomous method overrides redundant design/plan approval menus.
