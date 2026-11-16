# Frostbite — ISSUE #49

- Issue: https://github.com/sandersouza/msxgp-frostbite/issues/49
- Project: Frostbite, `/Users/sandersouza/Developer/msx-gamePorts/frostbite`.
- Base: `main`, `964d6a2639019cec014ece343084c6fe70169076` (PR #48 merged).
- Prepared branch: `codex/enhancement/49-start-select-hints`.
- Scope: show exactly `F1: START` and `F2: SELECT` on consecutive rows in the
  upper-right corner before gameplay. Align both keys, colons and action text.
  Standard MSX glyphs are acceptable. Hide/restore the area as gameplay begins;
  keep the hints visible while selecting variations with F2.
- State: issue created and Ready; implementation has not started. Classification:
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
