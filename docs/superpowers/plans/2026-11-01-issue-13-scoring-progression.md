# Scoring, progression and game variations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Deliver issue #13 with original-backed scoring/life/progression boundaries and continuous acceptance for all four variations, including alternating turns, exhaustion and restart.

**Architecture:** Retain the existing native whole-phase Z80 translation and real original-clock contact acquisition. Add independent original probes, explicit route predicates and immutable replay evidence; correct native behavior only when a differential failure demonstrates a defect. Reuse existing paced capture through explicit optional validation callbacks rather than copying the harness.

**Tech Stack:** Python in `.venv`, py65 source CPU, instrumented Stella, sjasmplus, openMSX C-BIOS MSX1, GitHub CLI/plugin.

**Spec:** `docs/superpowers/specs/2026-10-31-frostbite-design.md`; contracts S1/S2/V1/V2/V3/C1 in `docs/gameplay-contracts.md`; local P13 issue; `docs/handoffs/issue-12.md`.

## Global Constraints

- Standard-speed MSX1, 64 KiB RAM / 16 KiB VRAM, TMS9918-family VDP and built-in PSG; no expansions, turbo, disk or additional sound hardware.
- Original ROM SHA-256 `cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834` is gameplay authority. Preserve byte arithmetic, CPU flags, phase boundaries, RNG and update ordering.
- 4 MiB ASCII16 cartridge is permitted. Keep original ROM/disassembly/derived tables and complete source captures ignored/local.
- No source/contact/RAM injections in natural routes. Controlled boundary fixtures are explicitly distinguished.
- Every changed testable ROM gets a new prerelease with exact tested binary, source commit, checks/limits, next work and human actions. Never replace v0.0.5 bytes.
- Whole-frame limits NTSC 59,736 / PAL 71,364 cycles; VRAM spacing >=29 cycles; <=4 sprites per line; no dropped logical steps, turbo or weakened fidelity.
- One issue per fork, current exclusive checkout/branch; existing approved autonomous native execution/integration/release policy applies.
- Manual emulator and physical evidence stay pending until observed. Definitive graphics/HUD/audio belong #14; legacy removal belongs #17.

## Review Focus

- A score carry coinciding with death/bonus transition must award through source order and preserve both player records.
- One exhausted alternating player must be skipped without losing the surviving player's six-byte record.
- Level FF wrap and scoring plateau must not introduce a difficulty cap or incorrect day/night selection.
- Select hold/release, simultaneous Reset/Select and difficulty switch bits must retain the source console behavior.
- PAL double steps on bonus/reinitialization and terminal/restart frames must satisfy every presentation view, not only default layout.

---

### Task 1: Independent scoring and state-machine boundary evidence

**Files:** Create `scripts/progression_cases.py`, `scripts/progression_check.py`, `tests/test_progression_cases.py`; create `references/progression-contract.json` and `docs/scoring-progression.md`.

**Interfaces:** Consumes `native_contract.reference(rom, case)`, `hazard_mechanics.original_step(rom, ram, registers, reader, keys)` and `hazard_check.run_target`. Produces `primitive_cases() -> list[dict]`, `phase_cases(base: bytes) -> list[tuple[str, bytes]]`, `check(out, build_dir, reader, initial_path, explore=False) -> dict` with exact source/native identities and complete CPU/all128RAM results.

- [x] Write original-free tests for case coverage: BCD carry/overflow/attract/cap, all256 level bytes, both records and all four variations, every F1 dispatch bit/priority, dead-other/both-empty recovery and console switch combinations.
- [x] Run `.venv/bin/python -B -m unittest discover -s tests -p 'test_progression_cases.py' -v`; require RED for the absent API, then implement deterministic fixture generation and strict finite-domain validation; rerun GREEN.
- [x] Run primitive source versus actual Z80 contract slices; run full visible+native phases using actual audited contacts, not fabricated neutral masks. Require complete registers/RAM, no mismatches and clean producer fingerprints. Record observed invariants rather than assuming mathematical score shortcuts.
- [x] Run whole original-free suite and source policy, record results and commit the focused task.

### Task 2: Continuous source routes for modes, progression, turns and restart

**Files:** Create `scripts/progression_routes.py`, `references/progression-routes.json`, `tests/test_progression_routes.py`.

**Interfaces:** Consumes original `poweron_capsule`, `capture_steps`, `floe_routes.route_policy`, and `trace_compare.compare_traces`. Produces `assess(points, kind, active_start=0) -> dict`, `capture(out, kind, variation, stella='stella') -> dict`, `replay(original, out, stella='stella') -> dict`; routes contain complete inputs, trace, initial/final capsule, restore journal, hashes and explicit completion predicates.

