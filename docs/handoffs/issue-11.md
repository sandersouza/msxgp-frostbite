# Issue 11 handoff — exact floes and build-and-enter loop

Issue: https://github.com/sandersouza/msxgp-frostbite/issues/11
PR: https://github.com/sandersouza/msxgp-frostbite/pull/33
Release: https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.4-buildloop

## Ownership and completion gate

Issue 11's chat owns the shared checkout until integration, release download
verification and its explicit exclusive-ownership transfer. Do not start #12
from this document alone. The final live receipt in issue 11 records merged
main/CI/release verification; the parent sends the current main commit and
ownership transfer in the dedicated Frostbite issue 12 fork. No other chat may
edit concurrently. Routine successor work is already owner-authorized.

Branch: `codex/feat/11-floe-construction`; tested source commit
`81619c058e04a644564404ec4bd8582ac46cee41`. The approved design and project workflow remain authoritative.
At transfer there must be no pending source edits; any exception must name
its owner and files explicitly. Preserve `.legacy/seaquest/` and frozen old
release/issue 10 outputs. Final legacy deletion remains #17.

## Exact artifact and evidence

- ROM: `frostbite-0.0.4-buildloop.rom`, 4,194,304 bytes, ASCII16.
- SHA-256: `c298a0311eb263b4e2fdc5ce490d29880ac27ebbc92f53e492f17b7f5747d600`.
- Private final bundle: `outputs/floes/issue11-final/`.
- Public compact result: `references/floe-result.json`.
- Validation SHA-256: `8e67d622f1b9836ecffbf9f6d296708416c6c5365b20c8ea63d12a17fc04501a`.
- Private evidence manifest SHA-256:
  `e07ce869afa53f9640a40215b7691c543c2643ba2a82ec2752898447575ba440`.

Original ROM authority remains
`cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834`.
The canonical electrical catalog is `outputs/floes/catalog-issue11-b/`,
producer `07195b0`. Catalog-A is interrupted exploration, never acceptance.
The observer is pinned Stella 7.0/`d55b1aec`, focused patch in tools/, binary SHA
`1b84b99fe8554405b1138fb63de4ef1aa56c7730a43a7e24f2349239f428e297`.
Original route `outputs/floes/natural-issue11-a/` and strict replay
`outputs/floes/natural-issue11-replay-v2/` preserve every serialized byte.
Different restore batching resets upstream jitter metadata; do not mask it.

All final target captures are fresh/clean at the tested source commit:
4497 generic CPU cases, 1793 carry-fused cases, 1368 geometry cases, 86 actual-key
whole-ROM boundary cases, RPC natural 2254 states, and actual paced natural
2254 states each in NTSC/PAL (2253/1886 completed frames, zero pixel errors).
Stress: 13×240 frames plus 8 negative identities. All raw paths and hashes are
closed by the private manifest; never upload it or original captures.

## Target ABI and limits

Standard 3.579545 MHz MSX1, 64 KiB RAM, 16 KiB TMS9918-family VRAM, built-in PSG;
no expansions/turbo/disk/extra audio. Normal banked cartridge ROM is allowed.
The released cartridge contains native Z80, not a 6502/TIA interpreter.

`visible_step` maps F019→F476 effects, then existing native F476→F019 executes.
Canonical game RAM is C000..C07F. Source D0/SPFF is required; preserve all 128
RAM bytes and logical A/X/Y/P/SP. Input samples remain at F5AD before 81 increment
and F630 after it; preserve all physical registers, slots, PSG15/PPI-C and DI.
The new diagnostic preserves INPT4/5 bus lowbits 0C for either selected player.

Contacts use actual control bytes 9C/9D (not 9E), P0X0..159, floeX0..159,
6 poses×19 shifts×2 reflections and normalized Y45..77/outside sentinel. Full
58-byte near records retain both 228-bit latch channels; bit 6 can differ from
its sentinel. BF bit7 blanks new samples; ED remains sticky. Do not revive
raster overlap, coefficient convolution, assumed horizontal classes or all-Y
bit 6 factorization. The complete matrix proved those simplifications unsafe.

Tables occupy 177 banks/2,861,024 useful bytes (2972 records, 5507 rows, 444 profiles).
Current image uses 256 banks/4 MiB. Banked reads restore bank 2 before native core
ROM data access. Source-owned scratch/cache is C780..C786; frontend blank-row
cache is CB00..CB02. Existing renderer metadata remains CB70..CB77. Do not
reuse these ranges silently. New model/query/record formats are documented in
`docs/floe-loop.md`; whole-frame checks use actual mapper/input/native work.

Timing remains tight: dense inverted PAL 71132/71364 (margin 232 cycles), natural
PAL 70205 (margin 1159); NTSC natural 44074/59736. Every ROM/input/renderer change
needs fresh full-density and paced-natural checks. Preserve 29 cycle VRAM data
spacing, at most 4 sprites per line, VBlank commit, source counts and stack/heap.
Do not hide work with a reserve or drop source simulation.

The optional unique-predecessor carry fusion is enabled only for the new
build; older movement ROM remains byte-identical `31bb62e4886c8baf361584ce6a140fc05e34c77be15642780e23ad5d5fdb9f82`. Renderer
blank-cache skips only already empty fixed hazard name rows, invalidates on
nonempty input, and clears both pages before future skips. Its corruption
negative is required. SAT termination precedes display enabling. Sprite pixel
oracle paints the diagnostic header underneath sprites.

## Scope and successor

Real floe acquisition/build/rearming/reversal/temperature/entry are delivered.
The original natural route builds, enters and initializes level 1; it loses 3
reserves and finishes with 0. It uses no source/contact injections or disabled
source hazards. Source ordering permits BOTH a block award and a requested
temperature-loss phase when landing coincides with temperature reaching zero.

Graphics/HUD are synthetic and audio silent. Full hazard/shore acquisition,
RNG/behavior coverage, progression, presentation, full-game and physical/manual
acceptance are not inferred. Controlled geometry reports 1081 full actual-original
phases and 287 explicit neutral odd/shore cases; the latter are NOT full hazard
acceptance. Inactive D8=0 still yields odd-window ghost contacts near X0 in the
original. Implement and validate them in #12. Manual/physical feedback is pending.

Next: use or fork a separate chat titled `Frostbite — ISSUE #12`, verify its
Frostbite project/workspace, move #12 to In progress and use a scoped branch.
Read the local issue copy/approved design before changing code. Extend actual
source acquisition for hazards/fish/bear/sticky shore and validate RNG ordering;
retain all source channels, priority and original frame ordering. Measure ROM
capacity and full pipeline costs before selecting a lookup/native method.
Current table format is simple/lossless rather than globally size-optimal;
free space and PAL timing are real constraints, not permission to approximate.
Publish every next testable ROM version with exact tested bytes/source/SHA and
human test expectations. Finish #12 with its own PR/release/handoff and another
exclusive fork. Never implement it inside issue 11's chat.
