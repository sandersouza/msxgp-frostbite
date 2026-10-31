# Issue #5 handoff — managed tools and first MSX1 diagnostic

Issue: https://github.com/sandersouza/msxgp-frostbite/issues/5
Branch: `codex/chore/5-macos-toolchain-scaffold`.
Base: `5f2cb273ce80d0a6e37f4bc4aaff13f09ce47ff4` (issue #4 integration).
Environment commit: `20f3c2e65994eb895c51f65cbfea774b82e17f87`.
Scaffold/runtime checkpoint: `0ed3aa72f8d79b7d0000108c19aab82937287f77`.
Final reviewed head/integration: this issue's delivery PR; the release tag and
attached build.json identify the exact final tested source commit.
Release target: https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.1-diagnostic

## Delivered scope

- Source-pinned native macOS sjasmplus/DiStella/DASM under a new managed
  .tools/frostbite subtree, receipts, setup/check/dry-run and preserved venv.
- A deterministic 16 KiB Normal/no-mapper SCREEN1 diagnostic, with ready
  signature, heartbeat, cursor/joystick1 directions, SPACE/fire readout and
  PSG tone while held. No Atari game code/assets or Frostbite gameplay.
- Bounded fresh openMSX functional checks, identity/profile gates and rendered
  preview; package gate requiring matching clean source/build/smoke identities.
- [Command-by-command checklist](../toolchain.md),
  [diagnostic checkpoint evidence](../../references/diagnostic-baseline.json)
  and [release note template/human tests](../releases/v0.0.1-diagnostic.md).

ROM: `frostbite-0.0.1-diagnostic.rom`, 16,384 bytes.
SHA-256: `d46320aec4b148c3b885d54de051bc078539b65a7a8bf739bb4e9e956c2028ca`.
Target: standard-speed MSX1, 64 KiB RAM, configured16KiBVRAM, TMS9918-family,
built-in PSG; no expansion/turbo/disk. Only NTSC TMS9918A automation is recorded.

## Verification and reproduction

```sh
bash scripts/setup.sh --dry-run
bash scripts/setup.sh
bash scripts/setup.sh --check
make test
make build
make smoke
.venv/bin/python -B scripts/smoke.py --screenshot
make package
```

Packaging requires a clean checkout and build/smoke from the current commit;
commit changes and rebuild/retest before packaging. The package is staged in
a fresh outputs/releases directory; latest-package.json names the exact files.
The PR uses Refs#5 so closure waits for the published-release verification.
After integration, rebuild/smoke the clean integrated commit, publish the exact
ROM/metadata/checksums/notes, download and compare before closing/Done.

The arm64 clean source clone was created at
`/tmp/frostbite-issue5-clean.4dyb8f/repo` with no original Atari input or inherited
tool/environment cache. It built all three pinned assemblers and new venv,
passed setup/check/repeat and then test/build/smoke. At the committed runtime
checkpoint it passed47 original-free tests; package and long-version-path
guards bring the current suite to51. Fresh-clone and primary ROMs have the
same hash above. Existing primary .venv package lists and both inherited and
managed executable hashes stayed unchanged across repeated setup.

Smoke verifies loaded-profile RAM, TMS9918A, standard3,579,545Hz Z80 and only
the expected cartridge extension, plus enabled SCREEN1/title/readouts,
heartbeat, UP/release/SPACE/held-edge/release and PSG period/volume on/off.
A booting fault-injection ROM with the heartbeat increment removed was rejected
specifically as stopped heartbeat; stale latest-success evidence was removed.
The actual normal-speed, frameskip0 screenshot was inspected and displays the
diagnostic correctly. Human listening, physical machines, Intel/Rosetta and
automated PAL validation remain pending.

## Important implementation details

- Source pins, not package-directory/banner guesses, identify tools. DASM's
  v2.20.17 source still prints2.20.16. Receipts contain executable hashes and
  architecture; wrong/dirty source or modified binaries are preserved/rejected.
- Setup creates .venv only if absent. Missing py65 is installed; a conflicting
  existing version is preserved with failure. Host CLT/Homebrew/Python and
  openMSX/Stella were already installed; cold OS/Homebrew/emulator install was
  not exercised. Intel support is prepared, not certified.
- DiStella has both50-byte filename and132-byte whole-argv buffers. Reference
  rebuild stages verified input.bin and a short executable symlink; setup
  version probing runs a short basename in the binary directory. Both have
  regression checks. Reference defaults now use verified managed tools only
  after canonical validation; explicit overrides still work.
- An isolated copied C-BIOS profile needs explicit verified bundled-firmware
  paths and the msxconfig2.dtd systemID. No BIOS bytes are embedded/published.
  OPENMSX_USER_DATA and explicit settings isolate user caches/preferences;
  HOME/CODEX_HOME are not replaced and settings are not saved.
- openMSX exposes a128KiB raw VRAM debug buffer even for this MSX1. The actual
  configured16KiB comes from validated loaded XML/TMS9918A, not debugger size.
- BIOS WIDTH centers its logical text line. Smoke locates the title margin
  before checking status cells. Accelerated raw captures can show an old blank
  framebuffer; screenshot mode uses normal speed/no frameskip and was viewed.
- Diagnostic GTSTCK/GTTRIG input is a hardware check, not the native raw-input
  adapter required by #4. No gameplay state/flags/collision/RNG acceptance is
  implied. Full-emulator reference alignment and geometry still belong to #7.

## Continuation and preservation

Original ROMs/full disassemblies remain local/ignored; #4's101 CPU probes and
source contracts remain research evidence. The Seaquest quarantine and
verified external snapshot were not removed; final cleanup is #17 after
working replacements pass. Do not stage the tree wholesale or reuse old
Seaquest success as Frostbite proof.

After release verification and integration, close #5/Done, then fork into a
dependency-ready successor, normally #6 synthetic CI/tracking. Verify project,
workspace, main/dirty state and current GitHub delivery first. Transfer issue,
commit, artifact hashes, ownership, limitations and next actions; this issue's
chat stops editing the shared checkout after dispatch.

Every later changed testable ROM needs a new release/version with exact tested
bytes, source commit, limitations, next work and concrete human tests. Never
silently replace the published diagnostic attachment.
