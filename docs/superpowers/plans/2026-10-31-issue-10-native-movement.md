# Native input and movement implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Execute original-equivalent movement and input phases as native Z80, prove them against independent original execution and deliver a measured testable movement diagnostic.

**Architecture:** Statically translate the verified post-visible phase F476→F019 and required subroutines; keep original logical RAM, carry/overflow/decimal and 6507 return-stack writes. No interpreter ships. Source hardware reads/writes terminate at explicit sampled-input/contact/shadow boundaries. A separate contract cartridge runs native slices under openMSX; the integrated diagnostic uses real per-source-step MSX controls and the synthetic measured renderer, with contacts explicitly scripted until #11. Original graphic integration is separate from mechanics and cannot silently change geometry.

**Tech Stack:** Existing pinned .venv/py65, sjasmplus, ALE/Stella and openMSX; standard-speed64KiB MSX1/TMS9918/PSG. Start CPU proof plain32KiB; use ASCII16 only if measured combined code/tables need it, with banked core/phase-data windows and resident input/render code. No system RAM expansion.

**Spec:** docs/superpowers/specs/2026-10-31-frostbite-design.md, local p10 and docs/gameplay-contracts.md.

## Global Constraints

- Original ROM SHA cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834 is gameplay authority. Preserve arithmetic/flags, ordering, phase, coordinates and all128RAM bytes at declared native/source boundaries.
- Full original ROM, generated original-derived assembly/tables/assets and raw evidence stay local/ignored. Public CI remains original-free. Native MSX release contains only needed native code/data, not a resident 6502 interpreter or full source ROM.
- Existing v0.0.1/v0.0.2 binaries remain immutable. Every new testable ROM gets a new versioned prerelease with exact tested ROM/source/hash/current/next/human tests and downloaded-byte verification.
- Contacts supplied by diagnostic fixtures are not native collision acquisition, natural gameplay or full-game equivalence; #11 owns collision integration. Do not invent approximate mechanics to make a demo playable.
- Native body, actual input adapter, mapper overhead and renderer must replace the surrogate in active timing gates. Preserve all layouts/widths/transitions/NTSC/PAL,29cycleVRAM spacing,4slots,guards and VBlank-only commit.
- Owner chose autonomous native inline execution/exclusive checkout; no routine approval menus. One fresh whole-branch review, one material-finding tested fix pass, no redundant rereview.

## Review Focus

1. 6502 BIT/V, decimal invalid-digit edges, carry across loads/stores and physical stack mirrors: full logical CPU/RAM comparison, not watched coordinates alone.
2. Indexed addressing wraps into hardware/RIOT or across source-data bounds: preserve 6507 decode or reject unsupported reads; no Seaquest-address substitutions or generic modulo shortcut.
3. Conflicting/held/diagonal input, selected player0/1, reset/select, PSG15 restoration and BIOS EI: exercise genuine keyboard/joystick device events and DI/register/slot preservation.
4. PAL double source steps, crowded stress-mode transitions and mapper windows: measure real core/input active frames, actual source counts and each selectable mode; no synthetic reserve accepted as native capacity.
5. Stale/dirty/forged evidence or diagnostic contacts mistaken for collisions: complete manifests and negative controls; explicit fixtures, source boundaries and release limitations.

### Task 1: Audited static translation and native CPU contract

**Files:** scripts/native_codegen.py, scripts/native_build.py, scripts/native_contract.py/.tcl, src/native_contract.asm, src/native_cpu.asm, tests/test_native_codegen.py, references/native-contract.json.
**Interfaces:** `decode(rom,pc)->dict`, `reachable(rom,roots,stops)->dict`, `generate(rom)->str` emit source-addressed native labels and needed local data; `build_contract()->dict` produces exact cartridge/symbol/hash metadata; `reference(case)->dict` consumes canonical RAM/register/MMIO stimuli and executes independent py65; `run_contract(cases)->dict` compares native A/X/Y/P/SP and all128RAM bytes.

