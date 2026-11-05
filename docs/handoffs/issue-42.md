# Issue #42 — native renderer implementation handoff

Issue: https://github.com/sandersouza/msxgp-frostbite/issues/42
Parent: #39, original-speed objective still open. P1 / XL / exploratory 40h.
Owner approved replacing the architecture and resuming GitHub. Continue
autonomously; routine implementation does not require another approval.

## Ownership and source

Current exclusive owner is the issue42 fork/thread
`01a1a457-0a26-77c0-b7c7-ddaa7a36a5eb`, branch
`codex/feat/42-native-renderer`. Draft PR43 is stacked on PR41. The following
starting instructions describe the original transfer; do not create a duplicate
chat/branch or resume predecessor edits.

## Z core/header cadence delivery — 2026-11-05

Published [v0.0.14](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.14-core-cadence-diagnostic)
from clean runtime source `2c1891635553e07b6fd096a58cc0e34905acd568`, ROM SHA-256
`e59d719e9169a4a73300eb9099008d1a92c77a247b205c78d6961015d16886c5`.
Maintained builder: `scripts/build_core_cadence.py`; final build/evidence under
`outputs/presentation/core-cadence-z/`. Read [the report](../core-cadence.md),
`references/core-cadence-result.json` and `references/core-cadence-delivery.json`.

Z combines exact core effect/ice/actor summaries with direct header columns,
mask-first player selection and cached static SAT work. NTSC/PAL active
cadence is 20.1127/19.0708 pictures/s versus X18.2214/17.2158. NTSC P95 gap
falls 83.44 to 66.79 ms; jumps show251/390 updates versus229/390 and14/26
grounded landings versus10/26. It remains below stable30fps/original fluidity.
Mean foreground86,984cycles and complete active ISR21,933 leave a two-field
mean deficit11,378; world37,063cycles remains the largest foreground component.
Changed snapshot populations prohibit adding isolated or inclusive savings.

All557 host tests and exact-source push42106542332/PR42106551981 CI pass.
Source/density/header4089scenes,4507CPU/allRAM and1785coherent pictures,
18IRQboundaries+AF2negative,10560clipping and2115ordered-audio intervals
(3499source/2472PSGwrites) pass. Clean final NTSC/PAL runs reproduce all five
qualified measurement buffers. Independent review/rebuild found no blocker;
all145source hashes match the source commit. All six downloaded release assets
are identical; the remote tag points to that exact source commit.

Workbook Z preserves all23Ytabs/762824cells, with two new cadence/cost tabs:
`outputs/01a1a457-0a26-77c0-b7c7-ddaa7a36a5eb-Z/Frostbite-performance-budget-Z.xlsx`,
SHA256 `f8cb7719502b1af6a882e38162fbd12d8de54fb3bcd8e17572fbd8d9c1dc9043`.
17formula checks, two mutation/restore tests, raw aggregate and eight-region
visual audits pass; native Excel was not exercised. Workbook is the sealed
pre-publication measurement snapshot. All318X/316W sealed files remain unchanged.

Important maintenance boundary: generic typed-header kinds16..18 are retired;
only the direct-header producer may publish that metadata. Re-audit before
introducing any new generic requester. Old core internal labels in replaced
spans are retired; public source-return CPU/V/allRAM remains strict. No new RAM.

Issue42 is **In review** for this diagnostic/owner test. PR43 remains draft,
stacked on41; no merge/close or successor handoff. Root/current chat remains
sole checkout owner. Next: continue remaining world/preparation and long-gap
work, using Z as the new measured control and preserving X/Y. Owner motion,
manual audio/controllers, all levels and physical hardware acceptance remain
pending; keep42/39/15/16open. No agent owns pending tracked source.

## Historical Y bounded investigation — 2026-11-05

Owner feedback on X is partial improvement, not acceptance. Issue #42 remains
**In progress**. Root owns tracked files; no new runtime is selected or released.
Read [the investigation](../cadence-y-investigation.md) and its bound reference.

Three isolated candidates remain local: static SAT gains 1.2% with unchanged
P95; the player selector saves cold-case work but no natural cadence; direct
header halves header cost but gains only 3.2% overall, leaving P95 unchanged
and some landing coverage worse. No combination is measured. Preserve the
sealed world/source/header/player evidence and prior X/W artifacts.

