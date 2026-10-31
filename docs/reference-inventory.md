# Frostbite original reference inventory and source timing

## Immutable authority

The sole supplied reference is local `references/roms/frostbite.bin`.
[manifest.json](../references/manifest.json) records its exact identity:

| Property | Verified value |
| --- | --- |
| Length / layout | 4096 bytes, plain Atari 2600 4K cartridge |
| SHA-256 | cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834 |
| MD5 | 4ca73eb959299471788f0b685c3ba0b5 |
| Reset word | $F000 |
| Raw trailing IRQ word | $F000 |
| Unused trailing NMI-position word | $EABA |

The 6507 cartridge bus window is $1000–$1FFF with address mirrors. Use
$F000–$FFFF as the disassembly window for this image. The unused NMI-position
word is reported as raw structure, not an executable interrupt entry point.

Stella's matching catalog entry is **Frostbite (1983) (Activision)**, model AX-031,
Steve Cartwright. The installed Stella ROM-info command reports both joystick
ports, 4K and NTSC autodetection. The matching catalog has no commercial revision
suffix. **Exact commercial revision, upstream dump provenance and intended sales
market remain unverified.** A catalog/name match does not establish them.

The binary authority is this exact hash. A different image must fail verification;
do not rename, download, substitute or automatically rebaseline it.
The original ROM and serialized states remain ignored/local.

## Measured cadence

The [source-timing record](../references/source-timing.json) contains two isolated
Stella 7.0 captures, ten checkpoints per run and the exact backend binary hash,
build, host, script hash, settings, state hashes and observed counters.

- Auto display detection and the saved frame layout identify NTSC timing.
- Aligned steady/console-Reset endpoints measured **262 scanlines per frame**.
- Their difference is **11,967,112 CPU cycles over 601 observed frames**:
  **19,912 CPU cycles per frame**, exactly 262 × 76.
- Select checkpoints changed RAM[$80] through 0 → 1 → 2 → 3 while retaining
  262-line steady output; subsequent console Reset retained the selected value.
  These are reference observations, not a complete gameplay/state-map contract.
- A separate post-warmup ALE 0.12.1+8a8fafb probe observed **600/600 frames with
  262 scanlines**, using seed 0, frame_skip=1 and repeat_action_probability=0.
  ALE uses a Stella-derived core; this is corroboration, not physical evidence.

No exact 60 Hz assumption is made. The measured source unit is scanlines/CPU
cycles; a target scheduler must use the appropriate nominal source clock rather
than replacing the cadence with an arbitrary exact 60 Hz tick. Conversion to
wall-clock/physical Hertz was not measured here.

## Startup and reproducibility boundary

The script explicitly resets the emulated System, starts neutral joysticks,
color and difficulty B/B, disables RAM/CPU/TIA/bank/hotspot/floating-pin
randomization and TV jitter, then records initialization and console inputs.
System reset is distinct from pressing the Game Reset switch.

First-update checkpoints record a 51-line startup event; the next checkpoint
records a 310-line previous event and may be partway through another frame.
These are emulator startup boundary observations, not gameplay cadence.
The raw checkpoints preserve current scanline and observed frame count.

Stella's debugger `frame N` asks for N update calls; it does not guarantee N
completed frames or a frame-aligned stop during initialization. Its bounded
timeslice can stop partial startup work or account for additional frame edges.
Requested calls and observed counters are therefore recorded separately.

The two runs agree on the measured aligned timing interval and mode checkpoints.
**Absolute checkpoint/RAM states and serialized bytes are not identical.**
The report exposes both runs and marks those repeatability flags false; it does
not claim a deterministic full-game replay. The complete cause/alignment of this
startup-state variability remains research for [issue #7](https://github.com/sandersouza/msxgp-frostbite/issues/7).
No expectation values for native gameplay should be derived from this timing
inventory alone.

## Decoder and backend boundary

The decoder follows the reviewed Stella 7.0 serialization structure: state
header, System cycle count, CPU, RIOT RAM/timers, variable-length TIA delay queue
and AbstractFrameManager counters. It does not scan for the number 262 or use a
fixed frame-manager offset. Tests also decode 313-line synthetic states.

Support is intentionally limited to little-endian hosts and the validated
`07000000state` format with DEBUGGER_SUPPORT. The launch log must identify
Stella 7.0 with Debugger. Unknown headers, malformed queues/booleans, truncation
and unknown frame layout fail. The source contract commit and blob identities
are recorded alongside the evidence; future format changes require review.

The probe uses fresh isolated settings/output directories, a validated local
ROM copy, dummy SDL video/audio and a 30-second subprocess timeout.
It leaves raw local captures under ignored outputs/reference-inventory/ and
never reads or changes the user's normal Stella settings.

## Reproducible commands

From the repository root, with the supplied ROM and installed Stella available:

```sh
python3 -B -m unittest discover -s tests -v
python3 -B scripts/reference_inventory.py
python3 -B scripts/reference_inventory.py --describe
stella -rominfo references/roms/frostbite.bin
python3 -B scripts/source_timing.py --output outputs/reference-inventory/timing.json
```

The tests use synthetic fixtures and require no original ROM or emulator.
The inventory default verifies identity; --describe is explicitly inspection
only and never writes the manifest. A missing, wrong-sized or mismatching input
fails clearly, and the timing command verifies before launching a backend.

The timing command runs twice and requires matching backend/settings, stable
interval measurements and selected-mode checkpoints. It reports full-state
equality separately. Raw state files contain source-derived execution data
and must not be committed. Public source-timing.json is a compact observation
record, not a serialized replay.

The copied host tools are present locally; this does not establish the fresh
development setup planned in issue #5. No MSX ROM, gameplay, manual listening,
full-game or physical-hardware acceptance is delivered by this issue, and it
creates no testable-ROM release.

## Sources

- [Stella 7.0 catalog](https://github.com/stella-emu/stella/blob/d55b1aec0d067a4c901a6dcdf81cb8f579685659/src/emucore/stella.pro)
- [Stella serialization](https://github.com/stella-emu/stella/blob/d55b1aec0d067a4c901a6dcdf81cb8f579685659/src/emucore/Serializer.cxx)
- [Frame-manager counters](https://github.com/stella-emu/stella/blob/d55b1aec0d067a4c901a6dcdf81cb8f579685659/src/emucore/tia/frame-manager/AbstractFrameManager.cxx)
- [Debugger update behavior](https://github.com/stella-emu/stella/blob/d55b1aec0d067a4c901a6dcdf81cb8f579685659/src/debugger/Debugger.cxx)
- [ALE TIA saved counters](https://github.com/Farama-Foundation/Arcade-Learning-Environment/blob/8a8fafb/src/ale/emucore/TIA.cxx)
- [ALE warmup/reset policy](https://github.com/Farama-Foundation/Arcade-Learning-Environment/blob/8a8fafb/src/ale/environment/stella_environment.cpp)
