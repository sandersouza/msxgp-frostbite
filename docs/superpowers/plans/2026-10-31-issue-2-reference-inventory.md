# Issue #2 — immutable reference inventory and measured cadence plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Identify the supplied ROM without silently changing authority and measure source timing across initialization, Reset and Select.

**Architecture:** A standard-library inventory validates immutable source metadata before execution. A headless Stella probe uses isolated settings, explicit reset/input policy and saved-state checkpoints. A version-guarded structural decoder reads emulator cycle/frame/scanline counters; no scanline value is assumed by the parser.

**Tech Stack:** Python >=3.11, unittest, installed Stella 7.0 with debugger; optional ALE 0.12.1 cross-check.

**Spec:** Approved Frostbite design under docs/superpowers/specs/2026-10-31-frostbite-design.md and issue #2 local copy.

## Global Constraints

- Target remains standard-speed MSX1, 64 KiB RAM / 16 KiB VRAM and built-in PSG; this issue builds no MSX ROM.
- Original source: references/roms/frostbite.bin, size 4096, SHA-256 cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834.
- Original inputs, serialized emulator states and complete disassemblies stay local/ignored.
- Unknown commercial revision/provenance must be reported, not inferred from filename/catalog.
- Never rebaseline a mismatching ROM automatically; fail before launching emulation.
- No semantic disassembly, gameplay or full toolchain/scaffold implementation in this issue.
- User already approved native autonomous execution and dedicated issue/fork handoffs.

## Review Focus

1. A same-sized altered image must be rejected before backend execution.
2. Missing/malformed manifest or unknown serialized format must fail clearly.
3. Arbitrary 262-valued bytes must not masquerade as measured frame counters.
4. Startup debugger commands may stop mid-frame or cross multiple frames; observed counters and requested operations must remain separate.
5. Emulator display/autodetection and nominal clock conversion must not be misreported as commercial revision or physical-machine measurements.

### Task 1: Immutable inventory and identification

**Files:** scripts/reference_inventory.py, references/manifest.json, tests/test_reference_inventory.py.

**Interfaces:** describe(data: bytes) -> dict; validate(data: bytes, expected: dict) -> list[str]; load_manifest(path: Path) -> dict; main(argv=None) -> int. The manifest supplies schema_version=1 and one immutable input identity.

- [ ] Write original-free tests for correct 4 KiB structure, vector extraction, malformed size/schema, changed-byte digest rejection and missing input CLI failure.
- [ ] Run unittest discovery and observe the missing inventory implementation fail.
- [ ] Implement the minimum metadata/validation CLI. Default verifies canonical input; --describe inspects metadata without writing authority; --rom/--manifest permit explicit paths.
- [ ] Record supplied size/hashes, 4K layout/reset and raw trailing words, catalog identity and unresolved commercial revision/provenance in the manifest.
- [ ] Run all inventory tests and the real input verification; mutate a temporary same-size copy and prove failure.
- [ ] Commit only utility/tests and compact metadata.

### Task 2: Measured source timing and delivery evidence

**Files:** scripts/source_timing.py, tests/test_source_timing.py, references/source-timing.json, docs/reference-inventory.md, docs/handoffs/issue-2.md; update README/development/issue metadata.

**Interfaces:** read_stella_state(data: bytes) -> dict containing cycles, current_lines, last_lines, previous_lines, frames, layout and RAM metadata; capture(rom: Path, stella: str, output_dir: Path) -> dict; summarize(checkpoints: list[dict]) -> dict. Decoder supports only the validated Stella 7.0 debugger-state format on little-endian hosts.

- [ ] Write synthetic serialized-state tests for both 262/313 values, variable delay queue sizes, decoy values outside the frame manager, truncated state, bad header, invalid queue index/size and unknown layout.
- [ ] Observe tests fail before implementing decoder/probe.
- [ ] Implement structural parsing from upstream 7.0 serialization order, with explicit bounds/format guards; record source links/blob identities.
- [ ] Implement a bounded headless probe in fresh isolated directories. Copy the already-validated ROM locally; generate autoexec.script, reset deterministic CPU/TIA/RAM and use SWCHB 3f/3e/3d for released/Reset/Select. Save ten cold/steady/button checkpoints with actual cycle/frame/scanline values and local artifact hashes.
- [ ] Repeat the same probe in another fresh directory and compare counter/RAM results; record exact backend identity/settings/script hash. Cross-check steady scanlines with installed ALE at frame_skip=1, seed=0, repeat probability=0, documenting its warmup/reset behavior.
- [ ] Record startup partial/nonstandard timing explicitly and derive stable cycles/frame only from aligned observed endpoints. Nominal Hertz is a clock-model conversion, not wall-clock/physical evidence.
- [ ] Run original-free unit tests, real inventory, repeated source capture and negative controls. Expected: identity mismatch fails; decoder distinguishes source values; repeated measurements match; region/revision limits remain explicit.
- [ ] Publish compact metadata/documentation and a durable handoff; synchronize issue copy. Obtain independent review, integrate focused PR, close/Done only on acceptance, then transfer to another fork for the ready successor.

## Execution notes

- Inherited Seaquest inventory/trace code was read for workflow patterns only; no game-specific input paths or state assumptions are reused.
- Native execution stays in the exclusively owned checkout, on codex/chore/2-reference-inventory.
- Source research found that Stella debugger script print results are not exported to its prompt session buffer; saved-state decoding provides actual counters instead.
- A debugger frame command is an operation request, not proof of one completed/aligned source frame. Preserve this distinction in output.
- Self-review: all issue #2 requirements map to the two tasks; decoder negative controls cover the five Review Focus risks; no gameplay/toolchain scope is introduced.
