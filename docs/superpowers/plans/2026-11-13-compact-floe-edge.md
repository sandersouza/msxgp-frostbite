# Compact Floe Edge Contact Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the rare edge contact tables with bounded source-clock
arithmetic, preserving the accepted electrical responses.

**Architecture:** Use the existing interior footprint clipped to visible
X8..159. Add analytic horizontal masks for the hidden HMOVE clocks and delayed
GRP/ENAM events. A universal160-entry,16-clock rectangle window needs320bytes;
hold masks account for stopped counters. Adjacent player-byte equality retains
the original GRP update behavior. No large per-position edge lookup is admitted.

**Evidence:** Ignored `issue44-edge-event-model-03`, sparse model04 and
`issue44-edge-analytic-01` independently agree with every816,000edge cell ×228
views. The rejected model02 omitted the one-color-clock GRP/ENAM delay. Its
726 differing horizontal columns remain archived. An earlier explicit lookup
needed51,159bytes and was rejected.

**Spec:** `docs/superpowers/specs/2026-11-13-compact-native-formats-design.md`

## Task 1: Maintained host compiler

- [x] Add hand-derived rectangle-window, hold and clear-line mask tests; RED.
- [x] Implement analytic masks with explicit bounds and no embedded ROM bytes.
- [x] Compare every declared edge cell against the accepted ROM independently.
- [x] Check visible clipping and scalar shadow separately; run host suite.

## Task 2: Native component

- [x] Add an isolated edge fixture; observe missing-entry failure.
- [x] Implement bounded Z80 masks, sharing existing floe/player assets.
- [ ] Measure code/data/scratch RAM and native cycles in the declared corpus.
- [ ] Verify source/ROM provenance, ABI, write bounds and native outputs.
- [ ] Review and record limitations before flat runtime integration.

Native work is staged: qualify all24,000horizontal mask-generator inputs first.
Its32-byte result is independent of player Y/glyph/reflection. Native view/Y
convolution and combined electrical outputs remain a subsequent component gate;
the generator proof alone must not be labeled a complete edge contact kernel.

The default game, releases and sealed controls remain unchanged. Enemy/shore
edge equivalents, copy dispatch, complete layout, loaders and whole-frame
performance remain required. Component probes are non-playable fixtures.