The new passive source profile is byte-identical to X. Per active NTSC source
step, core excluding input/audio costs 14,211 cycles, visible/contact work 4,764,
and complete ISR 23,689. Two fields leave about 72,094 cycles versus 95,808 for
rendering; the 23,714-cycle deficit is arithmetic, not a promised speedup.
Next: profile executed core_F476 blocks before lowering the dominant patterns;
retain source CPU/all-RAM, audio order, input sampling points and coherent scenes.

Header integration caveat: generic typed-header callers remain dormant; preserve
the sole direct-header producer invariant or relocate its code. Full PAL/matrix/
density/IRQ qualification and a combined whole-route benefit remain required
before selecting that component for a release. No agent owns pending source.

Workbook research appendices preserve all 21 X sheets and 761,109 cells:
`outputs/01a1a457-0a26-77c0-b7c7-ddaa7a36a5eb-Y-research/Frostbite-performance-budget-Y-research.xlsx`,
SHA256 `356167edc58a214cd08a6473fa986cddea8f29966e0ee81edb71175174d136a1`.
Two new sheets record isolated candidates and disjoint costs. Formula/input-change,
raw-aggregate and saved-file preservation audits pass; native Excel was not tested.

## X native lane diagnostic — 2026-11-05

Owner playtest follow-up: v0.0.13 has noticeable improvement, but gameplay is
still far from smooth. This is partial positive feedback, not motion acceptance.
Issue42 returns to **In progress**. Preserve X as the measured/public control;
the next investigation separates world lane costs and header spikes before
selecting another candidate. Root retains exclusive tracked-file ownership.

Owner slideshow feedback remains the acceptance priority. X is a substantial
measured diagnostic improvement, not a claim that original fluidity is solved.
Selected ROM: `b92478f778a57c70e152497e92102637879248fefac7a9161a9f196928a2c0dc`.
Source/reproduction and complete limitations: [native lane report](../native-lanes-cadence.md).
NTSC/PAL active cadence is18.2214/17.2158 pictures/s; NTSC mean gap54.88ms,
p9583.44ms/max116.82ms; complete foreground95,808cycles. Of390 original jump
updates,229 are presented vs132 inW; this remains below complete trajectory coverage.
The source clock/controls and coherent pixels remain exact in the bounded route.

Root owns all tracked changes; rejected prototype artifacts are ignored and
preserved. HUD sprite variants regressed cadence and are excluded. All full
source/density/directed, NTSC/expandedPAL, IRQ and clipping gates passed; independent
review/rebuild found no blocker. Published [v0.0.13](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.13-native-lanes-cadence-diagnostic) from runtime/source commit
`2318fe1b5b96e528a1864d43ebca093dd60194ba`. Both exact-source push/PR CI passed.
All six published assets were downloaded and matched locally; the remote tag
resolves to that source commit. Workbook X SHA256 is
`a58b1f9f081986f0a351c927e39d982c6bc4955fef17e63bd077e2497a479059`;
all14 W sheets are preserved. The316-file W seal and24-file passive-profile seal
remain unchanged. See `references/native-lanes-delivery.json` for exact downloads.
At publication Issue42 was In review for owner feedback and further performance
work; PR43 remains a draft stacked on PR41. No successor owns the shared checkout.
The next action is to reduce world cost and header/igloo spikes using the measured
long-gap cases; do not infer owner or physical acceptance from these checks.

## Earlier W investigation checkpoint — 2026-11-05

The owner rejected the movement fluidity after W. Issue42 is back **In progress**;
do not describe fast input or small average frame-rate gains as smooth animation.
The current internal combined experiment improves active NTSC pictures from
10.6131 to 16.2723 fps, but its 100.10 ms p95 and remaining unpresented four-step
poses are still unacceptable as a claimed fix. No new release has been published
in this investigation. W remains the immutable public control.

