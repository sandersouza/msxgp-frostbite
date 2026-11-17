# Frostbite 1.0.1-rc.2 — igloo graphics correction

Replaces the faulty 1.0.1-rc.1 test candidate for issue #49. Stable 1.0.0 and
the old published binaries are unchanged.

The F1/F2 text keeps its approved position, alignment and glyphs. The earlier
module overwrote addresses already reused for native background/igloo assets.
Those assets are now preserved, with build-time guards against overwriting
them or the IRQ vector. The module uses explicit unused cold-bootstrap/RST
extents. Removing unnecessary cartridge-header alignment provides room while
retaining a complete Normal 32 KiB cartridge.

Instructions appear on the empty initial/selection screen and disappear when
play starts. If an existing igloo occupies the borrowed tiles, its graphics
take priority and the instructions remain hidden until empty selection returns.

## Checks and limits

- Essential unit checks, source-only build, all five native files and CI.
- Real keyboard-driven NTSC/PAL selection/start/restart routes against 1.0.0.
- A separate controlled renderer diagnostic injects all 16 igloo construction
  stages in both video standards and compares displayed pictures with 1.0.0.
  The injection is explicitly recorded; it is not natural progression evidence.
- Exact hashes and coverage are in
  [the candidate receipt](../references/compact-delivery/issue-49-igloo-fix.json).
  No fresh full-density timing, owner play/listening or hardware acceptance is
  claimed.

## Please test

Load the [new prerelease](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v1.0.1-rc.2)
at 100% speed as Normal, MSX1 with 64 KiB RAM / 16 KiB VRAM. Check the F1/F2
text, select with F2 and start with F1. Build the igloo through several stages
and complete it: no black blocks, stray patterns or damaged HUD should appear.
Repeat in NTSC/PAL and report format, emulator/machine and version in #49.
DOS runs `FROSTBIT.COM`; BASIC requires the launcher and both BIN files together.

Next: owner confirmation of the igloo fix and review of PR #50 before promotion.
