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

Qualified ordinary-enemy component extends the same host/fixture/assembly files with
`--component enemy`. Its common-profile geometry matches25,740cells ×228views.
Source04a3454 passes6,094,440actual Z80 cases:192code+1,078data bytes including
shared P0glyph pages/offsets. Floe regression passes1,193,944calls with identical
ROM/cycle statistics. Independent review verifies final native receipts without
Critical/Important blockers. See `docs/compact-ordinary-component.md`.
No default-game source is changed. PR45 is draft, issue44 In progress.

Next shore research: `outputs/compact/issue44-bear-common-01` proves exact
geometry across4,267,200shore common-Xcells ×228views, playerX25..151, all
source bear positions/modes/Y.123shared17-row footprints plus a138-byte directory
occupy2,229bytes; source bottom two rows are blank in these aliases. This is
host-only; no shore Z80 implementation yet. Boundary research stays separate:
all9,859stored bit7 masks admit adjacent-byte-equality event atoms, but the
first Y-relative edge model is incomplete and must not replace the old tables.

Shore follow-through: source3d9a173 is now fully qualified for the common-X
domain,1,132,704native cases,137code+2,747data bytes (518shared),81..1,540cycles.
635host tests pass. Independent review verifies all native outputs/files and
frozen sources. Prior floe/enemy fixtures rebuild byte-identically; one-case
smokes are not new complete native reruns. All three components occupy6,451
logical bytes before integration. See `docs/compact-shore-component.md`.

Edge work remains open. `issue44-floe-edge-events-03` represents every edge
column exactly with adjacent-byte event atoms, but `issue44-edge-storage-01`
measures51,159bytes for its first explicit lookup/DAG encoding. Reject that
encoding for the compact runtime. Investigate a bounded source-clock/event
calculation instead. `issue44-edge-counter-01` captures unmodified Stella7.0
counter states across nine player positions and two ice rows. Run its helper
with SDL dummy video/audio also in the parent environment: backend `-help`
otherwise timed out before creating a capture. No default game changed.

Edge follow-through: `issue44-edge-event-model-03` corrects the rejected02 model's
GRP/ENAM one-color-clock delay; all816,000edge cells ×228views match. Sparse04
and analytic01 agree independently. Maintained sourcec79bfb2 qualifies all24,000
native horizontal mask-generator cases,652code+666data bytes,32scratch+32output,
19,352..24,969cycles (about6.98ms worst before convolution).640host tests pass.
Independent review reproduces all masks/assets and verifies final raw/native
hashes. See `docs/compact-floe-edge-masks.md`. This is geometry only; native
view/Y convolution and combined electrical outputs remain pending. Do not
promote without full-frame IRQ/cadence measurement and optimization if necessary.

`issue44-edge-evaluator-domain-01` measures666distinct five-mask row tuples and
2,086distinct39-byte full programs across the24,000horizontal cases. A row
evaluator can be qualified over all tuple/tag/view inputs, separately from the
already-qualified geometry generator. A full-program comparison can follow.
No row evaluator source exists yet at this handoff update. The earlier scope
and source hashes remain immutable; any later source extension needs its own
source-bound receipt.

Row follow-through: source78c1d8a qualifies3,340,656native tuple/tag/view calls,
101code bytes and518shared data bytes,99..419cycles.641host tests pass; the
horizontal-generator24k regression is byte/cycle identical. Independent review
reconstructed all666tuples from captured native masks and verified the final
receipt. See `docs/compact-floe-edge-row.md`.

Accumulation WIP: source322bd13 and `scripts/compact_floe_contact_probe.py`
classify actual captured geometry into2,086distinct39-byte programs. Expected
bit7 bytes come directly from v30. Independent review verifies all24,000class
members preserve source responses across34Y×228views, and reproduces the
16,170,672-byte expected corpus.100k native smoke passes,126wrapper+101row bytes.
Combined geometry calls, shadow merge and game integration remain separate.

ACTIVE LONG CHECK: `outputs/compact/issue44-edge-contact-native-full-02`, exec
session88297, source322bd13. Do not edit its six frozen sources or any of the232
baseline sources until completion: compact_floe.py, compact_floe_edge.py,
compact_floe_contact_probe.py, compact_floe_edge.asm, compact_floe_edge_row.asm,
compact_floe_edge_contact.asm (under scripts/ or src/ as appropriate).
Raw expected count16,170,672calls, actual target48,512,016bytes. New files and
documentation/private research outside those hashes may proceed meanwhile.

Full accumulation01 was stopped incomplete because permitted-write callbacks
made the16M run exceed its watchdog estimate. STOPPED.txt documents rejection.
The322bd13 guard watches the exact complement of allowed write regions instead.
Smoke02 is byte-identical to smoke01 across100koutputs AND cycles (38.9→13.1s
host runtime; this is observer speed, not a game gain). Negative CPU writes to
7000/C7D0/C800/F400 all fail in `issue44-edge-write-guard-neg-02`; neg01's0.1s
watchdog fired during BIOS boot and is rejected. These checks remain local.

Long-check completion: full02 now passes all16,170,672native calls. No source
freeze remains active. Receipt sourcec7a08c1 contains the same six sources as
322bd13. Cycles75/3,129.210546mean/6,711P95/6,775max. Independent review verifies
all outputs,14files and6source hashes, class membership and direct-ROM expected
bytes. See `docs/compact-floe-edge-accumulation.md`. Combined caller, shadow
merge, layout and cadence remain pending; C800 fixture buffers overlap current
NAME pages and are not an integration allocation. Logical component total7,996B.

New hazard host research: ordinary analytic03 matches every exceptional-X
cell:33shapes×2reflections×4copy counts×33playerX×160objectX×26Y,36,241,920cells
each with228views. Analytic02 was rejected (2,064columns) because its alignment
missed the X153 right-tail bit;03 corrects that threshold. Shore clock02 passes
all3aliases×2reflections×160playerX×160bearX×35Y =5,376,000cells ×228views.
Both are private host results, not target code proofs.

Untracked next files at this update: `scripts/compact_hazard_edge.py`,
`tests/test_compact_hazard_edge.py` and its plan. Six hand-derived tests pass.
The new ordinary/shore analytic compiler still needs the complete maintained
host proof and source commit, then native context/query qualification. The shore
compiler keeps18rows (including the clearing row), omitting only the final row
whose old/new source glyph bytes are both verified blank. It includes initial
bear fine motion: body=(bx+(bx<15?6:1))%160, clocks=14-(bx%15).

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