- [x] Test RED then GREEN: require real construction→entry→bonus→initialized next level; regular/advanced starts; actual per-player swaps with the other record preserved; both-empty terminal followed by Reset/recovery; reject truncated/mislabeled/injected/disabled-hazard routes.
- [x] Capture all four variations from cold source power-on with real Select/Reset and active-controller inputs. Acquire progression routes and exhaustion/restart routes with declared bounds; classify exploratory failed routes honestly and refine input policy without changing source state.
- [x] Independently replay exact inputs and restore journal; require full CPU/RAM/TIA/RIOT/input equality and final capsule identity. Publish only compact route summaries.
- [x] Run route unit tests/full suite and commit.

### Task 3: Versioned progression diagnostic and reusable native/paced replay

**Files:** Create `scripts/progression_build.py`, `scripts/progression_play.py`; modify `scripts/hazard_build.py`, `scripts/hazard_paced.py` only for explicit backwards-compatible build version/banner and route-validation callback inputs; add `tests/test_progression_build.py`, `tests/test_progression_play.py`.

**Interfaces:** New build wraps audited contact tables and native core as `0.0.6-progression`, retaining default hazard build behavior. Replay passes the Task2 assessment/helper closure explicitly; old hazard callers continue using existing defaults. Metadata fingerprints every consumed builder/source file.

- [x] Write tests proving default compatibility, progression version/banner, immutable source dependency fingerprints, callback routing and real active-controller input mapping; observe RED, implement minimal API extensions and observe GREEN.
- [x] Build from a clean committed source with accepted source catalogs; run all Task1 boundary cases and Task2 native input-only replays against that exact ROM. Include intentional score/record/state corruption controls that must fail for the named reason.
- [x] Confirm original catalog/helper closure is unchanged, native ABI/bank restore intact, and previous release artifact remains byte-identical. Run full suite/source policy and commit.

### Task 4: Fresh paced, pixel and full-density acceptance package

**Files:** Create `scripts/progression_delivery.py`, `tests/test_progression_delivery.py`; update compact `references/progression-result.json`, reproducible `docs/progression-checklist.md` and `docs/releases/v0.0.6-progression.md`.

**Interfaces:** Consumes complete source replay receipts, current-ROM controlled/native receipts and every original/new route × NTSC/PAL × layout0/1 × width0/1. Produces a fail-closed immutable private manifest and public ROM/build/validation/SHA256SUMS bundle.

- [x] Test RED→GREEN rejection of missing variation/route/view/replay, mixed ROM/source, dirty producers, missing complete states/pixels, unsafe timing, incorrect maxima and ineffective negative witnesses.
- [x] Run all new natural routes plus existing four hazard routes in all eight views/clocks; compare every source CPU/all128RAM state and every completed presented pixel frame. Run the existing fifteen stress modes and intentional spacing/sprite/guard/cache/state failures on the exact current ROM.
- [x] Recompute cycle maxima from raw observations; require unchanged hard budgets, VRAM spacing, sprite and memory guards. If any transition overruns, derive a source-equivalent optimization, prove it and repeat affected acceptance; never relax budgets or skip source steps.
- [x] Seal exact clean-source ROM and raw evidence, derive compact public validation; run whole suite/source policy and commit.

### Task 5: Review, integrate, release and transfer ownership

**Files:** Update local P13 issue, README, `docs/handoffs/issue-13.md`, archive execution ledger, and `references/progression-delivery.json`.

**Interfaces:** Consumes sealed Task4 bundle; produces focused linked PR, exact-head/main CI and byte-identical merged-main rebuild, public prerelease/download verification, final receipt artifacts and a prepared exclusive successor. Terminal operational closure follows the last repository bookkeeping write.

- [ ] Run one fresh whole-branch review; regrade findings by user impact, one RED→GREEN blocking-fix pass with green suite, ledger deferred minors and every disposition. No per-task reviewer or re-review.
- [ ] Move13 In review, push/create/attach focused PR, verify exact-head CI, integrate under existing owner authorization. Rebuild clean merged main and compare ROM bytes to the seal; confirm main CI.
- [ ] Publish prerelease `v0.0.6-progression` at exact tested source with four public assets. Download and compare every asset; notes must name diagnostic limits and concrete human tests.
- [ ] Prepare final delivery receipt/documentation and the dependency-ready successor (#14); verify Frostbite project/cwd and keep it idle. Archive the verified execution ledger and all rulings before terminal operational closure.

## Terminal operational closure

After repository artifacts and the execution ledger are complete, integrate the
receipt-only PR after its exact-head checks, verify clean main, and close13/Done
only after all delivery conditions pass. Send the final explicit sole-writer
transfer with actual main/hash/evidence/limits; verify it through read-only app
state and stop changing this checkout. This ordering follows the owner's
single-writer rule: no repository bookkeeping may follow the transfer.

## Plan self-review

S1/S2 map to Task1 boundary probes and Task2 bonus routes; V1/V2/C1 map to all four mode/terminal/restart routes and per-record controlled probes; V3 maps to all256 level boundaries and continuous progression. Task3 preserves the established native architecture; Task4 owns every timing/view requirement and raw evidence seal. Task5 owns integration/release, separate evidence classes and issue/chat handoff. Existing autonomous approval supplies native execution and routine delivery authorization; no additional permission menu is needed.