- [ ] Synthetic tests RED→GREEN for CFG/unsupported flow, addressing/stack/flag semantics, source identity and required local-only generated outputs. Audit legacy generic decode/translation/input patterns and credit selected reuse; discard every source-address specialization.
- [ ] Implement native carry/V/D/I/SP representation, real source return-byte writes and NMOS decimal semantics. Assemble the contract; compare all applicable mechanics/CPU cases plus seeded flag/arithmetic/index boundary cases and continuous movement chains. Deliberate flag/coordinate/order corruption must fail.
- [ ] Run full original-free host suite and actual openMSX native contract with bounded watchdogs. Commit helpers clean before canonical captures. Expected exact CPU/RAM agreement and explicit data/code footprint.

### Task 2: Native MSX input at source boundaries

**Files:** src/native_input.asm, scripts/native_input_check.py/.tcl, tests/test_native_input.py and contract hooks.
**Interfaces:** `sample_native_input` preserves virtual CPU/IX/IY/DI and PSG15, populates source hardware read mirrors for SWCHA/SWCHB/INPT4/5; `input_init` initializes released console controls. Hooks respect fire/source direction timing and selected C7=0/1; sample again per logical step, including PAL catch-up.

- [ ] RED→GREEN raw mapping tests cover all direction combinations, active-player keyboard joining, both joysticks, fire edges/hold/release and F1/F2 Reset/Select. Difficulty switches remain source-owned/unused.
- [ ] Implement audited BIOS SNSMAT/RDPSG/WRTPSG handling, restore PSG15, retain page0 BIOS and return DI. Actual emulated device schedules feed native/source comparisons; poison mirrors to catch stale samples and invert port2 as an expected negative.
- [ ] Full host/native suites and genuine device cases pass with preserved CPU registers/flags/slots and bounded measured adapter cost. Commit and freeze exact producer identities.

### Task 3: Integrated movement diagnostic and active timing

**Files:** scripts/movement_build.py, scripts/movement_bench.py/.tcl, src/movement.asm, renderer table banking only where necessary, tests/test_movement_build.py, local build/bench outputs.
**Interfaces:** Native step consumes original logical RAM and named scripted contact inputs, not inferred collisions; scene adapter copies presentation values without altering logical simulation. Existing renderer prepare/commit uses its tested ABI. Real source-step cost and input calls replace every10k surrogate.

- [ ] RED→GREEN tests for source-step scheduling, source-to-presentation mapping, ROM/header/mapper validation and immutable version identity. Build smallest measured layout; if >32KiB, explicitly bank core/data in a64KiB ASCII16 cartridge and verify bank transitions/BIOS mapping.
- [ ] Provide clearly labeled movement diagnostic: real keyboard/joystick/Reset/Select and source jumps/air/floe transport; selectable scripted contact contexts/stress layouts are diagnostic selectors, not original mechanics. Keep natural collisions/audio/original graphics claims pending.
- [ ] Differential frame/chain tests and full-density real-core/input/render benchmarks cover every layout/width/SPACE-equivalent transition on NTSC/PAL; require consecutive frames, source-step counts, pixels/SAT/invariance,29spacing,4slots,stack/RAM guards and negative controls. Profile/optimize proved bottlenecks if needed; never loosen gates or skip required source steps.
- [ ] Freeze clean exact ROM/helper captures and a reproducible immutable release package. Expected genuine measured positive margins; a boot is insufficient.

### Task 4: Review, release, integration and handoff

**Files:** docs/native-movement.md, docs/releases/<new-version>.md, references/native-result.json, docs/handoffs/issue-10.md, local p10, README.
**Interfaces:** compact evidence binds source/native binary/helper/tool/profile identities; package copies exact tested ROM without rebuilding/relabeling. Notes identify scripted contacts and required human setup/actions/results.

- [ ] Full suite/source policy, one fresh read-only whole-branch review with five Review Focus cases and ledger rulings. Material findings get owned RED→GREEN fixes in one pass/full suite; no second review.
- [ ] Exact-head CI green, focused linked PR integrated, clean merged main verified. Publish new prerelease with exact tested ROM/hash/source/current/next/human instructions; download/verify assets before close/Done.
- [ ] Durable handoff and exclusive transfer to dependency-ready #11 in a separate Frostbite fork, preserving all source/asset/legacy boundaries. Old chat stops checkout edits.

Self-review: p10 input/movement/equivalence/timing/release acceptance maps to Tasks1–4. Full visible TIA execution, natural collision acquisition and complete-game proof are not replaced by the post-visible CPU contract or scripted movement contexts.
