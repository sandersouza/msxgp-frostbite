# Direct enemy-band measurements — issue #42

The first complete-band variant, Q-C, is rejected against the sealed P-C
control. Its per-tile metadata construction outweighed traversal savings.
The revised Q-E stores a complete physical-owner identity and reconstructs
actor keys independently for auditing. It saves some whole-frame time, but
does not solve the original-cadence requirement.

| Active original-input route | P-C | Q-C | Q-E | Q-E change vs P-C |
| --- | ---: | ---: | ---: | ---: |
| NTSC source updates/s | 32.70293 | 31.48971 | 33.63501 | +2.8501% |
| PAL source updates/s | 34.23214 | 33.01443 | 35.29376 | +3.1012% |
| NTSC mean busy cycles | 106046 | 110383 | 102843 | -3203 |
| PAL mean busy cycles | 120046 | 125153 | 116412 | -3634 |

Q-E is7.85% NTSC /8.62% PAL faster than M-C. These are measured logical source
updates per elapsed second, including pacing waits and every PAL source step;
they are not a60Hz presentation or stable30Hz claim. The original NTSC target
remains unmet. Active P95 is219663 NTSC /242981 PAL cycles, active maxima
319748 /348578, and the complete-route maximum is484270. Startup's maximum
is2606 cycles worse than P-C. Synthetic density improves9.04% against M-C,
but is not natural high-level gameplay evidence.

## Representation and protected contracts

The existing copy driver, geometry IDs, original I packet generator, exact
ice/object fusion, fixed physical roles, player and black mask are retained.
Each changed page/lane publishes two24-byte mono pattern segments; colors are
filled only on a color change. The complete group/variant/coarse/color identity
becomes valid after the required planes. Its variant byte includes coarse in
bit7, making the Y128 split explicit. Unchanged identities reuse their planes.
Each copy writes NAME entries directly and retains dirty-row skipping, zero
cells, wrap31→1, hidden column1 and original fusion ordinals.

The selected template profile draws floes before objects. Its fusion reads old
ice keys, so it does not need eager actor-cell metadata. Old actor metadata
must remain FF. The independent checker reconstructs every actor key from the
saved physical identity and the live immutable ROM directory, verifies actual
PGT/CGT bytes and enforces the original same-generation NAME rule. The archived
geometry pool's older directory offsets are not live ROM offsets; an initial
auditor failure exposed this distinction and was corrected before acceptance.
No active-display protection was removed. Later paths that read old actor keys
must provide a runtime decoder or restore their eager metadata first.

Extra RAM is exactly128 bytes atE800..E87F; E880..F33F remains guarded. Combined
P/Q resident code is195 bytes in obsolete J space, bank7 code1025 bytes, ending
atA50D below the unconditional F footer breakpoint atA800. Mapper-changing
helpers restore bank7 through resident gates. No gameplay/input/audio code,
sprite conversion, player tiles, reduced actors or graphics concessions are
part of this experiment.

## Verification and identity

Q-C ROM SHA-256: `5526c58698a06d5ef97462ef3c543350c3ba38530b4b21d871d821b353235379`.
Q-D/E ROM SHA-256: `2654da3abdb2fc2624f6485a9104327447e0493f64a864feb56b41212dc5ada9`.
D and E are byte-identical; E records the updated checker/builder sources.
The default builder still reproduces exact P-C bytes.

- 209088 actual Z80 component cases per variant cover66 reflected groups,
 128 variants, eight physical owners, all15 colors, cold/hit/color transitions,
 padded columns/rows and the Y128 split.
- 2115 original scenes and1920 synthetic dense scenes have zero pixel differences
 for both Q-C and Q-E, with source/ABI/slot/VDP-spacing guards.
- 2253 NTSC and1886 PAL original-input images match the source pixel oracle.
 Each route matches all2254 original CPU/all128RAM checkpoints. Active NAME,
 PGT/CGT, SAT and complete referenced SGT protection remains enabled.
- Actual24-byte Q and128-byte P CGT fills are counted in traffic and inclusive
 IO cost:33 cycles/byte plus55 per fill. The standard stream remains29 plus53.
 The Q primitive is explicitly probed; bypassed generic counters are not savings.

Local evidence: `outputs/presentation/direct-enemy-q/`, including rejected
builds and failed checks. `analysis-c.json` and `analysis-e.json` use the same
authenticated original F route/profiler and M-C analysis as the O/P checkpoint.
Public aggregate measurements contain hashes, not original-derived assets.

The Q workbook preserves the M and O/P workbooks. It contains8278 paired frame
observations,424 stage/function rows, formula-backed summaries and an editable
native chart. Formula, sensitivity, saved XML and visual checks pass; native
Excel, listening, human emulator and physical hardware acceptance are untested.

## Remaining architecture work

Q-E remains an internal checkpoint, not a selected human-test delivery. Whole
frame NTSC stages still cost world35915, source22200, sprites15207,
dirty-state9179, header6426, preparation5513 and background5031 cycles on average.
Even eliminating all world work leaves66928 mean busy cycles, above the59736
video-frame budget. Further enemy-only work cannot solve the whole-frame target.
The next design must address the wider prepare pipeline and its large tails;
source cadence and correctness remain the acceptance criteria.

Independent branch review and public canonical-build integration remain required
before selecting a human ROM. The current builder authenticates a sealed local
M-C/contact14 prerequisite; inherited source-commit fields identify ancestors,
not a self-contained canonical release source. Keep #39/#15/#16 open, preserve
all controls, and publish the selected useful candidate as a new prerelease
with exact ROM/source/hash and concrete human tests when delivery is ready.
