# Issue44 — compact native formats

Issue: https://github.com/sandersouza/msxgp-frostbite/issues/44
Dedicated successor chat: `Frostbite — ISSUE #44`, forked in the Frostbite
project0fd5a899-599e-40d4-988e-46b3d31433dd, workspace
`/Users/sandersouza/Developer/msx-gamePorts/frostbite`.
Branch: `codex/enhancement/44-compact-native-formats`, from the integrated PR43
main commit. Resolve and record that exact merge SHA before implementation.
The dispatch message also carries the verified integration SHA.

Inventory continuation: integrated starting commit
`57d32b526757ac4ce3deb72323c4f163112dfe49`. Issue44 owns this checkout exclusively.
See `docs/compact-native-inventory.md` and its compact receipt for the read-only
storage/coverage measurements and finite collision-factor experiments. All
new raw work is in `outputs/compact/issue44-*`; older controls remain immutable.
No product ROM bytes or upper RAM/VRAM allocation changed. Do not mistake the
completed inventory for completion of this issue's ROM/COM/BIN deliverables.

Qualified standalone component: `scripts/compact_floe.py`, `compact_floe_probe.py` and
`src/compact_floe_kernel.asm` implement a standalone floe kernel, unlinked from
the default game. Host proof checks8,704,000shadow cells,7,888,000interior cells
and54,400cells ×228views. The shadow channel reduces further to a scalar rule
with zero table bytes. Source3370af7 passes1,193,944native cases,
186code+3,147data bytes,141..1,227cycles including CALL/JP. Independent review
verifies the final receipt with no Critical/Important blockers. This is full
qualification of the declared component corpus, not whole-game cadence or new
formats. See `docs/compact-floe-component.md`. Boundary/enemy/shore equivalents,
flat layout/loaders and whole-frame qualification remain pending. An additional
host-only ordinary-enemy experiment identifies seven collision rows versus
eight visual rows; preserve this source timing distinction.

Ordinary-enemy component WIP extends the same host/fixture/assembly files with
`--component enemy`. Its common-profile geometry matches25,740cells ×228views.
Smoke02 passes30,000actual Z80 cases:192code+1,078data bytes including shared
P0glyph pages/offsets. Full native corpus and a fresh floe regression are pending.
Do not edit the three component sources while those qualifications run; source
fingerprints are checked before/after. No default-game source is changed.

## Authority and ownership

The owner approved v0.0.30 as stable/enjoyable and requested closing42 and this
successor on2026-11-13. Preserve its graphics, colors, mechanics, controls, PSG
and accepted cadence. Scope is a complete <=32 KiB mapperless cartridge attempt,
an actual native MSX-DOS COM and a genuine BASIC BLOAD BIN.64 KiB RAM/16 KiB
VRAM remains the target, with no memory mapper, MegaRAM or turbo requirement.
32 KiB feasibility must be measured; do not promise it before the inventory.

Read `.github/issues/frostbite/0044-compact-native-formats.md`, AGENTS.md,
docs/project-workflow.md and current Obsidian0-/GitHub guidance. The predecessor
only prepares tracking/handoff. Product implementation starts exclusively in
this successor fork. After dispatch, the Issue42 chat stops checkout writes.
The new chat owns all subsequent pending files and must verify a clean tree.

## Exact baseline

- Release v0.0.30-reference-credit-diagnostic,4 MiB ASCII16.
- ROM e75535923a5751e3f4924dc7a3a2f762041b825efb7a5336650d35890cd3ff1d.
- Runtime9915dab1c4c431a62b68c4886cdf788b1983f774;232 source hashes.
- Canonical local build: `outputs/presentation/credit-reference-at/build-final`.
- Public evidence: `references/reference-credit-result.json` and
  `references/reference-credit-delivery.json`.
- Native/scene/audio checks and619 host tests pass. Four fresh regular/bear
  NTSC/PAL routes retain v29-identical source CPU, NAME ownership, IRQ and
  picture-timing buffers. Regular32.539/30.999FPS; bear29.698/25.079FPS.
- Owner approval is in `docs/handoffs/issue-42-owner-acceptance.md`. It is later
  evidence, not a rewrite of sealed publication-time acceptance flags.

All prior releases and sealed outputs are immutable. Do not regenerate inside
`credit-reference-at*`, `credit-as*`, AR/AQ or predecessor result directories.
Create fresh issue44 output roots. Original4 KiB ROM and Atari800CAR remain
local in references/roms; these and complete disassemblies/generated assets
must not be staged. Legacy removal remains issue17.

## First work and reference infrastructure

Start with a live-byte inventory: padding, duplicate/prepared tables, reachable
runtime versus diagnostic code, compression and startup versus steady-state
RAM/VRAM costs. The4 MiB format is not fixed by changing mapper metadata.
Preserve the accepted runtime as a measured rollback/control.

Read `docs/baseline-preservation.md` before selected inherited reuse. The live
Seaquest project provides audited Normal/COM precedents, but no Frostbite proof:
`../seaquest/docs/native-delivery.md`, `../seaquest/docs/handoffs/issue-35.md`,
`../seaquest/scripts/play.py` and `../seaquest/scripts/run_com.tcl` exist locally.
Audit current source before adapting. C-BIOS cannot substitute for a real
DOS boot test; use actual BIOS/DOS configurations for COM/BIN validation.

Report a concrete compact architecture from measured bytes, then implement
in this chat. Never truncate/rename the existing ROM or trade accepted graphics,
mechanics or cadence for a size claim. Keep39's remaining cadence goal and15/16
timing/full-game/physical acceptance separate. Every useful new testable ROM
gets a versioned prerelease with exact ROM/hash/source and human loading tests;
attach native COM/BIN candidates and their own provenance when available.
