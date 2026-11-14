# Issue 14 — selective PSG effect gain

Owner request, relayed from the issue 44 chat on 2026-11-14: raise drowning,
bear pursuit and freezing volume by 25%, leaving other sounds and accepted
v0.0.31 gameplay/presentation unchanged. This supersedes the research handoff
to issue 39; issue 14 is the sole checkout writer again.

## Boundaries and measured feasibility

Static original-ROM inspection identifies the drowning/freezing volume stores
at F4D7/F4D9 (EB/F0 animation), and effective bear pursuit at F7F0/F7F2.
Their nonzero volume is 4 on both channels. The independently retained bear
route audio contains volume-4 pursuit and death intervals; silence is retained.
Further original CPU replay must bind every event to its actual store PC.

The requested amplitude factor 1.25 is +1.9382 dB. The pinned openMSX 21.0
AY/YM static volume model has sqrt(2) amplitude steps: 4 -> 5 is +41.4214%
(+3.0103 dB), the nearest available static level. This is an approximation,
not an exact 25% result or a measured analog gain on physical hardware.
Source: https://raw.githubusercontent.com/openMSX/openMSX/RELEASE_21_0/src/sound/AY8910.cc
No dithering, extra voice or global attenuation is introduced. These observed
effects have headroom; unrelated levels, silence and other effects stay intact.

## Implementation and acceptance

- Preserve the accepted ROM and pending issue 14 work. Keep the unrelated
  `scripts/build_compact_grid_experiment.py` untouched.
- Opt-in source-linked native projection; original source bus/latches/CPU/RAM
  remain authoritative. Four original caller operands select gain observers.
- Identify the selected invocation by its actual observer return address;
  no persistent effect state. Equal raw volume must still reproject physical
  volume, including selected 4 -> unrelated 4 and repeated selected 4.
- Reuse the two 19-byte volume-handler extents, allocate small observers in
  certified native holes, and place the shared 29-byte projector in the
  verified zero-filled 35-byte tail of the selected sparse-bear helper.
  Reject overlapping objects or the unselected P0-clear experiment.
  Preserve every other object address.
- Require actual executed native ROM event/PSG checks, original state/pixel
  checks, normal-speed NTSC/PAL cadence, and native format boot checks.
- Publish a new immutable diagnostic release with ROM/COM/BIN/support files,
  hashes, source commit, WebMSX link, precise quantization disclosure and
  requested human listening tests. Do not claim listening/hardware acceptance.

First 106-byte contiguous allocation attempt failed before packaging. Retain
that failed build as research only; no testable ROM was produced by it.
The second scattered allocation exceeded the compressed cartridge payload by
six bytes and failed its size assertion. The third source-linked layout fits
with ten payload padding bytes; it is the candidate under qualification.
