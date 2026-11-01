# Issue #10 handoff — native input and movement diagnostic

Issue:https://github.com/sandersouza/msxgp-frostbite/issues/10.
Branch:`codex/feat/10-native-movement`; base
`94bdfb6373be06ab241fcd2adfccc80c76d0f8f7`.
Issue10 retains exclusive checkout ownership until its explicit transfer.
Independent review, exact-head CI, merge, release/download and Done readbacks
remain pending at this checkpoint; those steps are required before transfer.

## Frozen bytes and evidence

ROM producer:`64c2cec6d37e5b988b0b86bc1d57836dbe43498a`.
ROM:`frostbite-0.0.3-movement.rom`,262144bytes,ASCII16,
SHA-256`31bb62e4886c8baf361584ce6a140fc05e34c77be15642780e23ad5d5fdb9f82`.
Frozen private evidence:`outputs/movement/issue10-final/`.
Prepared immutable release package:`outputs/releases/v0.0.3-movement-reviewed/`.
Neither directory may be overwritten with changed bytes. A later auditor/docs
commit does not relabel the tested producer. Public compact evidence is
[references/native-result.json](../../references/native-result.json); operations
and required human checks are in [native movement](../native-movement.md) and
[release notes](../releases/v0.0.3-movement.md).

Verified against independent original execution:4497generic CPU cases including
all101 published mechanics cases;1793specialized full-phase/cold/continuous
cases;1354actual keyboard/two-joystick cases for each CPU path,2708samples each.
F5AD is before source81 increments; F630 is after it. Return-PC/phase, full logical
CPU/all128RAM, stack mirrors, peripheral/slot/DI preservation, poisoned mirrors
and continuous target-owned state are checked. Port2 fire inversion fails.

Eleven240-frame captures cover every layout/width on NTSC/PAL, actual F3/F4
held/repressed transitions and focused counts0/1/2. Every presented pixel, SAT,
source state, adapter, visible preparation invariance,29-cycle VRAM spacing,
four slots, source counts, consecutive frames, VBlank commit and stack/heap
is checked. Five pipeline corruptions reject for their intended gates.
Minimum measured margins:NTSC10736/PAL1227cycles. These are finite automated
fixtures, not a global future-state/performance or physical acceptance theorem.

```sh
make environment-check
make source-check
make test
make ci-verify
make render-build
.venv/bin/python -B scripts/movement_delivery.py audit --frozen outputs/movement/issue10-final
.venv/bin/python -B scripts/movement_delivery.py package --frozen outputs/movement/issue10-final
```

The original4096-byte ROM remains ignored under references/roms/frostbite.bin,
SHA-256`cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834`.
Full source disassembly, source-derived native assembly/data, CPU proof ROMs,
OMR snapshots and raw source/capture states remain local/ignored. Package only
the five explicit human release files. Old v0.0.1/v0.0.2 binaries are unchanged.

## Contracts and limitations

The runtime implements post-visible F476→F019, not F019→visible kernels→F476.
Contacts are explicit B0..B9/ED stimuli; EA=0 at declared E4 row values supplies
ground contact independently of X. Do not mistake that for natural landings.
Visible preparation, RNG/palette work at FAEA, other visible side effects and
TIA acquisition need source-phase reconciliation. CPU chains retain their own
state, but omit that source-frame environment by declaration.

The generic compiler supports named observable slices and SP86..FF. The fast
whole-phase compiler requires D=0/SP=FF at F476; F000 executes real CLD/clear.
Only F019 exposes CPU state. Finite X/D/C domains and NZCV/IY liveness follow
real bounded call contexts; IY indexes require proved non-wrapping RAM. Source
JSR return words still reach RAM at context-proved locations; internal SP is
implicit. TSX rejects, TXS only occurs in the proved top-level clear, and a phase
exit cannot retain call contexts. No source-address gameplay substitutions or
6502 interpreter are used. New entries/preconditions require renewed proof.

The static synthetic atlas/name-row strategy buys CPU time with256KiB ROM while
retaining64KiB RAM/16KiB VRAM. Only inactive-page dynamic slots may change.
Logical coordinates remain canonical. Original graphics prepared in9 are still
offline: the24-pixel original bear and exact source raster mapping do not fit
this synthetic presentation by inference. Do not use its shapes/grid/HUD as
collision authority. It has no audio engine or ordered source-bus/audio proof.

An early integrated candidate needed108172PALcycles; incremental tile caching
still exceeded budget. Only the final immutable-atlas pipeline passed. The307
cycle-over-budget width/layout case was rejected before the last flag-capture
optimization. Rejected/prototype outputs are local investigation, not acceptance.
Every future core/input/renderer/asset change must remeasure full active density;
there is no synthetic10k reservation to spend. Late levels, natural collisions,
full routes, expanded slots, manual viewing/listening and physical verdicts remain
pending. Keep evidence classes separate.

## Successor ownership

Start/reuse a separate `Frostbite — ISSUE #11` fork in project
`0fd5a899-599e-40d4-988e-46b3d31433dd`, cwd
`/Users/sandersouza/Developer/msx-gamePorts/frostbite`, only after10's delivery.
Move11In progress and use `codex/feat/11-<slug>`. Native post-visible routines
already execute much of the future central loop: do not replace their mechanics
with approximations. Issue11 owns floes/build/entry/temperature and the real floe
contacts needed for its natural route; issue12 owns RNG/hazards/full TIA-derived
semantics. Full progression is13, original HUD/audio/attract14 and acceptance15/16.

Transfer clean merged main, exact source/binary/report identities, no pending
implementation files and these remaining constraints. The prior issue chat stops
all checkout edits after transfer. Preserve .legacy/seaquest and its verified
external snapshot; final legacy deletion is17 after replacement acceptance.
