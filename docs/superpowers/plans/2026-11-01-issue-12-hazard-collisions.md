# Hazard acquisition and original interactions implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans in this exclusive issue checkout. The owner approved autonomous native execution; do not reopen design, method or successor approval menus.

**Goal:** Deliver original threat/fish/bear collision acquisition, RNG and interaction ordering, including natural crowded play on a standard MSX1.

**Architecture:** Keep the native F476→F019 game core and real input. Extend the independently observed original-clock boundary to all eight row windows and the sticky shore latch. Compile lossless source observations to native lookups; measure representation size and full frame cost before accepting it. No Atari interpreter or collision inferred from the synthetic renderer.

**Tech Stack:** Pinned Stella 7.0, Python/py65, sjasmplus Z80, openMSX, SCREEN 2, ASCII16.

**Spec:** docs/superpowers/specs/2026-10-31-frostbite-design.md; .github/issues/frostbite/p12-port-hazards-fish-bear-and-collision-semantics.md; docs/handoffs/issue-11.md; docs/gameplay-contracts.md H1–H3/F1.

## Global constraints

- Standard-speed MSX1, 64 KiB RAM, 16 KiB VRAM, TMS9918-family VDP, built-in PSG; no expansions/turbo/disk.
- Original authority SHA-256 cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834. Preserve all 128 canonical RAM bytes and logical CPU registers, source cadence, input boundaries, RNG and event order.
- Sole checkout ownership transferred from issue 11 after its closed/Done, clean-main and integrated-receipt gates. Base d6f214fd8923e11eea5cd3f71bdbb0cdb7ec93f7; branch codex/feat/12-hazards-collisions.
- Preserve published 0.0.1–0.0.4 ROM identities, old frozen captures, original-free CI and ignored legacy. Original ROM/disassembly/derived data/full states remain local and ignored.
- Source capture helpers/backend/capsules must be committed and frozen. Historical producers remain historical; changed helpers require new capture or an explicit unchanged dependency proof.
- The 0.0.4 PAL stress margin is only 232 cycles. Every runtime/input/renderer change requires fresh full-density and paced natural evidence with 29-cycle VRAM spacing, four sprite slots, VBlank commit, guards and uninterrupted source steps.
- A new testable ROM is 0.0.5-hazards with its own prerelease, exact tested bytes/hash/source, current limits, next work and human tests. Automated, manual-emulator and physical acceptance remain separate.

## Review focus

1. Inactive D8=0 object copies and left-edge hidden clocks still acquire original odd-window ghost contacts; object count zero must not become an invented empty mask.
2. Row and shore CXCLR/read boundaries, both electrical latch bits and sticky ED retain complete CPU/RAM effects, including airborne states and source blanking.
3. Fish removal/delayed points, attached-row pushing, low-index simultaneous contacts, bear refuge and RNG calls preserve the actual source dispatch and ordering across seeds/stages.
4. Dense PAL catch-up and transitions include real hazard acquisition/rendering without dropped simulation, stale caches, changed device state or relaxed timing budgets.
5. Observation/lookup/replay provenance and negative controls reject incomplete domains, mixed backends, changed raw bytes, altered RNG/collision/state and stale release artifacts.

### Task 1: Complete original-clock observation and bounded representation proof

**Files:** create scripts/hazard_truth.py, scripts/hazard_domain.py, scripts/stella_hazard.py, scripts/hazard_observer_check.py, scripts/collision_blocks.py, scripts/collision_compact.py, tools/stella-hazard.patch, tests/test_hazard_truth.py, tests/test_hazard_domain.py, tests/test_hazard_observer.py, tests/test_collision_blocks.py, tests/test_collision_compact.py; local outputs/hazards/; document references/hazard-contract.json and docs/hazard-collisions.md.

**Interfaces:** `full_record(data: bytes) -> dict` decodes a strict 674-byte record: nine 58-byte two-channel literal-view windows (row indexes 0..7, shore index 8), 128 RAM bytes, A/X/Y/P/SP and 19 glyph bytes. `observe(rom,binary,initial,cases,out) -> (bytes,receipt)` executes unchanged original instructions. An additive observation patch applies after the frozen floe patch; the old command/protocol remains unchanged. `contacts(record,ram) -> {rows:bytes[8],shore:int}` selects the actual one of 228 views.

