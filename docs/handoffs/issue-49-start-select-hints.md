# Frostbite — ISSUE #49

- Issue: https://github.com/sandersouza/msxgp-frostbite/issues/49
- Project: Frostbite, `/Users/sandersouza/Developer/msx-gamePorts/frostbite`.
- Base: `main`, `964d6a2639019cec014ece343084c6fe70169076` (PR #48 merged).
- Prepared branch: `codex/enhancement/49-start-select-hints`.
- Scope: show exactly `F1: START` and `F2: SELECT` on consecutive rows in the
  upper-right corner before gameplay. Align both keys, colons and action text.
  Standard MSX glyphs are acceptable. Hide/restore the area as gameplay begins;
  keep the hints visible while selecting variations with F2.
- State: implemented and awaiting owner play/display feedback and PR review. Classification:
  Feature, enhancement, P2, S, estimated 2 hours. Project fields are set. No open
  milestone or priority label exists; this limitation is recorded in the issue.
- Local issue draft: `.github/issues/start-select-screen-hints.md`, identical to
  the published body. These planning files belong exclusively to issue #49.
- Build: repository-only `make build`; Python standard library, pinned sjasmplus
  provisioned automatically, vendored ZX0 compressor. `make clean` removes only
  `outputs/`. No private ROMs, upstream images or sibling repos are required.
- Verified baseline: 16 unit tests; clean-source build and Linux CI passed for
  PR #48. All five game files reproduced 1.0.0; this is byte-identity evidence,
  not fresh manual/physical acceptance.
- Exact 1.0.0 cartridge SHA-256:
  `cfce4fe274165e1cd0be0a0ba76ef0a48e38c7ed7fec10de84c673335c2b82b4`.
  All five hashes are in `references/compact-delivery/issue-14-selective-gain.json`.
- Next actions in the dedicated chat: verify checkout/branch ownership, read
  `AGENTS.md`, current Obsidian guidelines, `docs/development.md`, the release
  baseline and the issue. Inspect the pre-game state and screen layout before
  placing glyphs. Move the issue to In progress only when implementation starts.
- Changed game bytes require a new version, relevant NTSC/PAL display checks,
  exact tested ROM/hash/source commit and a testable prerelease. Preserve 1.0.0;
  the current `make verify` intentionally rejects changed release bytes.
- This parent cleanup chat stops editing the shared checkout after the fork.

## Implementation and verification

- `src/game/start_hints.asm` provides the two-line block at x=168, y=8/16.
  `presentation_prepare` calls it after the original dirty upload. The normal
  active path returns after a visibility guard, without extra VRAM traffic.
- Source overlays reuse bypassed diagnostic/mapper bootstrap extents. The old
  SCREEN 2 initializer is unreachable from native cold loading and cleared to
  retain the complete Normal 32 KiB cartridge (24 bytes of final padding).
- Per-page igloo font slots have their six-byte keys invalidated. The check
  guards against live NAME aliases while loading the font and against reads
  from the retired initializer; both pages restore renderer-owned NAME bytes.
- Candidate: `v1.0.1-rc.1`. ROM SHA-256:
  `d648cd3b1ffc8aaa4bc282a8f17f1aa49029f6d73a961bd585b39265a212490e`.
- All five identities and qualification counts:
  `references/compact-delivery/issue-49-start-select-hints.json`.
- Sixteen unit checks passed. C-BIOS MSX1 NTSC/PAL keyboard routes cover all
  four variations, start, movement/jump, return to selection and restart.
  At matching coherent states, 2,328 NTSC and 2,571 PAL displayed pictures
  match 1.0.0 outside the pre-game text block; active pictures match fully.
- Bounded-route cadence differences are -0.319% NTSC and -0.797% PAL. These
  are not fresh full-density or hardware timing claims. Owner play/listening
  and physical acceptance remain pending; stable 1.0.0 is unchanged.
