# Issue 12 — original-clock hazards and interaction handoff

Issue: https://github.com/sandersouza/msxgp-frostbite/issues/12. Delivery PR:
https://github.com/sandersouza/msxgp-frostbite/pull/35. Dependency11 was integrated
at base `d6f214fd8923e11eea5cd3f71bdbb0cdb7ec93f7`.
Exclusive owner is `Frostbite — ISSUE #12`, thread
`01a19650-5f24-78c3-b4cf-3b2942a756ac`, Frostbite project
`0fd5a899-599e-40d4-988e-46b3d31433dd`, shared checkout
`/Users/sandersouza/Developer/msx-gamePorts/frostbite`.

## Artifact and evidence

Branch: `codex/feat/12-hazards-collisions`. Exact tested source:
`e83569dfde46f9bb6f39ea05817d6e3204333a54`. ROM
`frostbite-0.0.5-hazards.rom`, 4,194,304 bytes, ASCII16, SHA-256
`37beb4d58bfc6566ba064ff59d48118ce6bc70655f92dcc9695cb534a88bfd93`.
Target is standard-speed MSX1, 64 KiB RAM/16 KiB VRAM, TMS9918-family VDP;
no expansion, turbo, disk or extra sound hardware.

Immutable local bundle: `outputs/hazards/issue12-final-e/`. Upload only its ROM,
`build.json`, `validation.json` and `SHA256SUMS`. Never upload its
`private-evidence.json`, source ROMs, original/derived captures or generated
disassembly/assets. [Compact result](../../references/hazard-result.json),
[technical proof and commands](../hazard-collisions.md) and
[release/human tests](../releases/v0.0.5-hazards.md) describe the accepted scope.

Complete source domains total50,289,350 cells; independent physical decoding
checks16,776,480 leaves. The4MiB image uses239 contact banks, with resident/
assets/native usage12,416/13,088/8,192 bytes. Geometry14828 uses every actual
original collision channel, with no neutral substitutions; controlled652
covers both players/all rows/kinds, fish afterF7=0C, ground/air, bear2/3,
water/temperature and all256 RNG seeds. The clean actual-Z80 shift unit has
65,536 cases. All32 natural route/clock/layout/width pairs match every CPU/
128RAM checkpoint and24,604 completed frames; fifteen stress modes add3600
frames. Eleven real runtime faults are detected at their intended witnesses.
Tightest PAL margin645 cycles; crowded NTSC/PAL peaks49,545/64,802. VRAM
spacing29+, four sprite slots, VBlank commits and device/stack/heap guards pass.

Source roots: `outputs/hazards/catalog-{edge-b,ordinary-a,shore-a,aliases-a}`,
`outputs/floes/catalog-issue11-b/`. Observer:
`outputs/hazards/observer-check-clean-d/check.json`, pinned binarySHA
`6abd8c64821b4395373e1904698b3332b901caf9b3aa91a8d2067fe89dda064d`.
Natural original/replay roots are `route-/replay-bear-{chase,refuge}-a`,
`route-/replay-fish-envelope-c`, `route-/replay-threat-push-a` under
`outputs/hazards/`. New native/paced/stress evidence uses suffixD; the sealed
private manifest records every exact path/hash. Failed candidates and stopped
seal attempts are historical and never replace this bundle.

## Preserved contracts and limits

The ROM runs native Z80. Actual original-clock lookup supplies all odd/floe/
shore channels; NUSIZ0 draws one copy and preserves invisible edge ghosts.
Only a negative shore sample overwrites sticky ED. Source call/event ordering,
logical CPU flags and all128 canonical bytes remain authoritative. Scratch
C790..C79F is separate; restore bank2 before entering the core.

New compact flag lowering removes only outputs proved dead by contextual
liveness, with complete shift values/flags and whole-ROM proof. Hardware/
indexed aliases retain their old lowering; transfer/comparison operand and
IY paths remain intact. The shared old translator and published0.0.4 ROM
identity remain preserved. The generated optimized core is intentionally
different, with observable behavior proved against the original.

Earlier PAL failures at71,404(default view) and74,816(alternative view) caused
measured repairs and the expanded matrix. Never accept default-view-only
timing, suppress source steps, loosen budgets/29-cycle spacing or remove
original contacts. Source/backend/catalog helpers remain frozen; changed
dependencies require fresh capture or explicit unchanged-dependency proof.
Real keyboard controller selection is sourceC7 atC047, not graphic pointerC007.

Graphics/HUD are synthetic, audio silent, and clipping/art remain presentation
work. Whole-game/progression, manual-emulator and physical acceptance are
separate; pending owner feedback is not a failure of these automated gates.
The copied Seaquest tree remains ignored/local with its preserved snapshot;
only issue17 may remove it after replacement acceptance.

## Delivery and exclusive successor gate

At this documentation checkpoint the immutable automated package passed;
independent review, integration and release/download receipts remain pending.
The issue12 chat owns all pending documentation/delivery files. Do not transfer
the checkout or implement13 until12 has its own review, integrated PR, exact
prerelease/download verification and closed/Done status.

Then use/reuse a distinct fork titled `Frostbite — ISSUE #13`, verify Frostbite
project/workspace and clean current main, move13 to In progress and create a
scoped branch. Transfer actual integration/CI/release receipts and pending-file
ownership explicitly; the old chat stops writing. Issue13 owns score BCD,
progression, reserves, all four variations, alternating players/game-over/
restart and their boundary/natural acceptance. Routine successor start and its
next testable-ROM release are already authorized by the owner.
