# Issue #14 diagnostic integration and performance handoff to #39

Owner decision, 2026-11-03: return to the version before removing black masking
sprites, merge it into main, and start a dedicated performance investigation of
the supplied Atari 400/800 fan implementation.

## Exact baseline

- Issue #14 branch: `codex/feat/14-hud-psg-attract`, runtime source
  `12e204e6ecf6403fed63fd0e2f8c602ef84099a4`; documentation head before this handoff
  `266f272ab86efbfea38f15204f7b77ae4f0636f1`. No runtime changes between these.
- Existing release: [v0.0.9-performance-preview](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.9-performance-preview).
  ROM `frostbite-0.0.9-performance-preview.rom`, 4194304 bytes, ASCII16,
  SHA-256 `838b67ae6ba4c7cbed72f643f64f78b45bb404a1e43b395f36331343f6656ae6`.
- Local exact ROM: `outputs/presentation/performance-canonical-a/`.
  Seven black masking sprites remain in `src/presentation_sprites.asm`.
  No new runtime/ROM bytes are produced by this integration; no replacement release.
- A-D remain ignored under `outputs/presentation/`, excluded from main. B is no
  longer the selected baseline. Do not delete those experiments or promote their
  aligned crop, whole-enemy-row tiles or enemy sprites. Player tiles remain on hold.

## Verification and limits

Fresh 501 original-free tests and public-source policy pass. Independent targeted
review of runtime integration and evidence found no blocker to this explicitly
limited diagnostic merge: all 8917 sealed private files and four public release
assets match their recorded hashes. This is not a new exhaustive instruction
review or emulator qualification. Existing graphics/native/audio evidence and
failed timing measurements remain linked in `docs/presentation-performance.md`
and `docs/presentation-active-speed.md`; historical seals are not rewritten.

Original speed is NOT achieved (approximately 28 active NTSC updates/s).
Deadlines, skipped VDP frames and possible tearing remain failures. Full combined
routes/views/controller/PSG, listening and physical acceptance remain unapproved.
#14 remains open/In review rather than claiming its original DoD passed. #39 owns
performance corrections; #15 remains independent final timing qualification and
#16 full-game/hardware acceptance. This owner-authorized scope split overrides
earlier instructions forbidding merge/handoff until all #14 gates pass.

## Successor and exclusive ownership

- Issue: https://github.com/sandersouza/msxgp-frostbite/issues/39
- Dedicated chat: `Frostbite — ISSUE #39`, same Frostbite project and checkout
  `/Users/sandersouza/Developer/msx-gamePorts/frostbite`.
- Successor branch: `codex/fix/39-atari800-performance`, created from verified
  merged main by the successor. Parent must finish integration and all pending
  tracked files before messaging the child. After that transfer, #14 stops edits.
- Local-only input: `references/roms/frostbite_atari800.car`, 8208 bytes,
  SHA-256 `e3fc0fd44748810def7f3313720ed65f320624ec1cc832d087d983d00e947243`.
  Author/version/mapper/license and actual speed remain unverified research tasks.
- Atari 2600 source remains mechanics authority. Identify Atari-specific hardware
  advantages separately from portable algorithms; never assume fan-port fidelity.
- Next: inspect CAR identity/provenance, find source if available, establish a
  reference emulator and measure scheduling/rendering, then propose and validate
  a bounded native MSX optimization against the exact masked baseline.

Keep original ROMs/disassembly/generated assets ignored. Publish newly testable
ROM versions with hashes/source and human tests under the standing policy, unless
the owner explicitly requests a local-only diagnostic. No legacy cleanup (#17).