Private working checkpoint: `.superpowers/sdd/issue-42-fluidity-x-current.md`.
Root owns tracked changes; component agents write separate ignored prototype
directories only. Preserve exact ROM/source hashes and report whole-frame tails,
source-step gaps and pose-run coverage alongside mean costs. Final candidate,
complete-source inventory, expanded-slot PAL, density/boundary checks, workbook
and independent review are still pending. Do not close this issue or its parents.

## Latest world transaction diagnostic — 2026-11-05

### W palette/header follow-up delivered — 2026-11-05

Published [v0.0.12](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.12-player-palette-header-diagnostic),
source `48f570ea2b4c3894b2a77cb6555c226fe0b11863`, ROM SHA-256
`98904b6bb592f78964158d154545764eda0e986c9c979196d60e9a7ed03f30b4`.
This supersedes V as the current human diagnostic, without changing its sealed
control. Same issue42 chat/branch owns the checkout; PR43 remains draft/stacked.

Normal player EB=F0=0: hat Atari24->TMS10, face36/legs16->11, torso06 remains14.
Both ordinary and shore paths use a selected immutable color table. Terminal
animation keeps its original palette/four-plane bound. Header identities occupy
E840..E861, mask/pointer/palette-page scratch ends E866, and initialized RAM code
ends EE00. Per-page raw selectors, mapped colors and level>=20 determine which
columns need original packing/construction. Unchanged columns restore fixed NAME;
validity follows all three successful bands. No logic/input/PSG changes.

Active pictures: 10.61315 NTSC (+2.69% V), 10.54413 PAL (+2.54%). Full foreground
182896 cycles (-2.85%); header -15.07%. Active p95 ~133ms and maximum ~150ms remain;
owner cadence acceptance is still missing. No smooth30/60fps claim. First W-A
was correct but only +2.01%; W-B reduces repeated per-row palette selection.

553 host tests; 4089 source/density/directed scenes; 4507 CPU/all-RAM points;
1401 coherent pictures; 18 directed IRQ boundaries and AF2 negative control pass.
Source48f570e push42039267698/PR42039275961 CI pass. Independent review of
42a9b15..d2cad7c found no blockers; its blank-coverage and producer-fingerprint
recommendations were addressed in48f570e. Final NTSC/PAL raw buffers equal the
d2 clean/profile buffers exactly; all130 build source files match release git blobs.

Artifacts: outputs/presentation/header-palette-w/ (build-final, ntsc-final,
pal-final, matrix-final, density-clean, transitions, irq-ntsc/irq-pal, negative,
release-0.0.12). Disjoint profile is sealed separately under
outputs/presentation/header-palette-w-research/final-d2cad7c/. Public compact
receipt: references/header-palette-result.json. Release notes contain precise
human palette/jump/header/death checks. Current delivery retains human review;
do not close42/39/15/16 or merge from these bounded diagnostics alone.

W workbook: outputs/01a1a457-0a26-77c0-b7c7-ddaa7a36a5eb-W/Frostbite-performance-budget-W.xlsx,
SHA-25606737821c5a69b87da0994cb33adb40be9c9cb409a1ef828e2bebcdeccc61d5d.
All10 V tabs/434766 cells and native features preserved;180 aggregates and
stage comparisons independently checked, zero formula errors. Recalculation/
restore and rendered previews pass; native Excel was not exercised. Public
references/header-palette-delivery.json binds workbook/audit and downloaded
release identities. Four downloaded assets equal the tested local files; remote
tag points to48f570e. V and older controls remain untouched.

### Owner playtest feedback — 2026-11-05, after publication

The owner reports fast control response but continued excessive perceived speed,
skipped jump poses and insufficient visual continuity. This is not cadence or
gameplay acceptance. The exact loaded binary and emulator settings were not
independently observed during this playtest. The existing controlled V result
still measures only 10.3356/10.2829 active pictures per second (NTSC/PAL);
source-clock equivalence does not establish perceived motion quality.

The supplied character reference calls for pastel skin on head/legs, gray body
and a pastel yellow hat. The current general palette conversion needs review:
the measured Atari colors 0x24=(162,98,33) and 0x36=(198,108,58) both map to TMS
color6=(212,82,77); 0x16 maps to color10 and 0x06 to color14. These source codes
occur in the original player color tables at FC39/FC3A. A same-mapper pixel
equivalence check preserves this conversion but cannot establish that its color
choices match the owner's visual reference. The screenshot's source palette has
not been calibrated against the retained ALE palette, so do not assign every
body part a replacement code solely from this table inspection.