`collision_blocks.put_row(packer, records: sequence[bytes]) -> (bank,address)` interns a complete 160-coordinate row through ten 16-cell blocks of bank-local three-byte pointers. Its independent decoder checks original coordinate bounds and physical bank-local pointers. This measured representation proof changes no source collision result or published ROM; Task 2 consumes it only after size and access-cost acceptance.

The smaller candidate `collision_compact.CompactRows.intern_row(records) -> row_id` / `emit(first_bank) -> PackedRows` uses fixed 32-byte record/block pools, 16-bit IDs and sparse row bitmaps. A record retains its own bit6 value only after verifying all 228 shadow bits are uniform; otherwise compilation rejects it. `read_row(banks, metadata, root, index)` reconstructs all 58 original bytes independently. Task 2 owns complete-domain capacity and native access-cost acceptance.

`hazard_domain.shapes(rom)` includes initial pointer zero and every animated pointer; `object_modes(rom)` enumerates all shape/reflection/NUSIZ tuples without byte truncation. `bear_modes(rom)` returns representative source EF values and all eight pose aliases, deduplicating only byte-identical source pointers. Keeping domain derivation separate avoids freezing unrelated native/test harness imports during long source-only capture.

- [x] RED→GREEN protocol tests reject partial records, invalid padding/views, and wrong electrical low bits. Implement strict decoding without proprietary fixtures.
- [x] Extend only observation sidecars to acquire every original row/shore read and both latch channels, including CXCLR and P0 data-dependent update events. Retain the old binary/capture trees; build the new pinned backend separately.
- [x] Compare literal actual-view samples and complete CPU/RAM against unmodified Stella for boundary/reflection/shape/count cases, all four rows and shore, blanking and sticky ED. Run: `.venv/bin/python -B scripts/hazard_observer_check.py --binary outputs/hazards/observer-shore-source/stella --out outputs/hazards/observer-check-clean-d`. Expected: zero differences and exact frozen helper/backend/capsule receipts; failed models remain exploratory.
- [x] Enumerate animated and cold-cleared object shapes, reflections, NUSIZ copies, coordinates and vertical windows from source instructions. Prove source/header/row/prefix invariances and lossless record/tree encodings with raw independent observations; do not assume translation, empty D8=0 or glyph-independent coefficients. Measure bounded representation prototypes. Full-domain footprint and actual native access costs are Task 2/4 gates, where their inputs and implementation exist. A rejected factorization is recorded and replaced, never promoted.
- [x] Run `.venv/bin/python -B -m unittest discover -s tests`; expected all pass. Commit clean source helpers before canonical acquisition.

### Task 2: Native all-channel lookup and complete boundary equality

**Files:** create scripts/hazard_catalog.py, scripts/hazard_tables.py, scripts/hazard_query.py, scripts/hazard_build.py, src/hazard_contacts.asm, tests/test_hazard_tables.py; modify conditional integration in src/floe_visible.asm and src/movement.asm; local outputs/hazards/.

**Interfaces:** `capture(out,binary,initial_path,workers=4) -> manifest` freezes the complete measured domain with bounded independent source workers. `compile_catalog(root,out) -> manifest` emits byte-exact bank-local tables and rejects overflow/missing raw proof. `RawContacts(root).contacts(ram)` queries raw observations independently of compiled ROM data. `hazard_acquire` writes only odd C031/C033/C035/C037 and negative sticky C06D; canonical state remains C000..C07F, dedicated scratch C790..C79F. `build(catalog,out)` emits 0.0.5-hazards ASCII16 with WITH_HAZARDS and WITH_FLOES; restore bank 2 before the core.

- [x] RED→GREEN original-free compiler/query tests cover exact interning, complete-domain receipts, bank-local bounds, corrupt records and every source ghost/blank/sticky gate. Implement the measured lossless representation and measure complete-domain footprint/native access cost; do not ship a capacity or timing overflow. Include cold A3=0 alongside 32 animated pointers (264 edge shape/reflection/NUSIZ modes; no 8-bit mode truncation). Any ordinary single-copy/NUSIZ-copy alias requires independent source-clock proof before use; otherwise retain full actual mode profiles.
- [x] Integrate the native lookup conditionally so existing ROMs retain byte identity. Keep the original instruction core as the threat/RNG/score authority.
- [x] Run actual-ROM full-visible CPU/all-128-RAM comparisons against complete unmodified original phases, replacing issue 11's 287 declared neutral odd/shore fixtures with real channels. Include count 0..3, all shapes/reflections, both edges, all rows, shore, blanking and sticky carry-over. Expected: zero differences, exact mapper/stack/device state and no contact injection in the production path.
- [x] Full host suite, clean producer commit, complete canonical source catalog and fresh target boundary capture. Preserve raw paths/hashes and explicit test counts.

