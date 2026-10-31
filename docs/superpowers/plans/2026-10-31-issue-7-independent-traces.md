# Independent Atari traces implementation plan

> **For agentic workers:** Use superpowers:executing-plans. Native autonomous execution/design already approved; no repeat approval menu.

**Goal:** Freeze reproducible original-execution oracles for native mechanics, with explicit inputs, complete RAM/TIA evidence, independent CPU checks and deliberate failures.
**Architecture:** Stella7.0 is the four-variation/two-controller authority. A reviewed state codec and deterministic power-on capsule feed bounded debugger batches at PC F019; raw states/traces remain ignored. A strict comparator validates repeated traces and mutations. py65 CPU cases are independently executed in Stella; ALE0.12.1 supplies secondary seeded0/2-mode evidence only.
**Tech stack:** existing Stella7.0 Debugger, py65 1.2.0, existing ALE0.12.1, Python/venv/unittest, no MSX ROM changes.
**Spec:** docs/superpowers/specs/2026-10-31-frostbite-design.md; local p07 issue copy; docs/gameplay-contracts.md; issue4 handoff.

## Global constraints

- Authority4096-byte source SHA-256cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834; validate before backend use and after capture. Never modify it.
- Standard MSX1 target remains64KiB RAM/16KiB TMS9918/built-in PSG; this issue creates reference evidence, not a target ROM/gameplay acceptance.
- All raw states, traces, source clones and derived data remain local/ignored; only compact reproducible summaries/hashes/contracts enter Git.
- Preserve .venv/tools/Seaquest quarantine. Public CI stays original-free and exercises synthetic fixtures.
- Dedicated issue7 fork owns shared checkout, scoped branch, reviewed PR and durable handoff; release only if a new testable target ROM is produced.

## Research decisions

Stella7 initializes RIOT timer randomly unconditionally (M6532::reset), even with RAM/CPU/TIA randomization disabled. An ignored spike demonstrated repeatable game/RAM/timing after an explicit TIM1024T preset. Raw states still differed in the debugger access counter and unused host PRNG. A reviewed power-on capsule sets these bookkeeping/host seed fields before execution; two separate processes then produced byte-identical full states through ten aligned F019 checkpoints. The serializer string length is13; derive offsets structurally, never guessed positions.

Startup F019 passes can span partial/multiple raster frames; freeze after a declared warmup and retain actual cycles/frame counters. No claim that debugger calls automatically equal complete game steps. State/controller/TIA blobs are retained, not inferred from ALE score/terminal shortcuts. ALE exposes only modes0/2, so it cannot certify original two-player modes.

## Review focus

1. Wrong ROM/backend/state layout or truncated capsule must fail before executing/publishing plausible evidence.
2. Different initialization/RNG/inputs/boundaries must not be normalized away or called deterministic merely because cadence matches.
3. Both controllers/console bits/all four variations must be observed, with natural versus injected states explicit.
4. Comparator must reject coordinate/CPU-flag/collision/order corruption and mismatched provenance; no self-generated expectations.
5. CPU-only/BCD agreement must not become TIA/reachability/MSX acceptance; full raw evidence stays private and public CI remains synthetic.

## Task 1: Reviewed state capsule and comparison contract

**Files:** scripts/reference_state.py, scripts/trace_compare.py, tests/test_reference_state.py, tests/test_trace_compare.py.
**Interfaces:** decode_state(data)->dict with CPU/128RAM/RIOT/full opaque TIA/controller/switches and structural offsets; freeze_poweron(data,seed)->bytes edits only declared counter/PRNG fields after validating the power-on shape; compare_traces(expected,actual)->list of precise mismatches.

- [ ] Write failing synthetic-state tests for CPU flags/offsets/variable delay queue, cartridge/controller tail, truncation/wrong schema, invalid power-on normalization; then implement from pinned Stella source d55b1aec0d067a4c901a6dcdf81cb8f579685659. Validate whole RAM/TIA bytes rather than selected friendly fields.
- [ ] Write failing comparator tests with hand-authored coordinates/flags/collisions/order/input/provenance and unequal lengths; implement strict trace identity and per-step comparisons, with no implicit wildcard masks.
- [ ] Run full original-free suite and source gate. Commit task1.

## Task 2: Bounded full-emulator captures and CPU cross-check

**Files:** scripts/reference_traces.py, scripts/reference_cpu_check.py, references/trace-scenarios.json, tests/test_reference_traces.py, tests/test_reference_cpu_check.py.
**Interfaces:** capture_steps(rom,initial,steps,out)->decoded states plus exact raw-file hashes; source capsule/trace schema from task1. CPU cross-check consumes canonical mechanics cases and reports backend differences, preserving complete CPU/RAM observations.

- [ ] Write failing tests for canonical input/backend rejection before execution, isolated/fresh output, bounded commands, all raw controller bits/console switches and strict PC boundaries. Implement debugger batches of at most10save slots; explicit per-step controls, source hashes and watchdogs.
- [ ] Generate independently frozen power-on capsules with declared RIOT preset/host seed, align after startup, select/reset all four variations and replay raw two-controller routes twice in separate processes. Compare full observations/raw state bytes; validate observed mode and control pins. Report naturally executed routes versus explicit controlled fixtures.
- [ ] Independently execute applicable no-MMIO-read mechanics cases plus binary/decimal arithmetic boundary vectors in Stella from identical CPU/RAM; compare py65 full state and document/fix actual NMOS differences with RED→GREEN evidence. MMIO/TIA reachability is not inferred from CPU fixtures.
- [ ] Run deterministic ALE0.12.1 mode0/2 traces with random_seed, frame_skip1/repeat_probability0; assert supported modes and record limitations instead of pretending cross-backend startup is aligned.
- [ ] Run full suite and canonical capture twice, plus coordinate/flag/collision/order/provenance negative controls. Commit task2.

## Task 3: Publish compact evidence, review and transfer

**Files:** docs/reference-traces.md, references/reference-traces.json, docs/handoffs/issue-7.md, local p07 issue copy, Makefile.
**Interfaces:** docs/report consume exact hashes/backend revisions/seed/capsule/trace/comparator from task2; no raw original-derived state becomes tracked.

- [ ] Document command-by-command reproduction, seed and step semantics, independently verified CPU domains, four-mode/two-controller evidence and remaining natural/late-game geometry routes. Include precise coverage and honest incomplete acceptance boundaries.
- [ ] Verify current public CI/all tests/source gate and reproducibility report; move only7 Inreview, create focused PR and obtain one fresh independent review. Fix material findings once with RED→GREEN/full-suite evidence, no redundant re-review.
- [ ] Integrate after delivery checks, close/Done7 and transfer clean checkout via another dedicated fork to dependency-ready successor8. No ROM source/version changes or release are planned.

Self-review: all p07 acceptance items map to tasks1–3. Opaque TIA evidence supports repeatability, while collision samples and future software geometry require explicit aligned interpretation. No circular py65-generated expected state substitutes for Stella execution.
