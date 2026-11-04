# Direct enemy bands implementation plan

> Execute inline with superpowers:executing-plans; ongoing owner-authorized
> architectural rewrite in the dedicated issue42 checkout.

**Goal:** remove generic enemy-cell publication and measure whole-frame gain.
**Architecture:** exact per-owner band cache, two fixed mono transactions,
direct NAME writes and retained original fusion.
**Spec:** docs/superpowers/specs/2026-11-04-direct-enemy-bands-design.md
**Tech Stack:** Z80/sjasmplus, Python .venv, openMSX, sealed P-C and M-C controls.

## Constraints / review focus

MSX1/64KiB/16KiB/PSG, original CPU/input/audio/mechanics and all graphics/actors;
no player tiles/mask changes, no simulation reduction. Bound partial dirty rows,
zero descriptor cells, geometry-column padding, lane1Y127/128 bank split, wrapping
copies, color changes and ice fusion ordinals. Source-derived artifacts ignored.

- [x] Synthetic owner/normalization and variable-length IO accounting negatives.
- [x] Add conditional resident wrappers and banked direct-band implementation;
  authenticated builder retains all protected I/contact/template allocations.
- [x] Actual Z80 component checks, full source matrix, density/boundary/overlap
  cases, then paired original-input NTSC/PAL whole-frame CPU/RAM/pixel checks.
- [ ] Update performance workbook and evidence seal, preserve P-C/M-C and all
  rejected experiments. Source/ROM/tool/input identities remain explicit.
- [ ] Independent whole-branch review and meaningful checks, issue/PR updates,
  and versioned release with exact useful candidate and human tests when selected.

Ruling: replace Q-C's eager actor keys with saved owner identities after its
measured regression; see the design revision and docs/direct-enemy-progress.md.
Q-E is correct on the bounded tests but gains only2.85%/3.10% over P-C. Keep it
internal while the wider pipeline and source integration remain unresolved.
