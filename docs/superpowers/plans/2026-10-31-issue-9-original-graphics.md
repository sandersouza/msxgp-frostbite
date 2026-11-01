# Frostbite original graphics implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prepare deterministic, ROM-traceable graphics and prove their coordinate/palette/resource mapping before native integration.

**Architecture:** A local extractor decodes original tables and an independent ALE raster suite executes the unchanged original ROM in controlled presentation states. A SCREEN 2 compiler maps captured frames into actual VRAM, decodes them independently and measures adaptations/resource bounds. Public source contains algorithms, contracts and compact hashes, never original-derived pixels or generated tables.

**Tech Stack:** Existing Python .venv, stdlib, ALE0.12.1/numpy, existing original-free CI. No added dependencies.

**Spec:** docs/superpowers/specs/2026-10-31-frostbite-design.md and .github/issues/frostbite/p09-extract-original-graphics-and-map-msx1-presentation.md.

## Global Constraints

- Standard-speed MSX1, 64 KiB RAM, 16 KiB VRAM, TMS9918-family VDP and built-in PSG; no expansions.
- Supplied ROM SHA-256 cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834 is authoritative. Preserve collision/simulation bytes.
- Original inputs, raw frames, full disassembly and generated original-derived assets stay ignored/local.
- This issue prepares assets and mapping; native animation/runtime integration belongs to subsequent native work. Neither native timing nor a new ROM is claimed from offline VRAM compilation. Keep v0.0.2-renderer immutable.
- Use the owner's approved native inline execution and exclusive checkout; one fresh whole-branch review, one material-finding fix pass, no redundant review.

## Review Focus

1. ALE RAM edits change before the visible frame: capture actual before/after identities, verify requested states occurred, never count intent as coverage.
2. Raw tables differ from raster timing/width/reflection: compare decoded actor/digit masks against actual original pixels, and retain raster-derived floes/igloo/footer.
3. Day/night and overlap can exceed two colors per SCREEN2 byte: measure every changed pixel and reject unrecorded loss; do not call approximate RGB original color fidelity.
4. Cropping, wrapping, edge actors and bank Y128: exact mapping covers x0..159/y0..209 and resource/address bounds; source bytes remain untouched.
5. Forged/stale/corrupt producer or evidence: pin ROM/backend/helpers, require independent repeats and negative controls; publish a compact allowlist, not raw derived content.

### Task 1: Source catalog and mapping contract

**Files:** scripts/original_graphics.py, scripts/graphics_mapping.py, tests/test_original_graphics.py, tests/test_graphics_mapping.py, references/graphics-contract.json.
**Interfaces:** `catalog(rom: bytes) -> dict` produces named table views with source ranges/shape/colors; `map_x(x:int)->int`, `map_y(y:int)->int`, `compile_screen(pixels:bytes)->dict`, `decode_screen(vram:bytes)->bytes` consume indexed pixels and produce bounded SCREEN2 VRAM plus loss/resource facts.

- [ ] Write/run failing synthetic tests for reverse row order, reflection/double width, rejected identity/ranges, complete coordinate mapping, exact two-color packing/independent decode, deterministic over-color adaptation, bank boundaries and invalid shapes.
- [ ] Implement catalog, explicit palette/mapping contract and VRAM compiler. Keep raw pixels out of public fixtures. Run full host suite, expected green; commit.

### Task 2: Original execution, deterministic extraction and target fit

**Files:** scripts/graphics_reference.py, tests/test_graphics_reference.py, Makefile, ignored outputs/graphics/, assets/generated/.
**Interfaces:** `capture(rom_path, destination) -> dict` consumes Task1 catalog/compiler, records controlled original executions and actual asset coverage; `validate_capture(report)->None` rejects incomplete/different/dirty evidence. Local outputs include original and mapped previews/VRAM/catalog; compact facts feed Task3.

- [ ] Write/run failing tests for actual-state coverage, complete independent-repeat equality, pixel/ROM/state corruption, invalid dimensions and evidence allowlist.
- [ ] Implement deterministic fresh ALE instances, frame_skip1/sticky0/seeded explicit controls and controlled RAM presentation fixtures. Prove actor/digit table masks against raster pixels, capture animation/day-night/igloo/rows, record source state identities and unchanged simulation inputs across mapping.
- [ ] Generate twice and compare byte identities; compile/decode each full frame, count exact deviations/resources, test corruption rejection. Commit helpers clean before canonical evidence; run full suite and original suite. Expected explicit complete facts, not assumed animation coverage.

### Task 3: Review and delivery

**Files:** docs/original-graphics.md, references/graphics-result.json, docs/handoffs/issue-9.md, local p09 and README.
**Interfaces:** Compact report contains only counts/hashes/producer/resource/adaptation facts. Handoff names the generated local resource paths, integration limits and successor ownership.

- [ ] Document exact reproducible commands and original comparison evidence, all coordinate/palette/packing deviations, measured resource fit and integration work still required. No runtime timing or physical acceptance is inferred.
- [ ] Full suite/source policy, one independent whole-branch review; reproduce material findings RED, one fix pass GREEN/full suite. Exact-head CI must pass before integration.
- [ ] Merge focused PR, verify clean main, close/Done9 only after acceptance. If runtime ROM bytes change, add a new versioned tested/download-verified prerelease; otherwise no new ROM release.
- [ ] Durable handoff and exclusive transfer to dependency-ready #10 in a dedicated fork; old chat stops edits.

Self-review: all p09 acceptance maps to Tasks1–3. Offline full-frame packing is an asset fit check, not a real-time upload strategy. Existing renderer timing is unchanged; original-compatible dynamic integration must remeasure every mode later.