### Task 3: Hazard/fish/bear mechanics, RNG and continuous routes

**Files:** create scripts/hazard_mechanics.py, scripts/hazard_routes.py, references/hazard-routes.json, tests/test_hazard_routes.py; reuse audited full-ROM/real-device harness in a scoped hazard adapter.

**Interfaces:** `assess(points,route_kind) -> assessment` requires bounded explicit predicates for fish collection/reward envelope, threat attachment/push/recovery-or-death, bear chase/refuge and water/temperature loss. Routes record cold/reset preparation, complete CPU/RAM/TIA/RIOT/input checkpoints, seed, restore journal and final state. Controlled seeded fixtures and natural input-only routes are separately labeled.

- [ ] RED→GREEN predicate tests reject truncated routes, wrong reward/death ordering, disabled hazards and missing source continuity. Implement frozen directional/fire policies with declared maximum lengths and useful failure artifacts.
- [ ] Match the original native instruction paths for grounded/airborne threats, row priority, fish segment removal and delayed points, already-present fish after F7=0C, attachment and direction, bear onset/refuge/chase, deaths and simultaneous events. Include multiple meaningful source seeds/stages and both players.
- [ ] Capture/replay continuous input-only original routes and run their real-key target counterparts with all contacts target-owned. Expected: every complete CPU/RAM checkpoint matches and each explicit interaction predicate passes; no synthetic contact/expected-state writes.
- [ ] Negative controls alter a real collision, RNG state/order, row priority and shore sticky bit and must fail their intended comparison. Run full host suite; commit before canonical target captures.

### Task 4: Crowded paced acceptance and immutable diagnostic package

**Files:** create scripts/hazard_paced.py, scripts/hazard_bench.py, scripts/hazard_delivery.py, associated Tcl adapters and original-free acceptance tests; docs/hazard-collisions.md, references/hazard-result.json.

**Interfaces:** paced capture consumes the tested build and frozen input-only original routes; checks every source state and every completed frame/pixel. Stress suite includes NTSC/PAL, both layouts/widths/toggle orientations, real count 0/1/2/3 and nonempty→empty cache transitions. `seal(config,out)` enforces all source/backend/helper/raw-replay/target identities before writing a new immutable bundle.

- [ ] RED→GREEN acceptance tests reject wrong ROM, incomplete observer/catalog/replay, missing scenario, dirty producers and stale negative controls. Reuse audited gates rather than weakening them for the new workload.
- [ ] Run whole-ROM paced routes and crowded stress with actual new acquisition/core work. Expected: no dropped source steps, budget overrun, pixel mismatch, visible preparation writes, unsafe VDP spacing, fifth sprite or guard/device failure. Optimize only measured bottlenecks and re-run affected full gates.
- [ ] Freeze a clean exact 0.0.5-hazards ROM and compact validation/SHA/build files. Keep full original/private evidence local. Verify prior published ROM identities and all host tests.

### Task 5: Independent review, release and dedicated successor

**Files:** local p12 issue, README, docs/releases/v0.0.5-hazards.md, docs/handoffs/issue-12.md, archived execution ledger and compact delivery receipt.

- [ ] One fresh read-only whole-branch review on the most capable model checks the five focus classes and ledger rulings. Regrade material findings; one owned RED→GREEN fix pass and full green suite, no rereview loop.
- [ ] Exact-head CI, focused linked PR, clean merged-main checks and versioned prerelease attach only exact tested ROM/SHA/build/compact validation. Download every asset and verify bytes before close/Done.
- [ ] Synchronize local/live issue, record source/ROM/limits/evidence and exclusive pending-file ownership. Prepare a separate Frostbite issue 13 fork; transfer only after issue 12 acceptance/integration/release gates and stop editing this checkout.

Self-review: Tasks 1–2 own all original collision channels, including invisible inactive-object contacts; Task 3 owns interaction/RNG/reward/death predicates and natural continuity; Task 4 owns actual crowded timing and proof sealing; Task 5 owns review/integration/release. Original presentation/audio and full-game/hardware acceptance remain later gates. Native layout/factorization choices are evidence-driven engineering decisions under the approved exact-mechanics constraints, not permission to approximate.
