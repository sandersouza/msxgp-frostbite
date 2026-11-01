# Issue13 — scoring, progression, reserves and variations

Issue: https://github.com/sandersouza/msxgp-frostbite/issues/13.
Dependency: accepted issue12/v0.0.5-hazards. Scope: exact original arithmetic,
progression, per-player six-byte records, reserves, console selection and
terminal/reset behavior in all four variations. Definitive presentation is #14;
whole-game/hardware acceptance remains later work; legacy deletion remains #17.

## Ownership and delivery state

Exclusive owner: `Frostbite — ISSUE #13`, thread
`01a197d6-373a-7f30-9389-070dc5ac992b`, Frostbite project
`0fd5a899-599e-40d4-988e-46b3d31433dd`, shared checkout
`/Users/sandersouza/Developer/msx-gamePorts/frostbite`, branch
`codex/feat/13-scoring-progression`, base
`b0d8fe206f46106e20ba5b3df43297667b3c08f3`.

Complete raw sealing, independent review/fix checks, runtime integration,
exact-head/main CI, clean-main rebuild and all four public release downloads
pass. Final receipt-only integration and issue closure remain the terminal
operational actions. Issue13 remains In review until they pass. No successor
owns the checkout yet; this chat retains all pending source-file ownership.

Prepared successor: `Frostbite — ISSUE #14`, fork thread
`01a198a2-9ef4-77d2-b114-c5f107a205c4`, explicitly assigned to Frostbite project
`0fd5a899-599e-40d4-988e-46b3d31433dd`. Its readback is idle with the correct
shared checkout. No follow-up prompt or writing permission has been sent.
Do not create a duplicate or start it before the final exclusive transfer.

## Exact candidate and original

- Local immutable build: `outputs/progression/build-issue13-b/`.
- Build source: `ac146a7c82bd5ab77a5dff2deb5d5452a0478c99` (clean).
- ROM: `frostbite-0.0.6-progression.rom`,4194304 bytes,ASCII16.
- SHA-256: `1223931972bd7e0ec02a8c66805cb30ac0defaad1abd71dd67c9c8a7746be5f6`.
- Standard3.579545MHz MSX1,64KiB RAM/16KiB TMS9918-family VRAM; no expansions.
- Original4096-byte ROM SHA:
  `cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834`.
- Banks: resident12416 bytes,assets13088,native10240,contact239,total256.
- Existing v0.0.5 ROM SHA remains
  `37beb4d58bfc6566ba064ff59d48118ce6bc70655f92dcc9695cb534a88bfd93`.

## Verified evidence and reproduction

[Technical contracts](../scoring-progression.md),
[command checklist](../progression-checklist.md),
[source route receipt](../../references/progression-source-result.json),
[capture configuration](../../references/progression-config.json) and
[release/human checklist](../releases/v0.0.6-progression.md) record the scope.
Original captures/disassemblies/derived tables and complete raw streams remain
local/ignored, with their committed producer identities.

- Eight new source routes plus eight independent full CPU/RAM/TIA/RIOT/input
  replays:21468 intervals, all four variations. Progression requires real
  construction→door→bonus→initialized next level. Exhaustion requires actual
  losses, both-empty terminal and real Reset/recovery; alternating exhaustion
  observes seven exact record swaps.
- Twelve current-ROM input-only native routes:24820 CPU/all128RAM checkpoints,
  including all four retained hazard routes. No active canonical/contact writes.
- Full paced matrix:96 route/family/layout/width combinations,198560 logical
  checkpoints and182308 completed frames, every pixel compared. NTSC peak49732
  of59736 cycles; PAL peak71081 of71364, minimum margin283 on advanced one-player
  exhaustion/restart PAL/layout1/width1. No dropped source steps or weakened IO,
  sprite, VBlank, mapper, stack, slot or interrupt guards.
- Fresh actual target geometry14828/max6679 cycles, interactions652/max26602,
  progression818/max20223. Controlled starting RAM is explicitly separate from
  natural routes. The primitive checker also passed816 cases/max3139 with the
  unchanged generic translator at cleanacff562; it is not a whole-game ROM test.
- Actual-Z80 pure-loop135168 cases,69649 summaries/65519 guard fallbacks,
  all65536 index/bound guard pairs, complete CPU/all128RAM and flags/ABI/heap guards.
  Fast cases compare the independent source CPU; rejected guards prove unchanged
  entry state, stopping before the original slow body. Full phases/routes test
  the integrated program separately; do not claim exhaustive slow-body execution.
  Existing shift/flag proof65536 cases remains valid with unchanged lowering.
- Fifteen stress modes/3600 frames, max45789 NTSC/64802 PAL. Fourteen intended
  runtime faults fail at the named raw CPU/RAM/pixel/spacing/sprite/guard cause.
