# Source-faithful graphics, HUD, PSG and attract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver issue14 with source-derived live graphics/HUD/attract and built-in PSG events without changing the validated mechanics or exceeding standard MSX1 limits.

**Architecture:** Observe original raster and ordered audio writes at explicit source phase boundaries, independently of the native cartridge. Compile original graphics into finite reusable SCREEN2 fragments and compose dirty bands with bounded sprite repairs; derive HUD directly from canonical source state. Translate the original audio writes to a documented AY approximation without modifying source envelope/scoring state. Retain complete source/native equivalence and remeasure the entire integrated pipeline.

**Tech Stack:** Existing pinned Python `.venv`, Stella7 source/debugger observer, py65 independent source checks, sjasmplus, native Z80/SCREEN2, openMSX C-BIOS MSX1, GitHub plugin/gh.

**Spec:** `docs/superpowers/specs/2026-10-31-frostbite-design.md`, local P14 issue, `references/graphics-contract.json`, `docs/handoffs/issue-9.md`, `docs/handoffs/issue-13.md` and its review/execution archive.

## Global Constraints

- Standard-speed3.579545MHz MSX1,64KiB RAM/16KiB VRAM,TMS9918-family and built-in PSG. No expansions/turbo/disk/additional sound chip.4MiB ASCII16 is permitted.
- Original4096B ROM SHA `cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834` is authority. Preserve all byte/flag/RNG/input/update ordering and logical intervals. No Atari CPU/TIA interpreter in the released ROM.
- Base clean main `f516b9e22b44644bafac222a5565287f8e80a949`, publishedv006 ROM SHA `1223931972bd7e0ec02a8c66805cb30ac0defaad1abd71dd67c9c8a7746be5f6`. Never replace published bytes.
- NTSC59736/PAL71364 cycle limits; IO spacing>=29cycles, <=4sprites/line, VBlank commits, mapper/slot/IFF/stack/heap guards. PAL's existing minimum283cycle margin is not available headroom for new work.
- Preserve original source coordinates separately from target drawing. Default visual mapping follows #9: X=8+floor(3*x/2); sourceY7..185→0..178 and189..201→179..191. Omitted rows must be black; any new contrary observation requires an explicit measured adaptation, never silent clipping.
- Original inputs/disassembly/derived standalone assets, full frames/audio streams and raw proofs remain local/ignored. Preserve all frozen catalog/backend helpers; add a separate observer rather than changing their semantics.
- Every newly qualified human-testable ROM gets its own versioned prerelease, exact ROM/hash/source, current/next/human notes. Development candidates that fail acceptance remain clearly private research; a useful separately delivered diagnostic still needs its own release.
- Automated source, automated target, manual visual/listening and physical evidence remain separate. Do not infer human verdicts from captured screenshots or audio files.
- One exclusive issue14 chat/shared checkout/scoped branch. English code/GitHub, PT-BR user updates. Approved autonomous native execution and routine PR/integration/release policy applies; no repeated permission menu.

## Review Focus

- PAL double steps must retain both ordered audio updates and exact gameplay state during bonus, death, record swap and restart; the second update cannot silently erase an event.
- Audio register7 direction bits and registers14/15 must preserve both joystick ports while tone/noise updates occur, including held/opposite inputs and player changes.
- Score rollover, blank/status glyphs, reserves0/9 and attract blinking must display the original state without feeding any presentation value back into mechanics.
- Unaligned actors, wrapped edges, bear/player overlap and dense object/floe bands must retain source priority, every declared mapped pixel and <=4actual sprite rectangles per scanline.
- A cold start, Select/Reset during attract/bonus, or a diagnostic view transition must not expose half-prepared VRAM, stale cache generations or a falsely successful failed guard.

---

### Task 1: Independent original raster/audio phase observations

**Files:** Create `tools/stella-presentation.patch`, `scripts/presentation_reference.py`, `scripts/presentation_records.py`, `tests/test_presentation_reference.py`, `references/presentation-contract.json`; document `docs/presentation.md`.

**Interfaces:** `parse_records(data: bytes) -> list[dict]` validates versioned complete records with source phase/ordinal, CPU/all128RAM,160×210 indexed raster and ordered `(cycle,address,value)` audio writes. `observe(out: Path, initial: Path, inputs: list[dict], backend: Path) -> dict` runs unchanged original ROM semantics and retains full source state/restore journals. `build_backend(out: Path) -> dict` clones the pinned Stella revision into a fresh ignored directory and applies only the separate observation patch.

- [x] Write original-free tests for truncated/duplicate/out-of-order records, incorrect source phase, missing raw raster, nonblack cropped rows, same-value audio writes, silent intervals and source-state mutation. Run `... unittest discover -s tests -p test_presentation_reference.py -v`; require RED before implementing the parser/observer wrapper, then GREEN.
- [x] Add sidecar-only full-raster/audio observations at F019/visible-end/next-F019 with bounded instruction counts; source ROM, CPU/TIA/RIOT semantics and inputs remain unchanged. Associate a raster with the state that actually drew it, rather than assuming the last completed frame represents newly changed RAM. Record visible-phase and post-visible audio timing separately.
- [x] Build a fresh canonical backend after committing producers. Compare complete source checkpoints and final capsules with retained independent source routes; acquire fixtures for score/reserves/temperature/igloo/day-night/animation/attract, both players and transitions. Preserve source pin nibbles and every input/restore journal.
- [x] Verify repeated observations, backend/patch/helper hashes and actual requested states; retain compact public metadata only. Run the complete host suite/source policy and commit.

