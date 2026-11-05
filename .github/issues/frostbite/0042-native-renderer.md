<!-- AB ready-picture delivery from v0.0.15, 2026-11-05 -->
Published [v0.0.16](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.16-ready-presentation-diagnostic)
from clean source `a9cf5ff3ea802b79a0e328e0a9de844e9749f8d3`, ROM SHA-256
`9d2ee2926bc8de7fd0d22b05e7ad334e76078141bfde997720adfb62414cc77b`.
Fresh WORLD profiling and per-arc landing analysis led to current-picture enemy
eligibility reuse and first-safe-VBlank admission of complete coherent scenes.
NTSC active cadence improves 21.46 to 25.45 pictures/s (+18.60%), grounded
landings 9/26 to 15/26, endpoints 20/26 to 21/26, and missed pose runs 2 to zero.
P95/maximum NTSC gaps remain 66.75/83.44 ms. Original clock, mechanics, graphics,
input and ordered audio are preserved in the bounded checks.

**PAL limitation:** throughput improves 20.20 to 22.92, but grounded landings
fall 13/26 to 12/26, endpoints 21/26 to 19/26, and P95 gaps rise 59.91 to79.71ms.
First post-landing ages at source1732/1762 rise3 to7 and2 to6steps. No general
PAL landing improvement, stable30FPS or original fluidity acceptance is claimed.
Whole foreground mean is70,935 versus80,142cycles over different picture
populations; this is not paired CPU savings. Long tails remain the next target.

565 host tests,4089source/density/header scenes,4507CPU/all-RAM checkpoints,
2497coherent pictures,18realIRQ boundaries plus rejectedAF2fault,10560clipping
cases and2115ordered-audio intervals pass. Exact-source CI and independent clean
rebuild verify151sources; final natural runs reproduce all5measurement buffers.
All6published assets were downloaded and byte-verified; tag/source identity is
exact. AB workbook preserves27AA sheets/767714cells. See `docs/ready-presentation.md`,
`references/ready-presentation-result.json` and `references/ready-presentation-delivery.json`.

Status: **In review** for diagnostic owner tests. PR43 remains draft/stacked on41.
Next: WORLD/floe NAME costs, long preparation tails and PAL landing sampling.
The NAME residency idea is only an offline upper bound, not a measured ROM gain.
Keep42/39/15/16open. Root/current issue chat remains sole checkout owner; previous
versions are preserved. No owner-fluidity, all-level or physical acceptance.

<!-- Historical AA floe transaction delivery, 2026-11-05 -->
Published [v0.0.15](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.15-floe-transactions-diagnostic)
from clean source `e5dd710a910272150709f7b806fb3c62403fa009`, ROM SHA-256
`d28c68590a27004d6624af3d1ecb9d80dc422ed3f4f4241caed2df278d1a5db0`.
The owner reports a large improvement in v0.0.14 and authorized the next
playfield optimization. Fresh passive profiling identified floes as the largest
average WORLD cost. Native floe setup/publication and an exact resident color
lookup raise active NTSC/PAL presentation from 20.11/19.07 to 21.46/20.20
pictures/s; complete foreground falls 86,984 to 80,142 cycles (7.87%).

NTSC longest gap falls 100.10 to 83.44 ms; P95 remains four fields. Jump states
shown increase 251/390 to 266/390, but grounded landings regress 14/26 to 9/26.
Endpoint Y improves 19/26 to 20/26. No original simulation state/contact rule is
removed; graphics and mechanics match the bounded oracles. **Original fluidity
and stable 30 FPS remain open.** The NAME-layout experiment was rejected before
ROM construction because its proposed allocation did not fit.

