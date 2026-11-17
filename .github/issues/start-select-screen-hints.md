# Show F1/F2 start and select hints in the top-right corner before gameplay

Players need visible instructions for starting the game and selecting a game
variation. Add this two-line block to the pre-game screen:

```text
F1: START
F2: SELECT
```

## Scope and acceptance criteria

- Display the exact uppercase strings in the upper-right corner, fully inside
  the visible screen and without obscuring existing information.
- Put the lines on consecutive text rows with the same left edge: `F1` and `F2`
  must share a column; the colons and action text must also align.
- Standard MSX text/glyphs are acceptable; no custom lettering is required.
- Keep both hints visible while waiting to start, including when F2 changes
  the selected game variation.
- Remove both lines as soon as F1 starts actual gameplay. Restore the correct
  background underneath, with no leftover glyphs, damaged HUD or flicker.
- Tie visibility to the actual pre-game/gameplay state; do not show the hints
  during gameplay. Re-entering the pre-game screen restores the instructions.
- Preserve F1/F2 behavior, gameplay mechanics, controls, audio and standard-speed
  MSX1 compatibility (64 KiB RAM, 16 KiB VRAM, built-in PSG).

## Definition of Ready

- Text, location, alignment and visibility transition are owner-specified.
- Start from `main` after PR #48, commit
  `964d6a2639019cec014ece343084c6fe70169076`.
- The repository-only native build is available. Inspect the existing pre-game
  state and screen ownership before choosing the precise tile coordinates.
- No new graphics design or gameplay rearchitecture is needed.

## Definition of Done

- Acceptance criteria above are verified in NTSC and PAL: cold start, repeated
  F2 selection, F1 start, and return to the pre-game screen when applicable.
- Record before/after images and confirm no text remains during active play.
- Essential automated checks pass; all native formats build from repository
  sources after `make clean`. Exercise the changed display in the emulator.
- Deliver a focused linked PR from `codex/enhancement/<issue>-start-select-hints`
  through its dedicated `Frostbite — ISSUE #<issue>` chat.
- Because the game bytes change, publish a new versioned testable prerelease
  with the exact ROM, SHA-256, source commit and human test steps. Preserve the
  published 1.0.0 assets and baseline; do not overwrite them or claim that the
  changed ROM still matches the frozen 1.0.0 hashes.

## Classification and estimate

- Type: Feature. Label: enhancement. Priority: P2.
- Project: MSX Game Ports #7. Initial status: Ready.
- Size: S. Estimate: 2 hours for the bounded display/state change, emulator
  verification and delivery; this is an estimate, not a deadline.
- Dependencies: self-contained native build delivered by PR #48 (merged).
- Repository metadata limitation: no `priority:p2` label or open milestone is
  currently configured. Record P2 in the project's existing Priority field;
  leave the milestone unset rather than inventing shared configuration.

## Delivery for review

- PR: https://github.com/sandersouza/msxgp-frostbite/pull/50
- Test prerelease: https://github.com/sandersouza/msxgp-frostbite/releases/tag/v1.0.1-rc.2
- Exact tested source: `c3dcda4`.
- Sixteen unit checks, source-only five-format build and NTSC/PAL keyboard/display
  qualification passed. Exact hashes and evidence limits are recorded in
  `references/compact-delivery/issue-49-igloo-fix.json` and release assets.
- Status: In review. Owner display/play feedback is pending before stable promotion.

RC1 was found to corrupt igloo graphics and is superseded. RC2 preserves the live graphics assets and adds a separate controlled diagnostic for all 16 stages on both pages in NTSC/PAL. Existing construction takes priority over borrowing font tiles.