- Host original-free suite303 tests and public staged-source policy pass.
  Current pinned arm64 environment check passes; Intel/physical remain untested.

Canonical private selections are in `outputs/progression/delivery-b-config.json`;
full original route paths are also in `outputs/progression/source-index.json`.
The complete raw-evidence seal passed at `outputs/progression/issue13-final-c`.
Its public validation is copied byte-identically to
[progression-result.json](../../references/progression-result.json), packager
`7cbcf7bdb31a6b83bd605da3b6688b5ef82cd489`. All128 selected positive proof reports
pass, including96 paced combinations. All14 independent negative controls pass
their expected detection checks separately.
Do not publish its private manifest or transitive raw evidence. Public assets
are only the exact ROM,build.json,validation.json,SHA256SUMS.

## Measured optimization and failure history

CandidateA (`895298a8d21593ab787f9d14388fa10b4090d2890c9ff5979fc304c0d186e06c`)
matched native states but failed advanced PAL timing at81673/71364. It is rejected
private research. Original CPU/native profiling identified a pure indexed
ROM→RAM write loop as the dominant cost. The source-derived pattern lowering
uses finite exact partial writes/CPU flags under X=0/safe-bound guards; all other
inputs execute the unchanged original native instruction body. It does not
replace gameplay with a high-level model or skip contact/render/source work.
RNG, input sampling and complete state order remain exact.

The micro-harness initially exposed Tcl `exit` returning/falling through;
regression tests now require explicit success return and propagated fatal errors.
Exploratory WIP captures never satisfy canonical acceptance. Natural native row0
is the cold checkpoint with zero timing; every later timed row must be positive,
and maxima are recomputed from complete raw rows.

The [single independent review](issue-13-review.md) found the same exit behavior
in inherited native/paced final guard handlers. One RED→GREEN fix pass propagates
their errors and rejects fatal markers in all128 selected positive logs. No
selected log had such a marker. Fresh repaired-harness progression-v1 native,
all818 phases, alternating NTSC11 and tight advanced-exhaustion PAL11 captures
pass; PAL11 remains71081/71364. An explicit exploratory actual-openMSX heap-fault
probe rejects the corrupt heap and writes no success receipt. Its private result
is `outputs/progression/guard-probe-b/probe.json`; this controlled fault is not
natural play or an additional human ROM. The unfinished prior seal was stopped
before producer edits and is never promoted; the complete restarted audit passed
with the repaired committed sealer. Original source/build inputs and ROM bytes did
not change, so retained positive captures are re-audited under their recorded
historical helper commits and mandatory fatal-log checks.

Advanced route input proposals were private search only. Unchanged Stella and
independent replays certify every actual checkpoint; predicted states never
replace source state. Preserve both original controller nibbles: the regular
alternating progression route can hold an inactive controller across a source
turn. `progression_native.tcl` selects the actual player atC047 every boundary;
do not rewrite original input traces to satisfy the older strict hazard encoder.

## Limits and next actions

Graphics/HUD remain synthetic/coarse and sound is absent. Exact score/reserve/
temperature state is checked automatically; it is not fully displayed. Human
manual-emulator and physical feedback remain pending and cannot be inferred
from any automated result. Complete-game acceptance is separate.

Runtime delivery is integrated by [PR37](https://github.com/sandersouza/msxgp-frostbite/pull/37),
merge `00c22d4d919e671440e0b08cd9b20a9debb319c0`. Final feature-head CI
41344848655/41344853140 and merged-main CI41345012514 pass. That clean main
passes303 host tests/source policy and rebuilds the exact sealed ROM with
identical build-input fingerprints.

[v0.0.6-progression](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.6-progression)
is published as a prerelease at exact tested sourceac146a7. Fresh downloads of
ROM/build.json/validation.json/SHA256SUMS all compare byte for byte with the
seal. The [compact delivery receipt](../../references/progression-delivery.json)
records source, CI, rebuild, tag and every asset size/hash. No private evidence,
original captures or standalone derived assets were uploaded.

Integrate [receipt-only PR38](https://github.com/sandersouza/msxgp-frostbite/pull/38)
and close13/Done first. The [execution ledger](issue-13-execution-ledger.md)
archives all decisions, verification boundaries and the single review/fix pass.
Then fork or reuse `Frostbite — ISSUE #14` in the Frostbite project, verify its
workspace and send an explicit sole-writer handoff with the actual clean main
commit, zero pending source files, exact ROM/hash and limitations. The old chat
must stop writes after transfer. Issue14 needs source-backed HUD/art/PSG/attract
work and fresh acceptance in every clock/view after ROM changes:283 cycles is
the current minimum margin, not a promise of available presentation headroom.
Keep `.legacy/seaquest/` and the verified external snapshot until issue17.
