# Issue #2 handoff — immutable source identity and measured cadence

Issue: https://github.com/sandersouza/msxgp-frostbite/issues/2
Branch: `codex/chore/2-reference-inventory`.
Base: `b2a232cd170a2fe4c9b2a63ce1a0687ab33d7396` (issue #1 delivery).
Inventory commit: `3ab81d9afe307c4c55121fc3ff3aa31f53ba8235`.
Final reviewed head and integration identity are recorded by this issue's PR.

## Delivered scope

- Immutable [reference manifest](../../references/manifest.json) and verification
  CLI with explicit mismatch/missing-input failures and no automatic rebaseline.
- Original-free tests for structure, corruption, CLI boundaries and versioned
  Stella serialized-counter decoding, including 313-line/variable-queue fixtures.
- A bounded headless Stella 7.0 probe using fresh isolated settings and explicit
  startup, console Reset and Select inputs. Raw captures remain local/ignored.
- [Measured metadata](../../references/source-timing.json) and
  [inventory/timing explanation](../reference-inventory.md).
- No MSX ROM, scaffold, full toolchain setup or gameplay implementation.

## Canonical input

`references/roms/frostbite.bin`, 4096 bytes, 4K.
SHA-256: `cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834`.
MD5: `4ca73eb959299471788f0b685c3ba0b5`.
Reset/raw IRQ word $F000; unused NMI-position word $EABA.
Stella catalog: Frostbite (1983) (Activision), AX-031, Steve Cartwright.
The exact commercial revision, intended market and upstream dump provenance
remain unverified. This hash is authority; do not substitute another ROM.

## Timing evidence and limits

Two isolated Stella captures agree on 262-line steady output and an aligned
interval of 11,967,112 CPU cycles over 601 observed frames: 19,912 cycles/frame.
Select observations at RAM[$80] progress through 0,1,2,3 and console Reset
preserves the selected value. ALE 0.12.1+8a8fafb corroborates 262 lines in 600
post-warmup NOOP frames, with frame_skip=1, repeat probability=0 and seed=0.

Startup records include 51/310-line emulator boundary events and possible
partial frames. Requested debugger updates are not equivalent to completed
source frames. Read observed cycle/frame/current-line counters, not batch size.

**Full-state/serialized repeatability was not established.** The two captures'
absolute checkpoint counters/RAM can differ even with the explicit settings.
Their common stable timing and mode effects are the delivered result.
Issue #7 must establish aligned deterministic state/RNG/input traces; do not
use these checkpoints as native gameplay equivalence oracles. No precise
wall-clock/physical Hertz or physical-machine result is claimed.

The source decoder contract is upstream Stella commit
`d55b1aec0d067a4c901a6dcdf81cb8f579685659`, little-endian 7.0 debugger-state
format. It follows CPU/RIOT/variable delay queue/frame-manager serialization,
not a guessed numeric offset. Unknown formats fail. Backend binary hash/build,
script/settings and per-checkpoint state hashes are in the metadata.

## Reproduce

```sh
python3 -B -m unittest discover -s tests -v
python3 -B scripts/reference_inventory.py
python3 -B scripts/source_timing.py --output outputs/reference-inventory/timing.json
```

Tests need no original inputs or Stella. The timing command requires the local
ROM and installed Stella 7.0 with Debugger; it is not a fresh-install claim.
Raw captures always stay under ignored outputs/reference-inventory/ even if a
different compact report destination is selected. They include source-derived
ROM/state data and must not be added to Git.

## Preserved material and successor

The full snapshot and `.legacy/seaquest/` quarantine from issue #1 remain
untouched. Read [preservation/provenance](../baseline-preservation.md) before
selective reuse. Tool caches `.tools/` and `.venv/` remain local; their presence
is not a clean environment verification. Initial byte-identical disassembly
research is still under ignored outputs/frostbite-planning/.

After this issue's checks/review pass and its delivery is integrated, close #2
and set Done, then start [issue #3](https://github.com/sandersouza/msxgp-frostbite/issues/3)
in another dedicated Frostbite fork. Revalidate GitHub/branch/dirty state and
the canonical hash, then reconstruct/rebuild/annotate the actual 2600 image.
The old Seaquest reference rebuild assumes Atari 800 inputs and source-specific
addresses; it cannot be reused unchanged.

Transfer exclusive checkout ownership only after a clean integrated state;
the previous chat stops editing after dispatch. Continue autonomously along
ready dependencies. Every later testable MSX ROM needs its exact attached
prerelease and human-test checklist. This research-only issue creates none.