Next acceptance work must distinguish palette quality, actual jump/event
durations and visible picture spacing. Preserve responsive original input and
the sealed V control. Review player-specific color choices across poses and
day/night/death states; improve presentation continuity without an arbitrary
logic slowdown. This feedback inspection changes no ROM or published evidence.

The latest selected ROM is [v0.0.11](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.11-world-transactions-diagnostic), built from clean `a43e2f1b265ef956ee154e82a198a17f9831a220`, SHA-256 `fbf81a5eafa536f95497be22c787812046cf59a38eb962ee28230b3fc8f9ec99`. Publication documentation follows that source commit. No other writer owns pending source files. This dedicated issue42 chat/branch and stacked draft PR43 remain the owner; do not start a duplicate.

Read docs/world-transactions-diagnostic.md and references/world-transactions-result.json. V compiles final ice names and compact enemy occupancy in certified empty contact tails, with the original full-geometry fusion fallback. RAM image688bytes; E834/E835 scratch remains in Q region. Source IRQ/PSG/player/mask unchanged. Active picture rates10.3356NTSC/10.2829PAL, gains5.49%/6.02% versus T. World foreground−12.19%, complete foreground−6.48%; original presentation cadence remains unmet.

Final build/proofs: outputs/presentation/world-transactions-v/build-final, ntsc-final/pal-final, matrix-final/density-final, irq-final-ntsc/irq-final-pal, negative-final/fault-final.4507CPU/allRAM,1379pictures,4035scenes,18directed IRQ boundaries pass; zero late VBlanks.548host tests and push/PR CI at a43e2f1 pass. Independent review found one Important stack-error path; forced-carry red/green proof verifies its correction. Review scope does not grant physical/manual/audio/all-level acceptance.

Final passive disjoint stage profile: outputs/presentation/world-cost-v/final-a43e2f1/. Full NTSC2252step route,177active snapshots versus T168; do not treat them as same-frame microbenchmarks. All five raw buffers and phases are identical to the pre-fix valid-path control. Previous sealed T/R/Q/P/O/M remain immutable.

The diagnostic awaits human A/B testing against0.0.10at standard100%MSX1 speed. Issue42is In review for delivery/human checks, not Done. Next work should reduce the remaining whole-world transaction cost and long gaps, then HUD/igloo/player work, using the complete fixed-clock profile. Do not halve source logic or claim smooth30/60fps. Existing original-speed target, owner too-fast observation and #39/#15/#16 acceptance stay open.

Workbook: outputs/01a1a457-0a26-77c0-b7c7-ddaa7a36a5eb-V/Frostbite-performance-budget-V.xlsx,
SHA-25658a48897b35e1e1bf07382d7a30373f75667a883491355f500eeaa3c88e588bc.
All six T tabs/296476cells, formulas/styles/features and chart preserved.180independent
aggregates and9stage comparisons pass, zero formula errors, rendered review done;
native Excel not exercised. Delivery receipt binds workbook/audit hashes. Four release
attachments downloaded again and byte-identical, remote tag matches source commit.

## Current clock diagnostic checkpoint

Owner feedback supersedes diagnostic-review status: perceived excessive speed
and skipped pictures.42is now In progress; no cadence acceptance. Read
docs/fixed-clock-cadence-feedback.md and its bound reference. Original counters
confirm one update/frame after startup; active pictures skip2..9states(mean6.043).
Actual owner emulator speed/binary hash remain unverified. World preparation is
100566of201312mean foreground cycles per active snapshot in the new clocked
pipeline. Read-only replay/instrumentation stays under outputs/presentation/cadence-u/;
all original measurement buffers remain byte-identical. ROM0.0.10is unchanged.
Next: world/preparation architecture and regular presentation, not an arbitrary
simulation slowdown. The old Q ledger is not the clocked renderer's cost ledger.

