# Scoring, progression and game variations

Issue [#13](https://github.com/sandersouza/msxgp-frostbite/issues/13) retains the
existing static native Z80 mechanics. The original ROM and complete CPU/all128RAM
comparisons define correctness. There is no replacement high-level score or
progression model in the cartridge.

`scripts/progression_cases.py` declares816 primitive and818 full-phase fixtures.
The primitive arithmetic assertions cover valid BCD awards, low-byte carry,
5000/10000 threshold gates, six-digit rollover, attract inhibition, reserves0/1/8/9
and the saved player's complete six-byte record. Exact source flags and all
temporary RAM are compared separately, rather than inferred from decimal totals.
The block award is10×min(CB+1,9); progression remains an uncapped byte.

Full phases exercise every level byte and both players, every variation and
reserve pair0/1/8/9, each dispatch bit and combined priorities, delayed bonus/fish
envelope boundaries, and Reset/Select with color/difficulty switch combinations.
Each phase acquires actual original-clock contacts from the audited catalog;
neutral collision substitutions are forbidden. Recovery swaps exactly C8..CD
with CE..D3, skips an exhausted other record, and consumes one reserve from the
selected record. The inactive world is not separately saved. Both records empty
produce C6=FF/F1=00; that differs from single-player emulator terminal shortcuts.

The initial exploratory checks passed816 actual-Z80 primitive cases (maximum3139
cycles) and728 complete visible/native phases (maximum22609 cycles) against the
unchanged v0.0.5 mechanics. These are controlled fixtures, not continuous gameplay
or acceptance of a new release. Later sections record the clean source/native
evidence; subsequent sections record the new ROM's complete paced matrix.
Manual emulator and physical tests are pending.

## Continuous original source acceptance

All eight cold input-only source routes and their independent complete replays
passed. They contain21468 logical intervals, each retaining CPU, all128 RAM,
TIA, RIOT, raw inputs and the serialized final capsule. Every replay preserves
the original restore journal and ends byte-identically. Nothing writes active
source state, disables a hazard or skips source instructions.

| Variation (source80) | Progression intervals | Exhaustion/restart intervals |
|---|---:|---:|
| 0 regular one player |2254|4334|
| 1 regular alternating players |2268|2537|
| 2 advanced one player |2061|1700|
| 3 advanced alternating players |3051|3263|

Progression requires construction, actual door entry, complete block/temperature
bonus and initialized next level. Exhaustion requires an observed death,
both-reserves-zero terminal C6=FF/F1=00, real Reset and a completed recovery delay
before active control. Alternating exhaustion routes observe seven natural
record swaps1→0→1→0→1→0→1; the six-byte active/saved records are checked exactly.
The regular progression route also swaps both ways with distinct score/igloo
records. This certifies source routes, not target replay or frame timing yet.

Advanced input proposals were searched with the existing original-CPU/contact
model. That search produces controller pins only. Unchanged Stella execution and
an independent full replay certify the actual route; predicted states never
enter the source capture. Failed/stopped exploratory routes remain ignored and
are excluded from acceptance. The compact
[source result](../references/progression-source-result.json) binds each accepted
route/replay receipt and exact producer revision without distributing raw states.

## Native progression diagnostic and measured optimization

Clean candidate `0.0.6-progression` from
`ac146a7c82bd5ab77a5dff2deb5d5452a0478c99` is4194304 bytes/ASCII16, SHA-256
`1223931972bd7e0ec02a8c66805cb30ac0defaad1abd71dd67c9c8a7746be5f6`.
All eight actual MSX1 cold input-only routes match21468 complete original CPU/RAM
checkpoints and every named milestone. The818 controlled full visible/native
phases also pass (maximum20223 cycles). Intentional real target mutations of
score CA, saved record CE and active-player C7 are rejected at those exact bytes.

The first candidate preserved the old core but the new advanced route exposed a
real PAL overrun:81673 cycles for71364. Profiling measured only~4500 cycles in
contact acquisition; a16-iteration native translation of a pure ROM-indexed
write loop dominated completed-igloo work. That failed candidate remains private
and is excluded from acceptance.

`native_write_loop.py` recognizes the instruction pattern rather than a game
rule/address substitution. Runtime X=0 and a source-derived safe bound prefix
use precomputed partial RAM writes and exact final A/X/Y/N/Z/C; V/mode and
untouched RAM are preserved. Reads must remain in approved ROM data, writes in
canonical RAM, and no destination may alias the bound. Every other entry follows
the original native body. Input instruction points, RNG order, source steps and
presentation remain intact. Generated effect data stays local; public metadata
contains only domain/address descriptions and hashes.

An independent original-CPU oracle and actual standard MSX1 Z80 microcartridge
pass135168 cases:69649 summarized executions and65519 rejected-guard executions,
including all256×256 index/bound pairs, all source accumulator values and flag
combinations. Complete CPU/all128RAM, untouched bytes, mode/V, IX/IY/SP/DI and
memory guards are verified. The existing native shift/flag lowering is unchanged.
The new core uses10240 of16384 bytes in its existing bank; cartridge size, RAM
requirements, source contact catalogs and their helper closure remain unchanged.

The complete current-ROM matrix now passes all12 new/retained routes in all96
clock/layout/width combinations:198560 complete CPU/all128RAM checkpoints and
182308 completed pixel frames. Peaks are49732/59736 NTSC and71081/71364 PAL.
The smallest margin is283 cycles on advanced one-player exhaustion/restart,
PAL/layout1/width1; future HUD/art/audio changes require fresh full acceptance.
Fifteen dense modes add3600 frames, max45789 NTSC/64802 PAL, with all14 named
runtime faults detected and raw witnesses independently audited. Original
catalog/helper inputs and published v0.0.5 ROM bytes remain unchanged.

See the [reproduction checklist](progression-checklist.md) and
[human tests and limits](releases/v0.0.6-progression.md). Final raw-evidence
sealing, review, integration and public release delivery remain pending until
recorded in the issue handoff; completed captures alone do not close the issue.

The approved S1/S2/V1/V2/V3/C1 contracts remain in
[gameplay-contracts.md](gameplay-contracts.md). Definitive HUD/art/audio belongs
to #14; this work certifies mechanics and keeps presentation adaptations explicit.