### Task 2: General source-derived presentation commands and finite assets

**Files:** Create `scripts/presentation_model.py`, `scripts/presentation_assets.py`, `tests/test_presentation_model.py`, `tests/test_presentation_assets.py`; reuse `original_graphics.py` and approved mapping without altering frozen capture helpers.

**Interfaces:** `describe(rom: bytes, state: dict, layout=0, width=0) -> dict` produces read-only layer/HUD commands with explicit source coordinates, masks, colors and priority. `pixels(rom: bytes, description: dict) -> bytes` is a host reference compositor, not runtime gameplay. `compile_assets(rom: bytes, out: Path, *, measured_palette: dict) -> dict` emits bounded fragment/cache tables and assembly descriptions into ignored output, with bank/RAM/VRAM manifests and hashes. The explicit calibrated palette input is a ledgered adjustment for newly observed colors.

- [x] Test RED→GREEN source font blank/digit/status behavior, valid BCD display/rollover, reserves0/9, full temperature domain,16igloo stages, every level byte/day-night selector and attract phases. Include clipping, reflection, terminal displacement, logical row order, overlap priority and full sprite rectangles.
- [x] Derive masks/placement/HUD from original ROM/kernel observations; no prerecorded route/frame playback tables or another game's rules. Compare the general compositor against actual source rasters on #9's544 fixtures and new source routes. A raw bitmap-table match alone is insufficient for HUD/playfield placement.
- [x] Compile static fragments plus dirty fused bands and bounded repairs. Reject lossy colors/pixels, unsupported bank capacity, allocator overlap, >4sprites/line or >16KiB VRAM. Preserve source mapping independently of any optional diagnostic layout; label adapted diagnostics separately from faithful default evidence.
- [x] Measure generated table/cache resources before runtime integration. Full16KiB/frame upload and a runtime TIA interpreter are rejected alternatives. If a measured packing limit requires a different allocation, ledger the smallest source-faithful change and prove the new domain before emitting a human ROM.
- [x] Run compositor/asset tests, complete suite/source policy and commit.

### Task 3: Native live graphics/HUD/attract compositor

**Files:** Create `src/presentation.asm`, `scripts/presentation_build.py`, `scripts/presentation_check.py`, `tests/test_presentation_build.py`; modify `src/movement.asm` only through explicit profile hooks and audited bank/RAM allocation.

**Interfaces:** `build(...original_catalogs, out: Path) -> dict` produces a new versioned cartridge with complete consumed-file hashes. Native `presentation_prepare` reads canonical state and builds offscreen resources; `presentation_commit` publishes only in VBlank. `presentation_check(out, build_dir, source_observations) -> dict` compares complete VRAM/register dumps and source/native CPU/RAM at aligned boundaries.

- [ ] Test RED→GREEN version/source identity, immutable old builds, bank limits, read-only canonical state, prepare invariance and cache generation changes. Pin declared graphics/HUD ABI and RAM ranges in the build manifest.
- [ ] Implement source-derived fragment lookup/dirty fused-band updates with bounded sprite repairs and safe cache replacement. Retain the four existing diagnostic test paths while adding faithful normal presentation; do not relabel a single default run as acceptance of other layouts/widths. Optional debug presentation must not alter source coordinates or gameplay.
- [ ] Integrate full score, temperature, reserves, igloo, transitions and attract without diagnostic banner obscuring the normal game. The renderer must handle naturally changing values, not just a static snapshot. Preserve every source CPU/all128RAM state.
- [ ] Measure real standard-clock complete frames, including dense animated bands, edge overlaps, newly changed HUD and PAL double-step transitions. Profile any overrun; optimize equivalent work, not quality, source steps or hardware assumptions. Keep failed candidates immutable/private.
- [ ] Run complete host/target checks, retain exact ROM hashes and commit. If this becomes an independently useful human diagnostic before the final issue delivery, publish its own qualified prerelease with exact artifact and limitations under Task6's release gates.

### Task 4: Ordered source audio to built-in PSG

**Files:** Create `scripts/presentation_audio.py`, `src/presentation_audio.asm`, `scripts/presentation_audio_check.py`, `tests/test_presentation_audio.py`; extend the presentation build profile with explicit source-write observation hooks where needed.

**Interfaces:** `events(source_records: list[dict]) -> list[dict]` preserves ordered source audio writes and logical timing. `psg_step(source_registers: bytes, previous: dict) -> dict` returns documented PSG tone/noise/volume writes without mutating canonical envelopes. Native `presentation_audio_step` applies each logical update; reset silences owned channels. The actual-target checker records PSG writes and complete source CPU/RAM/input state.

