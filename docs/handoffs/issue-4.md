# Issue #4 handoff — mechanics contracts and bounded source probes

Issue: https://github.com/sandersouza/msxgp-frostbite/issues/4
Branch: `codex/docs/4-gameplay-contracts`.
Base: `15ded9ec33174e037d7ff25127a613c62f446fff` (issue #3 integration).
Initial slice utility commit: `124dcb5432643019e866de082ef09a6a09ce765b`.
Final head, review and integration identity: this issue's delivery PR.
Delivery PR: https://github.com/sandersouza/msxgp-frostbite/pull/22

Read [gameplay contracts](../gameplay-contracts.md),
[101 cases](../../references/mechanics-cases.json),
[recorded results](../../references/mechanics-probes.json), approved design and
the issue copy before implementing a native subsystem. Contracts cover all
requested mechanics, input phases/state/order, boundary routes and explicit
completion/failure predicates. They are not accepted target gameplay.

## Reproduce and evidence

```sh
.venv/bin/python -m pip install -r requirements-reference.txt
.venv/bin/python -B -m unittest discover -s tests -v
python3 -B scripts/reference_inventory.py
.venv/bin/python -B scripts/mechanics_probe.py
```

Existing .venv already contained reviewed py65 1.2.0; the install command is for
reproduction when needed, not a claim of fresh-machine setup (#5). The full
original-free suite passed 33 tests with no skips. Standard python3 also passes
but explicitly skips four CPU-specific tests if py65 is unavailable.
Canonical CPU probes passed all 101 cases and repeated byte-identically as a
compact report. No original inputs are installed/fetched by the dependency file.

Source: references/roms/frostbite.bin, 4096 bytes, SHA-256
`cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834`.
An isolated source clone with a newly created Python venv and only the pinned
reference requirement also passed all 33 original-free tests. Missing private
ROM input fails clearly. This validates that optional Python test path, not
the complete macOS cross-development setup required by #5.
Results record exact utility/case/map hashes and backend version. Probe input
contains explicit RAM/registers and constant MMIO samples; results contain
compact state/events, not complete source or original graphics.

CLI guards the input before backend loading, checks all start/stop/executed PCs
against reviewed instruction boundaries, bounds execution and rejects unexpected
results or undeclared hardware reads. A provisional F5D0 case accidentally
started at an operand byte; a synthetic regression failed before boundary
validation was added, then passed. The canonical bad entry was also rejected;
the case was corrected from the listing to F5D1. This prevents plausible output
from invalid entry points becoming research evidence. RIOT read-alias behavior
was likewise checked against upstream M6532 and corrected with RED→GREEN.

## Important findings for successors

- F2 is hazard attachment/push state. Free floe transport uses B9 and bit 6 of
  row state, while attached threats use F2 and bit 7. The prior compact map's
  broad occupied/carried name is clarified in this issue.
- Opposed horizontal inputs prioritize left; opposed vertical inputs select
  up. Fire is a phase-specific falling edge shared through AF, gated by EA=0.
- Joystick normalization follows countdown filtering: on (81&07)=0 and C6!=0,
  force the sampled Y to FF and decrement C6. Its expiry may set C5 bit 7 and
  jump through the X=D4 partial reset before writing 84 or sampling the console.
- Jump EA starts 0F/1F and advances on even frame-counter values. Each vertical
  arc has 15 updates and net 26 decimal pixels; input and parity boundaries
  matter. No high-level parabola or constant animation timer replaces it.
- Initial CD=FF needs sixteen activations to reach 0F. A new incomplete row
  activation wins over same-step reversal; completed igloos keep progress but
  can still earn white-row points. Partial reversal needs a block and costs one;
  completed reversal is free. Door entry requires shore/up, CD=0F, X=78–7F.
- Fish scoring is twenty delayed ten-point updates through the audio envelope,
  not an immediate atomic 200. F7>=0C prevents new fish selection; it does not
  erase existing fish or cap collection. F7 survives a life reset.
- Temperature decrements only on its reachable main-path/frame gate; delay,
  phase or bear-chase branches can skip it. Preserve BCD and live flags.
- Both-player exhaustion is a source dispatcher/record condition, not ALE's
  CC-zero/F1-bit7 terminal shortcut. ALE exposes only modes 0/2. Full two-player,
  temperature-final-life and restart acceptance needs broader reference traces.
- Magic fish display is selected by CB>=14 (twenty decimal), not a score
  comparison; day/night uses CB bit 2. Progression remains a byte while block
  scoring plateaus at level 9. Do not invent a difficulty/level cap.
- FA/FB still overlap initialization return addresses; retain #3's three-call
  depth and phase-aware RAM ownership. Legacy/snapshot preservation is unchanged.

## Evidence boundaries and successor

The slice bus models address decode and RAM/stack mirrors, with constant MMIO
stimuli and write records. It is not a TIA/RIOT timing emulator. No natural
reachability, pixel geometry, NMOS-wide flag conformance, source frame latency,
full-game trace or target equivalence is inferred from these probes.
Issue #2's full-state capture mismatch remains unresolved; #7 owns aligned
initialization/RNG/input and independent full-emulator oracles. Required routes
R01–R13 have completion/failure predicates and explicit timeout design bounds;
they are pending evidence, not completed runs. Left-shore refuge in particular
needs real TIA geometry and natural-play confirmation.

After review/integration, close #4/Done and start dependency-ready #5 in another
Frostbite fork (verify live dependencies first). It supplies macOS toolchain and
the first MSX diagnostic scaffold; no inherited Seaquest runtime is validated.
Only the new issue chat owns the shared checkout after dispatch. Do not delete
.legacy/seaquest/ or the external snapshot; final removal belongs to #17.

No MSX ROM was produced in #4. Every later testable ROM, including a useful
diagnostic, needs a versioned release/prerelease with exact ROM attachment,
SHA-256/source commit, state/limitations, next steps and concrete human tests.

## Independent review and scope decisions

Fresh review reproduced 33 tests and the initial 99 cases/report. It also
independently executed both complete jump arcs and the full fish envelope,
confirming fifteen vertical updates/26-pixel displacement and twenty score
calls/200 points. Those remain CPU-slice corroboration, not natural TIA routes.

The Important input-contract finding was reproduced with a nonzero C6 on its
eight-frame gate. I1/C1 and two new cases now cover neutral filtering and the
early attract reset; expected input from the old interpretation failed before
the correction and passes afterwards.

The reviewer graded the fish segment assertion gap Minor. The executor treated
it as Important because the named contact-effect case could accept deletion
of its core H3 state mutation. An in-memory negative control replacing F93F's
store with two NOPs initially passed the case; adding observed/expected DC=03
now rejects the mutation (DC remains07). The canonical 101 cases, repeated
report and all 33 tests pass after both corrections. No deferred minors remain.

The reviewer set aside these behaviors; retained boundaries and costs are:

- Full NMOS/BCD flag conformance remains #7; py65 alone cannot justify accepting
  an incorrect native flag adapter.
- TIA/refuge geometry, naturally reachable states and complete routes remain
  #7/later gates; fixtures must not be upgraded into natural gameplay proof.
- MSX fidelity/performance/hardware remain later delivery; no target ROM exists
  here, so accepting native behavior or publishing a fake release would be wrong.
- Full fresh macOS toolchain acceptance remains #5; the fresh Python-only clone
  check above cannot stand in for cross-assembler/emulator/setup verification.
- Prior full disassembly classification remains #3's reviewed input. Relevant
  paths were checked here and F2 clarified; unobserved-path coverage is still
  unresolved rather than silently certified by this issue.