Published [v0.0.10-fixed-clock-diagnostic](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.10-fixed-clock-diagnostic)
from clean source `854dcf462b56274f60f1f0cf978bc487d124e57a`. Four exact assets
were downloaded again and verified. Public receipts:
references/fixed-clock-{result,delivery}.json. PR43 remains draft/stacked on41;
issue42 is In review in project7 for the diagnostic/human checks, not Done.
The tracking helper's old catalog excludes42; its targeted dry-run made no
writes. Status was changed through the verified existing item/Status IDs with
gh and read back; P1/XL/40h and unrelated items were preserved.

Public F→I/J/K/L/M/contact14/P/Q producers reproduce sealed Q byte-for-byte.
R's native header/igloo/player-way path is correct but marginal and rejected
as a human candidate. T separates the original scheduler/native/input/PSG clock
from coherent full-picture preparation. Read docs/fixed-clock-diagnostic.md and
the0.0.10human tests first. Selected ROM SHA
`29b4588b62d4b44a88401c691512d415b26bdaf559198d889730ee2b49763b1e`.

Measured source59.92275NTSC/59.92467PALsteps/s; active pictures9.79790/9.69859fps.
Do not call this smooth/original-speed graphics or close42/39/15/16. Default
original sprites/player/mask, pixels and mechanics remain protected. Independent
review requested real IRQ boundary alignment; the added harness tests nine
mapper/address/stream/snapshot boundaries and actual register/bank/VRAM return
invariants. F3/F4 mixed-pixel hypothesis was retracted; polling moved to the
prepare boundary as optional cleanup. Source F1/F2 input is unchanged.

Local artifacts: outputs/presentation/fixed-clock-t/. Preserve all previous
immutable controls and trial failures. Workbook continuation in
outputs/01a1a457-0a26-77c0-b7c7-ddaa7a36a5eb-T preserves all Q cells/features.
Current exclusive checkout owner remains this issue42chat/branch. Next work:
reduce preparation/cache replacement tails across several source ticks and
measure active complete-picture cadence separately from logical-step cadence.
Manual audio, alternating controls and physical acceptance remain pending.

Fresh clean-source measurements: ntsc-clean/pal-clean; directed gates:
boundaries-clean-ntsc/boundaries-clean-pal; negative-clean; component scenes:
matrix-d/density-d. The old natural D buffers and clean-source buffers are all
byte-identical, so the T workbook's exact measured data remain valid. Source
clock/visual timing are distinct. T workbook SHA
`07fc8187d9c2a8f2e224ebde65495b49177d21d4484c42d61dedfa020a3220b3`.
The final kernel is384bytes; observed stack64NTSC/62PAL of128bytes. Header/igloo
R is not selected. No further source changes belong to the released854dcf4tag.

## Earlier Q checkpoint

Latest implementation commit before review correction:1c25578. O-B rejected,
P-C correct internal packet baseline, Q-C rejected versus P, Q-E lazy actor bands
gain2.85% NTSC /3.10% PAL over P. Q-E ROM SHA
`2654da3abdb2fc2624f6485a9104327447e0493f64a864feb56b41212dc5ada9`.
Active source cadence33.6350 /35.2938 updates/s; original speed remains unmet.
Read docs/direct-enemy-progress.md and docs/issue-42-review.md first for current
evidence/representation and review fix. Source canonical integration and useful
human-ROM delivery remain pending; do not call inherited commits complete source.

Local Q evidence is under outputs/presentation/direct-enemy-q. Use bound reports
and v2 physical receipts.209088 native cases,2115 source scenes,1920 density
scenes,4139 original images and4508 CPU/all-RAM points pass;531 host tests pass.
The Q workbook is under outputs/01a1a457-0a26-77c0-b7c7-ddaa7a36a5eb-Q,
SHA`c50df7aa188ff89a16d2ab16ae6c53238ecc32531449375170d220d639151767`.
M/N/O/P evidence seals were freshly verified unchanged(112/147/220/467 files).

Next: redesign the wider prepare pipeline and its tails. Even zero world work
leaves66928 mean NTSC cycles, above59736; another enemy-only patch cannot solve
the target. Source/input/audio, player/mask and original graphics remain protected.
No human candidate/release was selected from these internal modest-gain tests.

