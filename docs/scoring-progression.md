# Scoring, progression and game variations

Issue [#13](https://github.com/sandersouza/msxgp-frostbite/issues/13) retains the
existing static native Z80 mechanics. The original ROM and complete CPU/all128RAM
comparisons define correctness. There is no replacement high-level score or
progression model in the cartridge.

`scripts/progression_cases.py` declares816 primitive and728 full-phase fixtures.
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
or acceptance of a new release. Clean committed producers, new diagnostic ROM,
continuous all-mode progression/turn/exhaustion/restart routes and all paced
views/clocks are still required. Manual emulator and physical tests are pending.

The approved S1/S2/V1/V2/V3/C1 contracts remain in
[gameplay-contracts.md](gameplay-contracts.md). Definitive HUD/art/audio belongs
to #14; this work certifies mechanics and keeps presentation adaptations explicit.
