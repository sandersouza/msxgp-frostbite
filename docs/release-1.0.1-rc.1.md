> Superseded: this candidate corrupts igloo graphics during construction. Use [1.0.1-rc.2](release-1.0.1-rc.2.md).

# Frostbite 1.0.1-rc.1 — pre-game instructions

Test candidate for [issue #49](https://github.com/sandersouza/msxgp-frostbite/issues/49).
The stable 1.0.0 release is unchanged.

Before gameplay, the upper-right corner displays two aligned rows:

```text
F1: START
F2: SELECT
```

The block has eight-pixel top/right margins and uses simple MSX-style 8x8
glyphs. Selection keeps it visible; starting gameplay removes it from both
NAME pages. The background underneath is restored. The font reuses pre-game
igloo slots with key invalidation, so active igloo tiles reconstruct normally.
Native cold-load/clock bootstrap extents are reused and the old unreachable
SCREEN 2 initializer is cleared to retain a complete Normal 32 KiB cartridge.

All formats use the same source-defined runtime: standard-speed MSX1, 64 KiB
RAM, 16 KiB VRAM and PSG. The cartridge needs no mapper or disk; COM and BASIC
retain their usual loading requirements. Mechanics and input mappings are
unchanged. See the [artifact/qualification receipt](../references/compact-delivery/issue-49-start-select-hints.json).

## Automated evidence and limits

- Sixteen essential unit checks, native source assembly and five-format hashes.
- Real C-BIOS MSX1 keyboard routes in NTSC/PAL: all four variations, start,
  movement/jump, F2 return to selection and restart.
- Thousands of displayed pictures compared with 1.0.0 at matching coherent
  source states. Before play, differences are limited to the 80x16 text block;
  active pictures match exactly. Runtime guards check the retired initializer
  and exclude live igloo aliases when the font loads.
- These are bounded emulator routes. They do not establish fresh full-density
  timing, listening acceptance or physical-hardware certification. Small cadence
  differences on these routes are recorded in the receipt; no speedup is claimed.

## Human test steps

1. Load the candidate Normal cartridge at 100% speed in NTSC or PAL.
2. Check both lines are fully visible in the top-right corner, with F1/F2,
   colons and action words aligned. They must not cover the score or temperature.
3. Press/release F2 repeatedly through all four variations. Both lines remain.
4. Press F1. Both lines disappear immediately as gameplay starts; no letters or
   colored rectangles remain. Move and jump, land on ice and check igloo progress.
5. Return to selection with F2 and start again. Check for stale letters or
   damaged igloo tiles. Repeat in the other video standard and native format
   when available. Report version, machine/emulator, format and NTSC/PAL.

Next: owner display/play feedback and PR review before stable promotion.
Download the exact tested files from the
[prerelease](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v1.0.1-rc.1).
