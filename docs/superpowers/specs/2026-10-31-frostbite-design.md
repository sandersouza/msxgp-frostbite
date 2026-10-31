# Frostbite for MSX1 — approved design and delivery roadmap

Date: 2026-10-31. Status: approved by the owner in the planning chat on 2026-10-31;
issue #1 repository preparation has started. No gameplay implementation started.
Repository: https://github.com/sandersouza/msxgp-frostbite
Tracking: https://github.com/users/sandersouza/projects/7

## Intent and non-negotiable acceptance

Port the supplied Atari 2600 Frostbite to a standard MSX1: standard-speed Z80,
64 KiB RAM, 16 KiB VRAM, TMS9918-family VDP and built-in PSG. No expansion,
turbo, additional sound chip or disk dependency. The RAM baseline follows the
copied project instructions. Cartridge capacity is separate from system RAM.

Preserve original mechanics exactly against the identified ROM: state transitions,
integer arithmetic/flags, update ordering, input sampling, movement, collisions,
random sequence and game-time cadence. Visuals and sound should be the closest
achievable on the target hardware. Record unavoidable presentation differences
explicitly; never change mechanics to conceal a rendering or performance limit.
Exact equivalence is an acceptance objective, not a claim established by this plan.

## Verified starting point

- Local branch main at ba9a6dd; origin points to msxgp-frostbite.
- Only README.md is tracked. The copied source, scripts, tests, documentation,
  workflow, license and references are untracked user-provided material.
- The tracked README still advertises Seaquest. Copied AGENTS.md and
  docs/project-workflow.md also name Seaquest. Those delivery rules must be
  adapted to Frostbite before any issue implementation.
- Input: references/roms/frostbite.bin, 4096 bytes.
- SHA-256: cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834
- MD5: 4ca73eb959299471788f0b685c3ba0b5 matches Stella's
  "Frostbite (1983) (Activision)" entry. This establishes catalog identity;
  region/revision and actual frame cadence still require explicit verification.
- Research-only automatic DiStella output rebuilt with DASM byte-identically
  on 2026-10-31. This proves round-trip identity, not correct semantic labels
  or complete code/data classification. Generated material remains ignored in
  outputs/frostbite-planning/.
- Available: Python 3.14.7, openMSX 21.0, Stella, DASM, gh, copied local .venv
  with ale-py 0.12.1, sjasmplus 1.24.0 and DiStella.
  Presence is not a successful fresh setup or a tested Frostbite development environment.
- Verified copied tool revisions: sjasmplus d379eeac9ad3857fb48fd3a3929175d0a56038ce;
  DiStella 1015ae53b2d222320eb706c220186305fcac55dd.
- The copied inventory/rebuild scripts require Seaquest and Atari 800 inputs.
  The translator contains source-address-specific optimizations. None may be
  assumed generic or validated for Frostbite.
- Project #7 already has Backlog, Ready, In progress, In review and Done,
  plus Priority, Size and Estimate. No Frostbite issues existed at inspection.
  No repository milestone exists. Native issueTypes is null. Priority labels
  are absent; record priority in issue bodies and project fields rather than
  silently changing shared configuration.

## Approaches considered

1. **Recommended: native Z80 translation with an independent original oracle.**
   Reuse audited development infrastructure and selected hardware adapters from
   Seaquest; reconstruct Frostbite-specific contracts from its ROM. Keeps the
   strongest route to exact mechanics, with up-front research and timing work.
2. High-level recreation from observation/manual. Quicker initial demo, but weak
   evidence for byte/flag behavior, rare collisions and update ordering.
3. A resident Atari CPU/TIA interpreter on MSX1. Retains source execution but
   adds a large runtime burden; reject as the default direction for the target.

The owner approved the recommended native Z80 direction and autonomous execution
in the planning chat on 2026-10-31 ("aprovado, pode seguir"). The approval includes
the testable-ROM release policy added after the initial proposal. Repository
preparation is issue #1; scaffolding and gameplay follow their own dependencies.

## Reference authority and initial findings

Authority order: supplied ROM executed under a validated Atari backend; annotated
ROM disassembly tied to that hash; original Activision manual; emulator/game
adapters and other secondary material as corroboration. Resolve disagreements
by probing the actual ROM. Do not use another platform's port as game authority.

