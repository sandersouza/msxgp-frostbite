# Independent original-execution oracles

The supplied4KiB Frostbite is authority, SHA-256
`cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834`.
Raw states, complete traces, screenshots and ROM copies stay under ignored
outputs. The versioned reference report contains compact observations/hashes,
not original code, graphics or complete state data.

## Reproduce

Use the existing project .venv with py65 1.2.0 and Stella7.0 with Debugger. For
optional ALE research, reuse ALE0.12.1 if present; `requirements-ale.txt` describes
the optional package for a new environment. Do not replace a supplied environment.
Public CI uses only synthetic fixtures and never installs/fetches original ROMs.

```sh
make source-check
make test
make reference-check
make reference-traces
make reference-cpu
make reference-ale
make reference-refuge
make reference-console
make reference-report
```

The original ROM is verified before backend use and after captures. Each run
creates a fresh private directory and prints it. Source helpers/backend binary
hashes are checked against changes during execution. Both full state replays
must agree; any mismatch or watchdog failure prevents acceptance. Preserve the
private directory when investigating a failure. A partial capture is not a pass.
Every local helper and configuration in the declared transitive dependency
manifest must match the producer commit before capture and still match after it.
Publication verifies the same complete manifest; a helper already dirty before
capture fails as well as one changed during the run. Commit intended tool changes
before recapturing; unrelated documentation changes do not affect this check.

For raw-state repeatability or the target-facing projection:

```sh
.venv/bin/python -B scripts/trace_compare.py compare outputs/path/run-a/trace.json outputs/path/run-b/trace.json
.venv/bin/python -B scripts/trace_compare.py project outputs/path/source/trace.json outputs/oracle/logical.json
.venv/bin/python -B scripts/trace_compare.py compare outputs/oracle/logical.json outputs/target/logical.json --logical
```

Replace example paths with the printed run directories. Target logical files
must be produced from actual running target state by a future native adapter.
That runner must separately validate the MSX ROM/commit/machine and record its
execution evidence. This issue defines the adapter contract; no native adapter
or target-equivalence result exists yet.

Frozen hashes belong to the listed producer commits/backends. New runs record
their own tool revision and provenance; later documentation commits can change
provenance hashes while identical source execution still repeats internally.
Do not compare captures with different declared initial states or policies as
if they shared a seed. CPU/MMIO fixtures and naturally reached routes are separate.

## Deterministic initialization and boundaries

