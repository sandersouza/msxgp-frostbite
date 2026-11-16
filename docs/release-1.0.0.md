# Frostbite 1.0.0 baseline

[Published 2026-11-14](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v1.0.0).
The owner approved stable promotion of the exact v0.0.32 game binaries;
packaging and the ROM filename changed, with no runtime byte changes.

- Release tag: `v1.0.0`, source `c492ccd7145626a627ffd204f37e72722a4864df`.
- Runtime build: `001f802f9589c826d5e0463834b6b09ca8dc6329`, with `--effect-gain`.
- Target: standard-speed MSX1, 64 KiB RAM, 16 KiB VRAM, built-in PSG.

## Exact game files

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| frostbite-1.0.0.rom | 32768 | `cfce4fe274165e1cd0be0a0ba76ef0a48e38c7ed7fec10de84c673335c2b82b4` |
| FROSTBIT.COM | 32585 | `a556452bc1f5af3091d8f4c43e1b6c3b9581cb7ef37f627b80ececad1bfcfd39` |
| FROSTBIT.BIN | 21325 | `f7f54f973008187b91274f260ed2a5ea113240ca100092b7f73958d35f5bd903` |
| FBGFX.BIN | 11797 | `b07a3d00775b85513c2978394e42fedc2076f0843b97ae956c7576b48342ad9b` |
| FROSTBIT.BAS | 80 | `8dda3742fd166fcd6448f98e7c344a92646b556f188ab2b99757aba3f0f26cd8` |

The release includes a ZIP, `SOURCE.txt`, `SHA256SUMS`, loading instructions
and `qualification.json`. Its historical manual/owner flags are preserved
verbatim; they do not invent physical or listening evidence. The public
[selective-audio receipt](../references/compact-delivery/issue-14-selective-gain.json)
binds the runtime files and automated qualification.

## Behavior and evidence boundaries

The game preserves the accepted mechanics, graphics, controls and presentation.
Drowning, freezing and bear-pursuit PSG volume changes from level 4 to 5,
approximately +41.4% nominal amplitude in the tested model. Other effects and
silences retain their previous levels. This is the closest static PSG step to
the requested +25%, not an exact +25% amplitude change.

Release-time automated qualification includes 5,724 audio callbacks, 2,115
original CPU/audio intervals, 2,115 original image cases, 1,920 dense scenes,
NTSC/PAL IRQ boundaries, natural state/pixel/ownership routes and four actual
DOS/BASIC boots. These are historical results for the exact published bytes.

| Route | NTSC pictures/s | PAL pictures/s |
| --- | ---: | ---: |
| Regular | 30.1089 | 28.3812 |
| Bear | 28.0966 | 24.0761 |

The original logic clock is distinct from presentation cadence. Original
60-picture/s presentation and physical-hardware certification are not claimed.
Further console/attract, timing, listening and physical checks require their
own evidence; stable owner approval does not automatically establish them.

## Regression play checklist

Use the [README controls and loading instructions](../README.md). At normal
speed, start, move/jump, land on ice, build the igloo, finish a level and reset.
Check comfortable drowning/freezing/bear volume, unchanged pitch/rhythm and no
stuck sound after death/reset. Test Normal cartridge, DOS and BASIC separately.
Report model/emulator, NTSC/PAL, format and exact version for any issue.

Changed game bytes require a new version and release. Published 1.0.0 assets
and the source tag remain the recovery baseline.