The original manual identifies four Game Select variations, including alternating
players and advanced starts; difficulty switches are unused. The button reverses
the occupied floe with an igloo cost until completion. White-to-blue row changes,
igloo entry, remaining temperature, reserves and day/night progression need
individual contracts. Airborne steering, grounded collision behavior and the
shore refuge deserve boundary probes. Exact thresholds and timing come from ROM
execution, not these descriptions. [Activision manual](https://www.atariage.com/manual_html_page.php?SoftwareLabelID=199)

Stella catalogs score bytes at $C8–$CA, level at $CB and variation at $80.
ALE's Frostbite adapter reads reserves at $CC and a terminal flag at $F1.
These are research leads, not an accepted state map. ALE's adapter exposes
single-player modes 0 and 2; do not mistake that API for full validation of all
four original variations. Use Stella scripting/instrumentation or a verified
backend extension when needed for two controllers, Reset, Select and switches.

## Proposed technical design

- **Native game state:** retain the original logical coordinate system, byte
  widths, wraparound, BCD/flags and phase boundaries. Z80 code generation may
  help, but all Seaquest-specific substitutions must be removed or rederived.
  No Atari interpreter in the released cartridge.
- **Hardware boundary:** replace TIA/RIOT services with explicit MSX video,
  input, timing and PSG adapters. Reproduce collision inputs and latch/reset
  timing in software from original geometry; a VDP overlap flag alone is
  insufficient evidence of Atari collision equivalence.
- **Renderer:** start with SCREEN 2, tile-based shore/igloo/ice and selected
  hardware sprites for actors. Benchmark this hypothesis before committing
  to a sprite allocation or animation scheme. Preserve collision coordinates
  independently from drawing coordinates. TI specifies a maximum of four
  sprites on a horizontal line; measure crowded landings, threats and transitions.
- **Timing:** measure original cadence first, then use a rational accumulator
  to decouple game steps from 50/60 Hz presentation if justified. On 50 Hz
  output some source steps may share a displayed frame; simulate every required
  step with correct input and collision timing. Measure worst-case double-step
  frames, VRAM access spacing, audio and input latency together. A roughly
  60,000-cycle 60 Hz frame is an initial planning scale, not an accepted budget.
- **Cartridge:** begin with the smallest suitable ROM layout; measure code,
  tables and bank-switch cost before selecting plain ROM or ASCII16.
  Do not inherit Seaquest's 128 KiB layout automatically. A normal banked
  cartridge does not imply expanded host RAM.
- **Assets/audio:** derive Frostbite-specific sprites, colors, masks and event
  timings locally. Adapt only the presentation to MSX constraints. Compare
  temporal sound behavior and arrange separate listening acceptance.
- **Cross-development:** macOS host to Z80 cartridge with pinned sjasmplus;
  DiStella + DASM for Atari disassembly/rebuild; Python in project-local .venv;
  ALE/Stella for reference runs; openMSX for target probes and replays.
  MADS/Atari 800 support is unnecessary unless new evidence justifies it.

## Reuse and migration boundaries

Retain a verified external local snapshot of the supplied copy before moving or
deleting anything. Record provenance and licenses for reused infrastructure.
The copy must not be committed wholesale: it contains old evidence and
original-derived generated assembly that need an explicit distribution audit.

Candidates for reuse after inspection: setup/check/dry-run pattern, pinned
assembler provisioning, ROM header/build checks, openMSX Tcl harness, hash
packaging, original-free CI and the issue/PR/handoff workflow.

Rebuild specifically for Frostbite: reference manifest, disassembly labels,
trace extraction, native translation configuration, gameplay adapters, graphics,
sound tables, renderer allocation and all acceptance reports. Seaquest's oxygen,
diver, enemy and scoring modules are not Frostbite implementation.

Before the first issue begins, correct active repository identity/instructions
and isolate inherited evidence so no old success is reported as Frostbite proof.
The final cleanup removes obsolete source, tests, docs, screenshots, workflows,
binaries, release links and game-specific tool dependencies after replacement
passes in a clean clone. Keep concise credit/provenance when required.
ROMs, complete disassemblies and original-derived generated assets remain
local/ignored under the inherited reference policy.

## Delivery and chat protocol

This is the planning chat. Creating backlog items is planning; starting their
implementation is a separate transition.

For every issue:
1. Check dependencies, matching issue chat, actual branch and dirty files.
2. Create/reuse a dedicated Frostbite issue chat by forking this context.
   Use "Frostbite — ISSUE #N" to avoid collision with Seaquest issue titles.
   Verify it belongs to this Frostbite project and has the intended workspace.
3. Provide a durable handoff: issue URL, scope, dependencies, branch/commit,
   dirty-file ownership, exact artifact hashes, evidence, limitations and next action.
4. Move only that Frostbite item to In progress when its issue chat actually
   starts work. Use codex/<kind>/<N>-<slug> branches and focused linked PRs.
5. The previous chat stops editing the shared checkout. At most one issue
   implementation uses it at a time. An isolated worktree is a fallback if
   concurrent work would otherwise overlap.
6. Move to In review while checks/review remain pending; close/Done only when
   that issue's own acceptance criteria and integration are satisfied.
7. Continue to a dependency-ready successor through another dedicated chat,
   without asking for routine implementation permission again.

GitHub issue bodies and repository documents are English. User updates are
Brazilian Portuguese. Local issue copies precede publication. Use existing
project fields and preserve unrelated items. No milestone will be invented.
If native issue types or priority labels are unavailable, record their intended
values in the issue body and report the limitation.

## Testable-ROM release policy

Owner instruction, 2026-10-31: every distinct testable ROM version must have a
GitHub Release with the exact MSX ROM attached. This applies from the first
useful diagnostic/scaffold test through playable milestones; do not describe a
diagnostic as a playable game. Development/test builds use versioned prereleases.

Each release must explain:
- Current state: implemented behavior, verified checks and known limitations.
- Next steps: the next planned work and relevant issue links.
- Human test request: emulator/hardware setup, ROM loading/mapper instructions,
  controls, concrete actions, expected results and what feedback/evidence to return.

Attach the tested ROM and its SHA-256/build metadata tied to the source commit.
Run appropriate automated checks before publishing; distinguish those results
from pending manual and physical tests. If a new version is offered for human
testing, its release and downloadable ROM are part of that delivery. Never
replace an already published version's binary silently. Publish a new version
when the ROM changes. No release is required for documentation-only changes.

## Acceptance strategy

- Round-trip original disassembly plus reviewed entry points, RAM, TIA/RIOT
  interactions, indirect control flow and data tables.
- Deterministic reference capture: source hash, backend/tool revision, initial
  state, seed, frame_skip=1, sticky/repeated-action probability=0 and raw inputs
  at explicit source-step boundaries. Include all supported console/controller
  inputs and meaningful random states.
- Independent original execution versus Z80 state comparisons; avoid deriving
  expected values from the translated implementation. Include negative controls
  that intentionally alter a flag, coordinate, collision or update order.
- Subsystem tests plus continuous natural-play routes: construction/entry,
  reversal costs, water/contact/temperature deaths, fish, bear, progression,
  extra-life cap, alternating players, game over and restart. Define completion
  predicates, maximum route length and failure output before recording results.
- Worst-case active-play CPU/VRAM budgets on unexpanded MSX1 50/60 Hz models,
  including transitions and double-step frames. Report measured margin.
- Public CI uses synthetic fixtures and does not fetch proprietary ROMs.
  It proves build/test integrity only. Local reference equivalence, automated
  emulator checks, manual visual/listening review and physical-hardware
  acceptance remain distinct evidence classes.
- Final package: exact ROM hash, mapper/size/RAM requirements, reproducible
  build, complete-game/replay results and explicit remaining manual/hardware gates.

## Proposed phases and dependencies

The companion backlog contains full draft acceptance criteria and estimates.
P01–P17 are planning identifiers, not GitHub issue numbers.

- Foundations: P01 (workflow/preservation), P02 (ROM), P05 (toolchain), P06 (CI).
- Reference: P03 (disassembly), P04 (mechanics), P07 (independent traces).
- Presentation feasibility: P08 (renderer), P09 (assets).
- First playable: P10 (movement), P11 (ice/igloo/temperature), P12 (hazards).
- Complete game: P13 (progression/modes), P14 (HUD/audio/attract).
- Delivery: P15 (timing), P16 (full-game acceptance), P17 (cleanup/package).

P02 → P03 → P04 → P07 is the reference chain.
P01 → P05 → P06 is the environment chain.
P07 + P05 → P08; P03 + P08 → P09.
P07 + P08 + P09 → P10 → P11 → P12 → P13 → P14.
P06 + P14 → P15 → P16 → P17.
Use dependency order, never numerical order alone. Size/hour estimates are
planning ranges with reverse-engineering uncertainty, not elapsed-time promises.
Split an issue if its measured scope exceeds a focused reviewable change.

## Reproducible research checks already run

From the repository root (macOS, tools already present):

```sh
shasum -a 256 references/roms/frostbite.bin
md5 -q references/roms/frostbite.bin
mkdir -p outputs/frostbite-planning
.tools/distella/distella -paf references/roms/frostbite.bin > outputs/frostbite-planning/frostbite.asm
dasm outputs/frostbite-planning/frostbite.asm -f3 -ooutputs/frostbite-planning/frostbite-rebuilt.bin -loutputs/frostbite-planning/frostbite.lst -soutputs/frostbite-planning/frostbite.sym
cmp references/roms/frostbite.bin outputs/frostbite-planning/frostbite-rebuilt.bin
```

Result: DASM completed successfully; cmp found no differences.
Do not use DiStella -r, which can relocate mirrored addresses and change bytes.
No Frostbite MSX ROM was built or gameplay-tested in this planning pass.
The future environment issue must supply a separate clean-machine checklist
for setup/check, build, smoke, reference, full-game and packaging commands.

## Sources consulted

- [Original Activision manual, electronic reproduction](https://www.atariage.com/manual_html_page.php?SoftwareLabelID=199)
- [Stella catalog](https://github.com/stella-emu/stella/blob/master/src/emucore/stella.pro)
- [ALE Frostbite adapter](https://github.com/Farama-Foundation/Arcade-Learning-Environment/blob/main/src/ale/games/supported/Frostbite.cpp)
- [TI TMS9918A/9928A/9929A data manual](https://computers.baffa.tec.br/pages/datasheet/TMS9918A_TMS9928A_TMS9929A_Video_Display_Processors_Data_Manual_Nov82.pdf)
- [DiStella documentation](https://github.com/johnkharvey/distella)
- [sjasmplus installation](https://github.com/z00m128/sjasmplus/blob/master/INSTALL.md)
- [openMSX manual](https://openmsx.org/manual/user.html)
- Local copied docs/project-workflow.md, scripts/environment.py,
  scripts/reference_rebuild.py and scripts/core_codegen.py.