The reviewed Stella7.0 source is
[`d55b1aec`](https://github.com/stella-emu/stella/tree/d55b1aec0d067a4c901a6dcdf81cb8f579685659).
M6532::reset randomizes the timer even with RAM/CPU/TIA randomization disabled.
The harness writes a declared TIM1024T preset before the first source instruction,
then freezes only the debugger access counter and emulator host PRNG seed in a
validated power-on state. Original ROM and game RAM are not patched. The initial
controller pins are all high/released, switches3F and source PCF000/cycle0.
This is a controlled initial hardware condition, not every physical power-on.

The structural decoder reads CPU registers/flags, all128RAM bytes, RIOT timer/I/O,
delay queue, frame manager, background/playfield/players/missiles/ball, audio,
analog/latched inputs, shadow registers, cartridge bank, host PRNG, both controllers
and switches. It rejects unsupported/truncated/trailing layouts. TIA core state
is retained completely; the emulator's frontend pixel framebuffer is separate.
The serializer header string is13bytes, and booleans use01/FE.

Every captured gameplay interval ends at PCF019. Startup can contain partial or
multiple raster frames, so32warmup intervals are recorded separately; actual
cycle/frame counters are retained. A loaded input slot must show forward cycles
and nondecreasing frame counters before being accepted as fresh output. Game
Reset's source delay is allowed to expire:80release intervals give active input
scenarios, rather than mistaking early pin changes for movement.

Stella debugger `joy*` arguments are electrical levels:0pressed,1released.
Both port nibbles, both fire pins and console switches are set explicitly every
interval and checked against observed pins. There is no sticky-action RNG or
instruction skipping. See [the debugger documentation](https://stella-emu.github.io/docs/debugger.html).

## Coverage and comparison contracts

The four source variations are selected/reset through original console inputs.
Regular modes0/1 start at logical level00; advanced modes2/3 at04 (manual stages1/5).
The electrical-input route includes independent port directions, diagonals,
opposed-bit fixtures and fire hold/release/repress. Opposed bits are controlled
electrical fixtures, not a claim about a standard stick's physical travel.

Modes1/3 also have a separately labeled C7=01 selected-player fixture. Only that
byte is injected at F019; the ROM then demonstrably ignores port0 and consumes
port1 direction/fire. It does not prove a naturally resolved alternating death
or record swap. Those broader routes remain for progression/full-game delivery.

Raw schema2 includes exact state bytes in each private checkpoint. The comparator
re-decodes those bytes and requires all recorded fields and their hash to match,
then validates full raw inputs and the structured backend/policy. Equal omissions
or placeholders on both sides cannot establish acceptance. Earlier schema1
research traces remain historical and must be recaptured for this interface.
The native logical contract remains v1, with complete structured provenance,
raw inputs, register/RAM types and collision consistency checked before equality.

Raw comparison checks the entire source trace, TIA fields, original state hashes,
input/order and declared provenance. Coordinate, P flag, latched-collision,
ordering, input and seed corruptions are deliberately rejected.

The portable contract `frostbite/source-logical/F019/v1` retains source phase,
requested raw inputs, logical A/X/Y/P/SP, all128RAM bytes and the B0–B9/ED collision
inputs. It omits emulated TIA internals, raw-state digest and physical CPU cycles
from the target comparison. Source provenance stays explicit in the oracle header;
target execution metadata is a separate runner responsibility. Values must come
from the target, never from copying expected source state. The baseline is
conservative: future representation/presentation mappings need an explicit,
reviewed contract rather than silent masks.

## Independent CPU and ALE checks

Stella executes86 existing no-MMIO mechanics fixtures from identical controlled
CPU/RAM, plus288 single-instruction ADC/SBC boundary vectors at the original
FB9B/FBC5 instructions. All374 pairs match py65 1.2.0 for A/X/Y/P/SP/PC and all128
RAM bytes after identical instruction counts. The matrix includes binary/decimal,
carry and invalid-BCD boundary stimuli. It is not exhaustive NMOS opcode/silicon
conformance or naturally reachable gameplay. Fifteen constant-MMIO fixtures are
excluded from this independent CPU-only comparison; they are not TIA evidence.

The secondary [ALE0.12.1](https://github.com/Farama-Foundation/Arcade-Learning-Environment/tree/8a8fafb1ac37796e3e8197a2e5727204fa1b926d)
checks mode0/2 with random_seed1, frame_skip1 and repeat_action_probability0.
Each run advances27API frames, replaying all18legal actions plus edge sequences;
whole serialized system state, RAM, RGB hashes, actions, frames and reward repeat.
Its Python `act` second argument is paddle strength, not another controller.
Its adapter reset/startup is not aligned with the Stella capsule, so no full
cross-backend equality or original two-player acceptance is inferred.
See [ALE's interface](https://ale.farama.org/main/cpp-interface/) for seed/action APIs.

## Natural refuge measurement

Two independent runs repeat all1056 complete states: Bailey lands at X09,
the bear approaches from85hex and stops at0F, and768 subsequent wait intervals
retain grounded shore state, reserve3 and no effective bear contact. This
measures one naturally reached route in advanced mode2, not all geometries.
The [frozen controller recipe](../references/refuge-scenario.json) walks to the
ordinary left bound, waits for the top floe, jumps down/left then up/left and waits
on shore. It uses no game-RAM injection. The acceptance predicate requires a
grounded left refuge, no effective bear hit/death/life loss and a nontrivial
original bear approach followed by a stable blocked edge. The bear pursues the
player; a fabricated automatic back-and-forth patrol is not the source behavior.

The earlier walking-only hypothesis was rejected by actual source execution:
walking reaches X10hex and the bear can initiate the chase. The manual specifically
says to jump up into the refuge. Preserve the original ground/airborne bounds
and measured collision results; proximity or an invented common clamp cannot
replace the original TIA result. [Original manual](https://www.atariage.com/manual_html_page.php?SoftwareLabelID=199).

## Console and frozen evidence

Two independent125-interval runs also verify four Select edges wrapping the
initial mode2 through3,0,1,2; holding Select35intervals repeats to0; simultaneous
Reset+Select retains mode0, confirming Reset precedence. Every full state repeats.

The [compact report](../references/reference-traces.json) records the exact
producer commits, utility/config/backend hashes, private-summary hashes and
trace identities. After independent review, the source capture tools at
eeefccc require complete committed dependency manifests and raw schema2.
The report publisher verifies every declared dependency blob at its producer
commit, including local transitive helpers and configuration. Publication
and source-execution commits have separate identities; a later documentation
commit does not retrospectively produce those captures.

The primary dataset records1472checkpoints across paired warmup/four-variation
and selected-player captures. Route preparation is bound to the primary mode2
trace hash, independently of later summary-publication revisions. Raw evidence
stays local/ignored. Historical aa81b27/35ba252/6445143/dc4c2c3 captures retain
their true producer identities and are not relabeled as new executions.

## Remaining acceptance

Natural whole-game/igloo/fish/final-life/two-player completion, every crowded
geometry and full timing/latency remain their subsystem/regression gates. These
oracles do not establish MSX rendering, audio, PAL adaptation or physical hardware
acceptance. No MSX ROM bytes changed here; the published diagnostic release is
unchanged, and any future changed testable ROM requires a new versioned release.