- [ ] Test RED→GREEN repeated/same-value writes, zero volume, maximal frequency/volume, simultaneous channel activity, PAL two-update frames, source Reset/Select, delayed fish/bonus/death envelopes and channel ownership. Preserve PSG register7 GPIO bits and registers14/15 exactly.
- [ ] Derive source modes/periods/envelopes from actual register events and the pinned TIA implementation. Choose finite AY mappings with explicit pitch/noise/shared-generator differences; preserve original F3/F4 arithmetic and scoring side effects. Do not substitute a high-level event engine that changes mechanics.
- [ ] Integrate at declared logical phase boundaries with bounded queues/overflow rejection, including both updates in PAL double steps. Record unavoidable timing quantization rather than silently dropping/reordering writes. Preserve native ABI/mapper and joystick sampling while sound runs.
- [ ] Compare actual PSG register histories with the mapping of independently observed source writes; test both controllers, input GPIO and mute/reset transitions. Capture local listening artifacts and perform a separate recorded visual/listening review where available; owner/physical verdicts remain pending unless observed.
- [ ] Remeasure the complete graphics/input/native/audio frame pipeline and run the full suite/source policy; commit.

### Task 5: Complete integrated acceptance and immutable delivery bundle

**Files:** Create `scripts/presentation_delivery.py`, `scripts/presentation_suite.py`, `tests/test_presentation_delivery.py`; add compact `references/presentation-result.json`, `references/presentation-config.json`, `docs/presentation-checklist.md` and versioned release notes.

**Interfaces:** Consume the exact current-ROM/source/graphics/audio receipts and every required original/new route×NTSC/PAL×presentation path. Emit only exact ROM/build.json/validation.json/SHA256SUMS as public assets; full raw evidence/manifest remains ignored. Reuse guard-safe harness primitives only after auditing profile/dependency closure.

- [ ] Test RED→GREEN rejection of missing source/native/pixel/audio states, dirty/mixed producers, wrong phase/ROM/profile, incomplete view/clock matrices, inaccurate maxima, fatal positive logs, dropped audio/source intervals and ineffective negative controls.
- [ ] Run all12 retained natural routes with full CPU/all128RAM, actual presented pixels against source-backed expected images, and PSG histories. Add bounded attract/re-entry and simultaneous-input routes. Run all required views/clocks, full-density/toggle/cache stress and relevant controlled boundaries. Preserve original catalog/helper identities unless reacquisition is explicitly justified.
- [ ] Recompute timing maxima from raw rows; require unchanged hard budgets, source cadence, VBlank/IO/sprite/memory/device/mapper guards. Prove intentional pixel/HUD/audio/state/guard failures fail at their intended raw checks. Negative logs never satisfy positive evidence.
- [ ] Seal a clean-source exact ROM and transitive raw artifact identities. Derive public compact metadata only after complete acceptance; verify previous published artifacts remain unchanged. Run full suite/source policy and commit.

### Task 6: Single final review, integration, release and successor

**Files:** Update P14 local issue, README/current docs; create `docs/handoffs/issue-14.md`, execution/review archive and `references/presentation-delivery.json`.

- [ ] Dispatch exactly one fresh whole-branch reviewer on the most capable allowed model, with approved spec/plan, immutable base/head, Review Focus verbatim and every ledger Ruling. Regrade by user effect. Critical/Important enter one RED→GREEN fix pass plus green suite; minors are recorded/deferred. No per-task reviewers or re-review.
- [ ] Move14 In review while delivery remains pending. Push/create/attach focused linked PR, verify exact-head CI, integrate under existing authorization. Rebuild clean merged main and require byte identity with the tested seal; verify main CI.
- [ ] Publish a new versioned prerelease for every delivered human-testable ROM (initial intended final version0.0.7-presentation; use another new version if an earlier diagnostic was already published). Attach exact ROM, hash/source, state/limits, next issues and concrete human setup/actions/expected results/feedback. Download all four public assets afresh and compare bytes/hash/size/tag/source/prerelease status.
- [ ] Integrate truthful final receipts/docs, archive this plan's ledger/review/rulings before removing only its scratch workspace. Close14/Done only after its own DoD and delivery pass. Prepare/reuse the dependency-ready next issue fork in Frostbite, verify project/cwd and transfer sole checkout ownership only after final clean main. Stop all old-chat writes afterward.

## Plan self-review

The approved native architecture and original-reference hierarchy feed Tasks1/2;
live original graphics/HUD/attract is Task3; ordered source-to-PSG adaptation and
GPIO ownership is Task4. Task5 measures their combined cost and all existing
gameplay paths; Task6 owns independent review, immutable publication and terminal
ownership. Research captures/controlled fixtures are separate from natural play.
No stage may spend the old283cycle margin by assumption. A failed allocation or
budget produces a ledgered measured optimization/research result, never a reduced
mechanical contract. Existing explicit autonomous native execution is preserved.