Start only in dedicated fork `Frostbite — ISSUE #42` within the Frostbite
project, cwd `/Users/sandersouza/Developer/msx-gamePorts/frostbite`. Fork from
the committed native-band checkpoint on `codex/fix/39-atari800-performance`
(parent `b341e9f020f94de197a5bafa7d45b4fe678f9a4d`). The transfer message supplies
the exact checkpoint commit. Create `codex/feat/42-native-renderer` there.
PR #41 carries the research checkpoint; avoid accidentally closing #39.
Only the new issue chat edits after activation; predecessor stops mutations.
Do not reset inherited files or rebuild into previous artifact directories.

Read AGENTS.md, required Obsidian guidelines, approved original design, local
issue copy `.github/issues/frostbite/native-msx-renderer.md`, and
`docs/native-band-feasibility.md`. Private continuation with prior M-C build
details: `.superpowers/sdd/issue-39-local-current.md`.

## Exact artifacts and evidence

- Owner-test M-C: `outputs/presentation/playfield-m-c/build/`, ROM SHA
  `0e43bd16a5219a2d2548580e581ee5e26c7f440e715c18d96e07dbe033351ad0`.
  All 112 files of its existing seal freshly verified unchanged.
- N-B internal walker: `outputs/presentation/native-bands-n/build-b/`, SHA
  `cd90ef510ba8c52ca3792d7803c4308d211d2855b700e39cc8a2cadeddc1a751`.
  Hardened build-C is byte-identical. Original build-B sources archived.
- N evidence: matrix-b (2115), density-b (1920), ntsc-b (2253), pal-b (1886).
  Every original CPU/all-RAM checkpoint and three complete VRAM snapshots match
  M-C; traffic and non-world cycles unchanged. 514 host tests passed.
- Active cadence M-C → N-B: NTSC 31.1855 → 31.6490 (+1.49%);
  PAL 32.4926 → 33.1387 (+1.99%). Whole-route peak remains 489112 cycles.
  N is not an accepted architecture solution or human-test delivery.
- Offline shared residency, 56 slots/bank: NTSC 6852 → 2756 semantic misses;
  PAL 6803 → 2714. At 64 slots: 2559 / 2523. No Z80/FPS/transfer claim.
- Public aggregate `references/native-band-feasibility.json` binds measurements
  and model to private inputs. Public source contains no original-derived assets.

## Implementation starting point

M-C is the control, not a requirement to keep the renderer. Its average NTSC
busy cost is 111564 cycles, world 44776, source 22059, sprites 15207. Zero world
still exceeds the 59736-cycle frame. Address whole-frame and tail costs.

1. Declare a physical shared ice pool, initially using existing 64 slots per
   bank. Current IDs: bank 1 = 19..50 and 83..114; bank 2 = 9..40 and 73..104.
   Verify these against the live asset generator before editing.
2. Pin actual displayed and complete-next references. Use bounded exact lookup
   for pattern+color keys and prepared per-band NAME mappings. Audit scratch
   allocation explicitly; never assume unused low RAM survives BIOS/slot calls.
3. Replace generation-derived `p_fast_old_key` behavior and ownership checks
   for physical IDs shared across pages. Add an independent reference-based
   guard; do not merely remove the old private-page checks. Preserve overlap
   fusion destinations and visible pattern/color/SAT/SGT protection.
4. Original logic/input/collision/audio remain untouched and authoritative.
   Audit Seaquest's prepared-data/dirty-region approach, adapting for Frostbite's
   overlap/vertical phases and TMS9918 constraints instead of copying assumptions.
5. Measure the complete frame with the original F profiler/input adapter and
   matched active NTSC/PAL routes, plus complete source matrix and synthetic
   density. Update a NEW performance workbook, preserving M's original file.
6. Continue other stages as required by measured budget. Only deliver a useful
   candidate after review, with a versioned prerelease, exact ROM/source/hash
   and human tests. No human or physical acceptance has occurred for N.

No player-as-tiles, graphics concessions, fewer actors, hidden source steps,
turbo, expansions or changing original mechanics. Respect VDP IO spacing and
current-display ownership; eventual VBlank/timing acceptance remains separate.
Keep #39/#15/#16 open for their own unmet acceptance conditions.
