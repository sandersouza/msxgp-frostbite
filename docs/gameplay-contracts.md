# Original Frostbite mechanics contracts

Issue [#4](https://github.com/sandersouza/msxgp-frostbite/issues/4).
Authority: the supplied 4096-byte ROM, SHA-256
`cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834`.
Addresses/byte values below are hexadecimal unless explicitly called decimal.
CB is zero-based: CB=00 is displayed level 1.

These are requirements for the native port, supported by source review and
bounded CPU probes. They are **not** accepted Z80 behavior, reachable-state
coverage, TIA collision geometry or full-game replay. The [state map](../references/disassembly-map.json)
and [frame/hardware analysis](reference-disassembly.md) provide the source sites.
Each native subsystem must preserve the specified ordering and pass an aligned
original-versus-target comparison before its gameplay fidelity is accepted.

## Evidence and reproducible probes

The [case definitions](../references/mechanics-cases.json) contain 101 explicit
start/stop PCs, initial RAM/registers, constant hardware samples, instruction
bounds and independently derived expected observables. The
[recorded results](../references/mechanics-probes.json) identify the source,
py65 1.2.0, utility, case file and reviewed disassembly-map hashes. Cases include
artificial boundary states; their execution is not evidence that those states
arise naturally during play.

With the existing project environment (fresh setup belongs to #5):

```sh
.venv/bin/python -m pip install -r requirements-reference.txt
.venv/bin/python -B -m unittest discover -s tests -v
python3 -B scripts/reference_inventory.py
.venv/bin/python -B scripts/mechanics_probe.py
```

Installation is only needed if the optional backend is absent; no original
ROM is installed or fetched. Standard-library tests can also run with python3;
CPU-specific unit tests explicitly skip when py65 is absent. A full evidence
run uses .venv and must have no skips. The CLI verifies the canonical input
before loading the backend, requires the reviewed py65 version, and validates
every start/stop/executed PC against the reviewed code partition. Every case
has an instruction limit; mismatched expectations or undeclared MMIO reads
fail, rather than supplying invented input/collision values.
Unspecified initial RAM is zero; CPU defaults are A/X/Y=0, SP=FF, P=30 before
explicit case overrides. These controlled preconditions are not power-on or
natural-gameplay initialization claims.

The bus decodes 6507 ROM and RIOT RAM/stack mirrors. Hardware reads are **only
explicit constant stimuli**, and hardware writes are recorded without device
effects. It does not advance RIOT timers, implement WSYNC, TIA pixels, bus
residue or collision latches. No CPU cycle count is advertised as frame time.
py65 decimal results require independent Stella confirmation in #7 before
they serve as the complete NMOS flag oracle.

The original [Activision manual, electronic reproduction](https://www.atariage.com/manual_html_page.php?SoftwareLabelID=199)
corroborates variations, controls, row construction, threats, scoring, airborne
protection and the left-shore refuge. The exact byte rules below come from the
ROM sites/probes. Another platform's port or an emulator adapter is not the
authority when it disagrees with this image. No Seaquest gameplay rule is used.

## State and source-step ordering

One source step follows the measured 262-line/19,912-CPU-cycle frame cadence.
Source clock phase and input sampling must be preserved independently of MSX
50/60 Hz presentation. Exact wall-clock scheduling and worst-case double-step
performance belong to #7/#15; skipping a drawn frame must not skip simulation.

The loop is F019 → visible kernels → overscan → sync/input → gameplay → FAE7
→ F019. In particular:

1. The visible kernel samples separate shore, object and floe collision windows.
2. Overscan may swap players, rebuild the igloo buffer, update audio **and
   points**, reduce row contacts, accumulate movement fractions and sample fire.
3. Sync increments 81; slow clock/attract flags update on its wrap. SWCHA is
   sampled at F630; console Reset/Select is processed at F665.
4. E7 delay and C5/C6 gates precede F1 dispatch. Active gameplay then updates
   row objects/graphics, contacts, construction/reversal, movement, temperature
   and bear state in original order. Several branches skip later work.

Rendering/input/audio adapters may change presentation, but must supply the
same logical inputs at these boundaries and retain all gameplay side effects.
FA/FB are not exclusive variables: three nested initialization calls use FA–FF
as return storage. Scratch/pointer snapshots require their PC/phase.

| State | Contract |
|---|---|
| 80, C7, C8–CD / CE–D3 | Variation, active player, active/saved six-byte score/level/reserves/igloo record |
| 81, 82, E7 | Wrapping frame phase, RNG byte, state delay; no arbitrary wall-time replacement |
| 84, AF, FB | Selected active-low joystick nibble, previous selected fire sample, falling-edge latch |
| 91–94 | Packed row state: bit 7 controls object direction; bit 6 controls floe direction; low bits select object behavior |
| B0–B7, B8, B9 | Four even floe/odd object contact pairs, reduced object-contact row, reduced floe-contact row; negative means none |
| E4/E6, EA, F2 | Player Y/X, jump trajectory phase, **hazard attachment/push row**; normal floe transport uses B9 while F2 is negative |
| AB–AE, CD, F5/F6 | Row color/activation, igloo progress, row-reset cooldown and landing latch |
| E5, E8/ED, F7 | BCD temperature, bear X/sticky shore collision, collected-fish counter controlling future spawns |
| F1, F3/F4 | Multi-bit game phase, audio/event envelopes including delayed scoring |

## Input and movement contracts

**I1 — controller selection and phases.** F630 samples SWCHA into Y. Before
normalization, F633–F64F filters that sample: when (81&07)=0 and C6!=0, force
Y=FF and decrement C6. If it reaches zero, decrement it again to FF; with
C5 bit 7 clear, set that bit and take the X=D4 partial-reset path before
normal joystick/console processing. Otherwise continue with the neutral sample.
When F651–F65C is reached, the retained sample's high nibble becomes 84 for
C7=0, low nibble for C7=1. Bits 0/1/2/3 mean up/down/left/right, active low.
Fire is read earlier at F5AD from INPT4/5 using the then-current C7.
AF is shared previous-sample state, not an invented per-player latch. FB is
set only for a 1→0 fire-bit transition and EA=0; hold/release or an airborne
press does not generate another reversal. The countdown-filter/expiry cases
also check that input can be neutralized, or its old 84 retained across the
partial reset, even when SWCHA contains a direction.

**I2 — raw combinations.** Preserve the ROM's branches for simultaneous bits.
Both horizontal directions pressed prioritize left (FA4D–FA6A), not neutral.
The up/down selection tests bit 0 first; both vertical directions select up.
MSX keyboard/joystick mapping must not silently normalize these raw inputs.

**M1 — jump.** EA=0 means grounded; a permitted up/down input starts EA=1F/0F
(F982–F9BA). E4=1B is the shore. Up from there needs the completed-door gate
described below; downward jump is blocked at E4>=70. At F9BC, an even 81
advances the trajectory: decrement index, add the signed table delta to E4,
and end when index is 10 or 00. Each arc has 15 vertical updates, net -26/+26
decimal logical pixels; phase parity determines which source step performs
the first update. Do not replace the table with a parabola or fixed animation
duration. End-of-jump clears ED and sets the landing latch F6 negative.

**M2 — horizontal control and carry.** While free (F2 negative), manual
horizontal motion uses 98 when jumping, otherwise 81&1; shore/airborne
bound checks differ. Free floe contact uses B9, floe direction bit 6 and 96
before manual movement; the carry result is clamped at 09/97 in that path.
F2>=0 instead follows the contacted object's movement (97 and direction bit 7)
and inhibits ordinary steering/jump/reversal paths. These states must remain
distinct even if a renderer draws them similarly. See grounded-object-attaches,
airborne-left-steering and coordinate cases.

**M3 — integer/fractional arithmetic.** FFD0 derives 96–98 and keeps three
low-nibble accumulators in 99–9B; fractional carry conditionally adds one to
the integer step. FCEA selects addition/subtraction using incoming carry.
FF5B normalizes the coordinate with two comparisons/subtractions: values
F0–FF subtract 60, then values >=A0 subtract A0. This is not generic modulo
160 for every possible byte. Preserve flags/wrap, not only screen position.

## Floes, construction and entry

**F1 — collision reduction.** B0–B7 signs are reduced at F566: visit high row
indexes first and overwrite B8/B9, so a lower index wins simultaneous contacts.
CXCLR sites F1FC/F25F/F307 and the separate read windows are part of the
contract. A whole-frame bounding box or VDP overlap flag is insufficient.
The probe supplies contacts; #7 must establish their original TIA geometry.

**F2 — activation.** With a floe contact B9>=0, F6 negative and AB+row=0C,
F8CD–F8F8 changes that row to 98, starts F5=10, clears F6 and awards 95.
CD increments unless already 0F. Initial CD=FF is a sentinel, so the first
activation makes 00; sixteen activations reach 0F. Blue rows do not award
another block on landing. Completed igloos keep CD=0F but white-row activation
can still score. A new incomplete activation branches past reversal: build
occurs before fire's reversal request in that step.

**F3 — whitening.** Once F5 is zero, CD!=0F and no row remains 0C, F9ED–FA07
restores all four rows to 0C. F5 decrements only when gameplay reaches F6C5;
do not turn its 10 hexadecimal count into unconditional wall-clock frames.
Test the last-blue-row and cooldown-boundary cases separately.

**F4 — reversal.** The F8FB–F91B gates require CD nonnegative, F2 negative,
FB negative and B9 nonnegative. Toggle bit 6 only on the contacted floe row.
Decrease CD unless CD=0F; a completed igloo reverses free. With no block yet,
CD=FF inhibits reversal; shore/no-floe, an airborne edge, held fire and hazard
attachment do not reverse. Preserve simultaneous landing/reversal ordering.

**F5 — door and completion.** Up on shore requires CD=0F and unsigned
7F−E6<08 (F993–F9A4): X=78–7F inclusive. It sets E9 negative and begins the
upward trajectory; later movement holds X=7B while the entry latch is active.
E4<06 at F9DB sets E4/E9=0 and F1=40, E7=40. Merely completing CD or drawing
a door is not level completion. Probe cases bracket both X edges and an
incomplete door. Visual door geometry and natural reachability still need #7.

## Threats, fish and temperature

**H1 — row threats.** Row state &03=01 denotes fish; other presented types are threats.
When EA!=0, F8B2 branches past grounded row-contact handling. With EA=0,
object contact B8 can set F2 to the row and derive push direction from the
object direction bit; row updates then carry Bailey toward the edge. Do not
convert every contact into an immediate life decrement. F2 stays attached
until original state/reset logic clears it. Test crab/bird/clam presentations
with the same source logic and their distinct geometry/movement schedules.

**H2 — bear/refuge.** ED negative only affects the chase at CB>=03 and EA=0
(F7BB–F7FE). The chase decrements E6 and changes animation/audio, skipping
later ordinary gameplay; at selected frame phases E8>=10 decrements by one,
so that contact path can reach 0F. Normal bear movement has separate pretests
and 97-sized increments; do not impose an invented common hard clamp.
The manual's extreme-left refuge requires a natural TIA collision route: a
CPU fixture with ED=0 cannot prove it. Airborne bear contact is inhibited.

**H3 — fish.** Grounded contact with low kind 1 increments F7, clears a segment
bit in DC+row using the player/object offset table, rebuilds the display and
sets F4=5B/E7=10 (F92C–F94A). Points arrive in the F4 envelope at F4DB–F4FC,
not as a single immediate 200-point mutation. Countdown values with low two
bits nonzero call FB95 with 10; the full envelope yields twenty such awards
(200 decimal). Test its ordering with reserve thresholds and death/transition.
At F7>=0C, FBCB avoids choosing a **new** fish kind. Already-present fish are
not deleted by that threshold, and F7 survives a life reset; next-level request
F709 clears it. Do not cap the actual collection counter at twelve.

**T1 — temperature.** E5 initializes to BCD 45. When the ordinary path reaches
FA95 and 81&3F=0, FBC1 decrements it with SED/SEC/SBC; zero sets F1=10.
Delays, state branches and the bear chase can skip that path. Therefore this
is not an unconditional seconds timer. Preserve the returned Z flag used by
FA9D's branch. The primitive's 00→99 underflow is an artificial boundary case,
not a claim that normal play intentionally decrements an already-zero timer.

## Score, reserves, variations and game phases

**S1 — score.** FB95 adds packed decimal into CA→C9→C8 and clears decimal mode
on return. C5 bit 7 inhibits scoring. The block award is 10×min(CB+1,9)
decimal, derived at F5D1–F5DE; scoring plateaus after displayed level 9 without
capping progression. Igloo completion converts sixteen block units followed
by remaining temperature units through the same award. Fish uses delayed
10-point units. Six-digit rollover and live flags must follow the source.

**S2 — extra reserves.** After a low-score-byte carry, updated C9=00 or 50
can award a reserve if CC<09 (FBAD–FBBD). Preserve the actual BCD gate rather
than replacing it with an unchecked mathematical score-difference shortcut.
The five-thousand, cap and six-digit-wrap probes cover important edges.

**V1 — variations.** 80=0/1 are regular one/two-player; 2/3 advanced one/two.
FB3B starts CB/D1 at 00 or 04 respectively. CC starts at 03. In two-player
initialization D2 starts at 04 because first activation of the other record
consumes one reserve; its first playable turn therefore also has three.
FE77 swaps exactly C8–CD and CE–D3 and toggles C7. It does not preserve an
entire actor/row world per player; FB57 resets that shared world for a new turn.

**V2 — life/turn recovery.** F1 bit 5 dispatches F71B–F73A. With reserves
remaining, swap once to a living other record; if its CC is zero, swap back;
decrement the selected CC and reinitialize actors/rows. Single-player uses
that double swap to skip the empty other record. Both CC/D2 zero instead
clear F1 and decrement C6 from 00 to FF, entering the terminal/attract path.
Do not use a single-player emulator terminal shortcut for two-player acceptance.

| Dispatch priority at F6CB onward | Meaning and observable next state |
|---|---|
| E7 positive | Decrement; if result nonnegative, skip state processing for this step |
| C5 not attract and C6 nonzero | Skip gameplay |
| F1 bit 7 | EB animation until 12, then F1=20/E7=70 |
| F1 bit 6 | Consume CD down through FF with six-count delays/awards, then E5 with two-count delays/awards; at E5=0 request F1=08/E7=30 and clear F7 |
| F1 bit 5 | Recover life/alternate player or enter terminal state as above |
| F1 bit 4 | Increment F0 animation until 12, then F1=20/E7=70 |
| F1 bit 3 | Increment CB in active play and call shared initialization; attract bypasses the increment |
| none | Ordinary gameplay; zero horizontal position can first request bit 7 |

The order is observable if multiple bits are set; do not replace BIT's N/V
tests with a differently ordered enum. Water/edge loss and temperature loss
have different animations. E7 initialization delays are state-dependent.

**V3 — progression/presentation.** Active next-level handling increments the
byte CB, including wrap, and resets temperature/igloo/rows. Day/night selection
uses CB bit 2 (four-level groups), independent of scoring plateau. The score
area's special fish graphic is selected at CB>=14 (twenty decimal, displayed
level 21), not by comparing score. Preserve this source condition even though
the manual describes the icon imprecisely in terms of achievement/high score.
Late-level object choices and packed movement derive from source tables and
byte arithmetic; do not impose a new difficulty ceiling or copy Seaquest RNG.

**C1 — Reset/Select/attract.** When the F665 console path is reached, SWCHB
Reset bit 0 is tested before Select bit 1. I1's countdown expiry can instead
take the attract partial reset before reaching this console path in that step.
Reset jumps with X=BF to the partial clear loop: 80–BE survive; BF–FF clear,
then player/row initialization runs. Select increments 80 modulo four,
formats variation sentinels in the score, sets C6=FF and 83=1E. Holding Select
decrements 83 before another selection; release sets 83=0. Difficulty switches
are not used by this path. C5 bit 7 marks attract simulation, inhibits scoring
and gates several resets. Input resets inactivity BF; its counters and original
phase gates must remain, with no invented pause or autoplay mechanics.

The [ALE v0.12.1 adapter](https://github.com/Farama-Foundation/Arcade-Learning-Environment/blob/v0.12.1/src/ale/games/supported/Frostbite.cpp)
offers modes 0/2 and declares terminal from low CC nibble zero plus F1 bit 7.
That is a limited adapter predicate: it cannot certify every original death
path, both-player exhaustion, bonus completion or restart. Acceptance uses
the source state predicates below and a backend supporting both controllers.

## Boundary routes and completion predicates

These are required route designs, **not completed replay evidence**. #7 must
freeze source/backend/initial state, RNG, per-step inputs and collisions, then
bind exact expected traces. Budgets below are chosen test timeouts, not measured
game durations. Every run must report success, unexpected transition, mismatch
or timeout; emulator launch/boot alone is never success.

| ID | Required boundary coverage | Completion predicate and bound in observed source steps |
|---|---|---|
| R01 | All four variations; Select hold/release/wrap; Reset+Select together | Requested variation survives Reset, correct initial level/records and first accepted control; <=1024 |
| R02 | Each jump direction, first-step parity, all diagonals/opposed bits, held direction, mid-air steering, landing | Expected trajectory endpoints, EA returns zero/F6 set and next contact consumed at aligned PCs; <=256 per arc |
| R03 | White/blue landing, simultaneous fire, last-blue reset and cooldown | Sixteen legal activations reach CD=0F with correct score and no duplicate held-landing award; <=30000 |
| R04 | No-block/partial/completed reversal, shore/no-floe, held fire/release/repress, hazard attachment | Only eligible edge toggles one row bit 6; correct CD cost and no other row mutation; <=512 per case |
| R05 | Entry at X=77/78/7F/80 and incomplete door; full bonus conversion | Legal route reaches F1=40, drains CD/E5, requests 08, then incremented CB and initialized active state; <=4096 after entry |
| R06 | Each threat, grounded versus airborne, multiple row contacts, push to sea and lost floe | Exact collision-window/latch/priority trace, expected attachment or immunity, then intended recovery/terminal predicate; <=4096 |
| R07 | Bear onset at CB=02/03, airborne contact, extreme-left refuge and chase | Refuge produces no effective grounded hit throughout a frozen bear sweep; chase preserves original escape/death transitions; <=4096 |
| R08 | Temperature 10/01/00 boundaries, frame gate, delayed/chase states; final-life temperature loss | Correct decrement/skip, F1=10 animation, then life recovery or both-reserves-zero F1=00/C6=FF; <=2048 after injected expiry |
| R09 | Fish segment offset, already-spawned fish after F7=0C, count across death and next level, delayed points | Segment removed once; complete envelope totals 200 with correct per-step score/reserve ordering; <=2048 per collection |
| R10 | 4990→5000, reserve 8/9, 999990 rollover; scoring during transition | Exact BCD bytes/flags at FB95 return and reserve cap; <=256 per primitive, full event separately |
| R11 | Both regular/advanced alternating games; one dead player; both exhausted; restart | Correct C7/record swaps and reserve consumption; terminal only after both records exhausted/resolved, Reset returns playable state; <=30000 |
| R12 | CB 03→04,07→08,13→14,FF→00; plateau and late object/step domains | Correct byte progression, palettes/icon/awards, no unsupported index/flag state; <=4096 per controlled transition |
| R13 | Inactivity/attract and control re-entry; 50/60 Hz target presentation | Same source-step states/input latency at aligned boundaries; no skipped logic/audio event; bounded frozen route supplied by #7/#15 |

For R06/R08/R11, a life animation beginning is not the same as resolved game
over. Inspect both records and the post-recovery dispatcher. For R03/R05,
door visible is not the same as igloo entered or next round ready. Natural play
and controlled injections must be reported separately, with negative controls
that alter collision, carry, order or one coordinate and demonstrably fail.

## Open acceptance gates

- #7: aligned initialization/seed, independent Stella traces, legal reachability,
  NMOS flag confirmation, complete input surfaces and TIA collision geometry
  including refuge, airborne transitions and simultaneous events.
- Native implementation issues: subsystem state/flag equality at the same
  boundaries, with all required source steps executed on unexpanded MSX1.
- #15/#16: worst-case timing, complete-game routes, manual visual/listening and
  physical MSX evidence. No CPU fixture can satisfy those gates by inference.

The 101 CPU probes and synthetic utility tests are current research evidence.
No MSX gameplay ROM is delivered here. Every future useful diagnostic or
playable ROM must receive its own versioned release with the exact tested ROM,
hash/commit, known limitations, next work and concrete human test instructions.