557 host tests, 4,089 source/density/header scenes, 4,507 CPU/all-RAM checkpoints,
1,829 coherent pictures, 18 IRQ boundaries plus negative control, 10,560 clipping
cases and 2,115 ordered-audio intervals pass. Exact-source CI, independent clean
rebuild of all 147 sources, and final NTSC/PAL raw-buffer parity pass. All six
published assets were downloaded and byte-verified; remote tag targets the exact
source. AA workbook preserves all 25 Z tabs / 765,304 cells. See
[the report](https://github.com/sandersouza/msxgp-frostbite/blob/e5dd710a910272150709f7b806fb3c62403fa009/docs/floe-transactions.md),
`references/floe-transactions-result.json` and `references/floe-transactions-delivery.json`.

Status: **In review** for diagnostic owner tests. PR #43 remains draft/stacked
on #41. Continue WORLD preparation and long-gap costs while tracking landings.
No owner-fluidity, all-level or physical acceptance; keep #42/#39/#15/#16 open.
Root/current issue chat remains sole checkout owner. Prior versions are preserved.

<!-- Historical Z delivery checkpoint, 2026-11-05 -->
Published [v0.0.14](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.14-core-cadence-diagnostic)
from source `2c1891635553e07b6fd096a58cc0e34905acd568`; ROM SHA-256
`e59d719e9169a4a73300eb9099008d1a92c77a247b205c78d6961015d16886c5`.
Exact source-core summaries plus direct header/player/static work improve
active NTSC/PAL pictures from 18.22/17.22 to 20.11/19.07 per second.
NTSC gap P95 falls 83.44 to 66.79 ms; jump updates shown rise 229/390 to
251/390. Whole foreground falls 95,808 to 86,984 cycles; complete active ISR
falls 23,689 to 21,933. The original source clock and tested CPU/RAM, graphics,
input and ordered PSG contracts are preserved. **Original fluidity remains open.**

557 host tests, all natural/directed/density/IRQ/audio/clipping gates and both
exact-source CI runs pass. Independent review and clean rebuild reproduce the
measured bytes; final NTSC/PAL reruns reproduce all five measurement buffers.
All six downloaded release assets match the tested package. Workbook Z preserves
all 23 Y tabs. See [the report](https://github.com/sandersouza/msxgp-frostbite/blob/2c1891635553e07b6fd096a58cc0e34905acd568/docs/core-cadence.md),
`references/core-cadence-result.json` and `references/core-cadence-delivery.json`.
Status: **In review** for owner diagnostic tests; PR43 stays draft/stacked on41.
Next: remaining world/preparation cost and long gaps. No owner, all-level or
physical acceptance; keep this issue and39/15/16 open.

<!-- Historical Y investigation after X, superseded by Z delivery above -->
The owner reports noticeable improvement in v0.0.13, but gameplay remains far
from smooth. Motion acceptance remains open. Status: **In progress**; preserve
X as the public control. Follow-up measurements rejected three isolated changes
as standalone delivery: static SAT +1.2%, player selector no cadence gain, direct
header +3.2% with effectively unchanged P95. At that checkpoint no combination
or new release was claimed. Judge the next candidate by complete-picture gaps and visible
jump trajectory coverage, not average FPS alone.

Passive profiles preserve all five natural X buffers. Two NTSC fields leave
about 72,094 cycles outside IRQ service, against 95,808 foreground cycles; the
mean deficit is 23,714. The translated core excluding input/audio is the largest
measured source component at 14,211 cycles per active step. Next work profiles
its executed blocks before proof-backed lowering, alongside native floe work.
Original mechanics, input/audio sampling and coherent snapshots stay required.

<!-- Native lane X delivery checkpoint, 2026-11-05 -->
Published [v0.0.13](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.13-native-lanes-cadence-diagnostic) measures18.2214NTSC/17.2158PAL active pictures/s, compared
with W10.6131/10.5441. Whole foreground falls182,896→95,808cycles; NTSC gapP95
falls133.47→83.44ms. Jump-state coverage rises132/390→229/390, still incomplete.
Original-speed/smooth-motion acceptance remains OPEN. See
[the native lane report](https://github.com/sandersouza/msxgp-frostbite/blob/2318fe1b5b96e528a1864d43ebca093dd60194ba/docs/native-lanes-cadence.md) for exact scope,
reproduction, guards and pending owner tests. Exact-source push/PR CI passed;
all six release assets were downloaded and byte-verified. Source commit:
`2318fe1b5b96e528a1864d43ebca093dd60194ba`. Publication status was In review; performance and
owner acceptance remain open, with no automatic close or successor handoff.

# Replace generic rendering with an MSX1-native residency and band pipeline

GitHub: https://github.com/sandersouza/msxgp-frostbite/issues/42

Implementation child of #39. Owner approved architectural replacement and
resuming GitHub. Original Atari 2600 mechanics remain authoritative; preserve
graphics, colors, actors, viewport, input order and audio event timing. The Atari
400/800 fan port and Seaquest are implementation references, not gameplay specs.

## Movement fluidity rejected by owner — 2026-11-05

The owner reports that the third diagnostic still presents player movement as
a slideshow, despite responsive controls. Status is **In progress**. Original
presentation cadence and owner acceptance remain unmet; another small mean-FPS
improvement is not sufficient evidence of a fix.

The immutable W control presents active pictures at 10.6131 fps NTSC, with
133.47 ms observed-order p95 and 150.19 ms maximum gaps. Of 84 contiguous active
animation-pose runs, 12 are never presented; ten last four source steps. These
pose runs describe animation states, not every individual position.

Current work measures whole-frame tails and source-step/pose coverage while
replacing generic world traversal, player construction and fixed HUD work.
An internal combined prototype reaches 16.2723 fps but still has 100.10 ms p95
gaps and five unpresented four-step pose runs. It is **not** a fluidity solution
or a new human-test release. Investigate those remaining worst cases before
delivery. Mechanics, input/audio order, colors, viewport and coherent snapshots
remain required; asynchronous player-only motion over an older world has not
been adopted. W and every prior sealed artifact remain unchanged.

## Player palette and selective header diagnostic — 2026-11-05

Published [v0.0.12](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.12-player-palette-header-diagnostic).
Source `48f570ea2b4c3894b2a77cb6555c226fe0b11863`; ROM
`98904b6bb592f78964158d154545764eda0e986c9c979196d60e9a7ed03f30b4`.
Normal player uses yellow hat, cream face/legs and gray torso; death colors remain
unchanged. Header updates rebuild only affected columns. Mechanics/input/PSG
remain unchanged in the complete controlled CPU/all-RAM comparison.

Active picture rates10.3356->10.6131 NTSC (+2.69%) and10.2829->10.5441 PAL (+2.54%).
Complete foreground preparation -2.85%; header -15.07%. Long active gaps remain
~133ms p95/~150ms maximum: original-speed presentation and owner cadence
acceptance are still open. Fast input does not establish smooth rendering.

553 host tests,4089 source/density/directed scenes,4507 CPU/all-RAM checkpoints,
1401 coherent pictures,18 directed IRQ boundaries and AF2 negative control pass.
Independent review found no blockers; blank transitions and oracle fingerprint
follow-ups passed. Source48f570e push/PR CI pass. See release notes and
references/header-palette-result.json. In review for diagnostic/human checks;
do not close this issue or parents from these bounded proofs.

## Previous world transaction diagnostic — 2026-11-05

Published [v0.0.11](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.11-world-transactions-diagnostic), exact source `a43e2f1b265ef956ee154e82a198a17f9831a220`, ROM `fbf81a5eafa536f95497be22c787812046cf59a38eb962ee28230b3fc8f9ec99`.

Final ice NAME templates, compact enemy occupancy and register-held NAME cursors reduce NTSC active world foreground cost12.19% and full foreground preparation6.48%. Active pictures rise9.7979→10.3356NTSC (+5.49%) and9.6986→10.2829PAL (+6.02%). Source logic remains59.92steps/s; all graphics/colors/actors/player/mask and mechanics are retained. The gain is modest; original presentation cadence is still unmet.

548host tests and both exact-source CI runs pass. The exact final ROM passes4035source/density scenes,4507native CPU/all128RAM checkpoints,1379coherent pictures,18directed IRQ boundaries, an AF2 negative control and the forced-geometry-failure stack regression. Independent review checked2560NAME contexts/8448occupancy entries and complete patch replay; its one Important error-path finding was fixed in one correction pass.

See `docs/world-transactions-diagnostic.md`, `references/world-transactions-result.json`, and the release human tests. Status moves to In review for this diagnostic/human comparison; full issue acceptance and #39/#15/#16 remain open. Owner/audio/controllers/physical acceptance is pending. Prior T and earlier controls are preserved.

## Measured checkpoint — 2026-11-04

### Owner cadence feedback

After0.0.10delivery the owner reports excessive speed, cadence unlike the original
and apparent picture skipping. Gameplay cadence is not accepted;42returns to
In progress. Controlled replay confirms2..9original states between active
pictures (mean6.043), with normal29-frame jumps shown in only4..5pictures.
An original-frame-counter audit and2253CPU/allRAM recheck found one source update
per original frame after startup, not a doubled update rate. Real acceleration
has not been reproduced in the owner's setup. Do not halve simulation as an
unmeasured workaround. New disjoint profiling puts world preparation at100566
of201312mean foreground cycles per active snapshot. See
docs/fixed-clock-cadence-feedback.md and references/fixed-clock-cadence-feedback.json.
No ROM bytes or published attachments changed in this investigation.

### Fixed-clock diagnostic delivery

The public F→I/J/K/L/M/contact14/P/Q chain now reproduces sealed Q exactly.
The T independent-clock diagnostic runs59.92275NTSC/59.92467PALlogical steps/s
in input-only original routes, with4507CPU/allRAM and1355coherent-picture checks.
Active drawing remains9.79790/9.69859fps: original-speed presentation is unmet.
It is a diagnostic, not the final performance solution. All original colors,
actors, player and mask remain. R's marginal header/igloo path is preserved and
rejected. See docs/fixed-clock-diagnostic.md and the0.0.10human tests. Do not close
#42/#39/#15/#16 from the source-clock result.

[v0.0.10](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.10-fixed-clock-diagnostic)
is published from clean854dcf462b56274f60f1f0cf978bc487d124e57a, exact ROM
`29b4588b62d4b44a88401c691512d415b26bdaf559198d889730ee2b49763b1e`.
All four attachments were downloaded again and verified byte-identical.545host
tests, both exact-source CI runs and all natural/directed gates pass. The T
workbook preserves all Q cells/features and clearly separates the two clocks.
Issue status is In review for diagnostic/human feedback; original-time drawing
and the implementation issue's full DoD remain open. See public fixed-clock
validation/publication receipts and docs/handoffs/issue-42.md.

Independent review found no demonstrated kernel blocker and required directed
hardware-IRQ boundary alignment in addition to natural replay. The new harness
checks nine mapper/VDP/stream/snapshot boundaries, complete main/alternate/index
registers, SP and bank after RETI; an AF2 mutation must fail its oracle. Manual
listening, alternating controllers, unseen levels and physical MSX remain pending.

### Preserved Q measurements

Shared residency O-B is correct but rejected(-6.91%/-6.90%). Prepared ice P-C
improves4.87%/5.35% against M-C. Eager enemy bands Q-C regress against P-C;
lazy-key bands Q-E improve2.85% NTSC /3.10% PAL over P-C, or7.85%/8.62% over M-C.
Active source cadence33.6350 /35.2938 updates/s remains below the original goal.
NTSC whole-frame mean102843 cycles, P95 219663; complete-route maximum484270.

Q validation:209088 actual Z80 actor cases,2115 original scenes,1920 dense
synthetic scenes,4139 source-model images,4508 source CPU/all-RAM checkpoints.
The complete host suite passes531 tests. Independent review found an evidence
binding gap; corrected reporters reject mixed-ROM proofs and altered audited
buffers. Fresh v2 owner receipts and bound reports preserve identical timings.

The O/P and Q workbooks each contain8278 paired observations and424 cost rows;
historical M and all previous artifacts are preserved. No manual/listening/
physical or complete-game acceptance is claimed. Q-E remains an internal test;
At that checkpoint canonical source integration and a useful human ROM/release
were pending; the current clock diagnostic above supersedes that source gap.

Next: redesign the wider prepare pipeline and its tails. Even zero world work
would leave66928 mean NTSC cycles, above59736. Further enemy-only changes cannot
solve the complete-frame target. See docs/direct-enemy-progress.md and
docs/issue-42-review.md. Keep draft PR43 stacked on41; #39/#42 remain open.

## Goal and first implementation boundary

Build an MSX1-oriented rendering pipeline with a credible complete-frame budget.
Start with shared ice-pattern residency across NAME generations and bounded
per-band NAME preparation. Keep displayed references pinned, including both
colors and vertical phases. Rework physical ownership/key recovery and its
independent checker together; do not weaken active-display protection.

Measure allocation, metadata, lookup, composition, IO and scheduling together.
Replace further generic stages when the whole-frame ledger requires it. The
56-slot host model avoids about 60% of semantic misses; this is a hypothesis
for implementation, not an FPS prediction. N-B traversal alone gained only
1.49% NTSC / 1.99% PAL and is retained as internal evidence.

## Dependencies / Definition of Ready

#39 research and sealed M-C control are available. Read
`docs/native-band-feasibility.md`, its design/plan, and the dedicated handoff.
Start in a forked `Frostbite — ISSUE #42` chat with exclusive checkout
ownership and branch `codex/feat/42-native-renderer`.
No next-issue implementation in the predecessor chat.

## Acceptance / Definition of Done

- Standard-speed MSX1, 64 KiB RAM, 16 KiB VRAM, TMS9918 and built-in PSG only.
- Original CPU/state/input/collision/audio contracts remain equivalent; full
  physical pixels, colors and actors match the sealed control on all tested
  scenes. No frame skipping or reduced simulation rate used to claim success.
- Independent VRAM allocation/visible-reference checks pass, including overlap,
  wrap, phases, blue/white rows, transitions and dense four-lane cases.
- Paired active NTSC/PAL whole-frame mean/P95/max and source cadence identify
  actual gains and remaining shortfall. Update the performance workbook and
  record exact ROM/source/tool/input hashes. Do not sum inclusive helper costs.
- Independent review and focused PR delivery are integrated before closing.
  If original cadence is not achieved, explicitly retain #39's unmet goal;
  #15/#16 remain independent final timing/full-game/hardware qualification.
- Preserve all prior versions. Publish a useful human-test candidate as a new
  prerelease with exact ROM, SHA/source, current limits, next work and concrete
  setup/action/expected-result tests. Internal rejected experiments are archived.

Player-as-tiles remains on hold. Any material visual compromise needs a concrete
owner decision. Do not assume a complete permanent atlas fits VRAM. Automated,
manual-emulator and physical-hardware evidence remain separate.

## Tracking

MSX Game Ports project #7. Type: Task (repository native types unavailable).
Priority P1; size XL; estimate 40 hours, exploratory engineering and validation,
not a deadline. No new labels, milestones or shared project settings required.
