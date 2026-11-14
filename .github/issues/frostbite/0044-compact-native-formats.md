# Compact native delivery: 32 KiB mapperless ROM, MSX-DOS COM and BASIC BIN

Issue: https://github.com/sandersouza/msxgp-frostbite/issues/44

## Goal

Reduce the accepted Frostbite implementation to a complete cartridge ROM that
fits within32 KiB without a mapper, and provide genuine native `.COM` and
`.BIN` entry points for MSX-DOS and MSX BASIC. The owner accepted v0.0.30 as
stable and enjoyable on2026-11-13 and explicitly requested this successor to42.
Further speed exploration is optional work, not a prerequisite for this task.

## Accepted baseline and constraints

- v0.0.30-reference-credit-diagnostic,4,194,304-byte ASCII16 ROM.
- ROM SHA-256: e75535923a5751e3f4924dc7a3a2f762041b825efb7a5336650d35890cd3ff1d.
- Runtime9915dab1c4c431a62b68c4886cdf788b1983f774; owner-approved graphics,
  mechanics, colors, controls, PSG, lowercase credit and observed cadence.
- Standard-speed MSX1,64 KiB RAM/16 KiB VRAM,TMS9918-family VDP,built-in PSG.
  No ROM mapper, memory mapper, MegaRAM, turbo or extra sound dependency.
  Disk formats naturally require a DOS/BASIC disk-loading environment.
- Preserve published versions and local sealed evidence. Original ROMs,
  disassemblies and generated source assets stay local/ignored.

32 KiB is an engineering target to investigate, not an asserted result. Do not
truncate the4 MiB ROM, rename it to COM/BIN or silently sacrifice graphics,
mechanics or accepted cadence to claim success. Do not promise compatibility
with every original MSX1 RAM configuration;64 KiB remains the established target.

## Work

- [x] Audit occupied versus padded bytes, live versus retired code, duplicate
  assets, lookup tables and prepared rendering programs. Produce ROM/RAM/VRAM
  budgets, startup/steady-state costs and a measured feasibility assessment.
- [x] Inspect Seaquest's working Normal-ROM and COM loaders/builds as reusable
  infrastructure. Audit and adapt selected pieces; its test results do not prove
  Frostbite. Include BASIC BLOAD conventions and actual entry/load addresses.
- [x] Design and implement a compact shared runtime/payload. Evaluate dedup,
  compact encodings and startup decompression against RAM and whole-frame costs.
- [x] Build a complete <=32,768-byte Normal cartridge with no external payload
  or bank-switching hardware dependency, if the measured architecture permits.
- [x] Produce an actual native `FROSTBIT.COM` for MSX-DOS and a BASIC-loadable
  `FROSTBIT.BIN` with the correct binary header/load/end/execute addresses.
- [x] Document and verify start/reset/return behavior, slot placement, stack,
  system ownership and DOS/BASIC integration. Do not ship empty wrappers.
- [ ] Compare source state/input/audio, pixels/ownership and full-density
  NTSC/PAL cadence against the accepted v30 baseline on all relevant paths.
- [x] Publish every useful testable candidate with exact artifacts/hashes/source,
  machine/RAM/VRAM/format requirements and precise human loading/test instructions.

## Native diagnostic progress (2026-11-14)

Complete32KiB Normal cartridge, actual DOS1 COM and Disk BASIC BIN/companion
are built from runtime424aab9.721 host tests, four actual cold source/pixel/IRQ
routes,2115 original scenes,1920 density scenes,54 header transitions and9 IRQ
boundaries in both video families pass. Both disk loaders pass real DOS/BASIC
loading and exact cold RAM/VRAM checks in NTSC/PAL. Independent review found no
Critical/Important findings; minor provenance wording was corrected.

Cadence remains below acceptedv30: regular30.168/28.441 and bear28.016/24.045
NTSC/PAL. No owner cadence exception, manual listening or physical hardware
acceptance is inferred. The published [v0.0.31 native diagnostic](https://github.com/sandersouza/msxgp-frostbite/releases/tag/v0.0.31-native-formats-diagnostic) does not close44;
PR45 remains draft while recovery and acceptance continue. See
`docs/native-formats.md` and `docs/reviews/issue-44-native-formats.md`.

## Definition of Ready

Owner scope is explicit. Issue42 integration and its ownership handoff identify
the accepted source and immutable ROM. Local original inputs and automated
oracles are available. Start in a dedicated `Frostbite — ISSUE #44` fork;
only that chat may implement this successor in the shared checkout.

## Definition of Done

- A complete mapperless cartridge fits32 KiB, or a separately reviewable measured
  feasibility result explains the remaining bound and asks the owner to decide
  a material target change; do not mark an unmet size target as achieved.
- COM and BIN load and execute as native programs in actual MSX-DOS and BASIC
  emulator configurations, with documented limits and reproducible commands.
- No unapproved regression in accepted graphics, mechanics, controls, PSG or
  whole-frame cadence. Fresh evidence distinguishes host CI, emulator tests,
  owner approval and physical hardware. Hardware testing is not inferred.
- Focused reviewed PR, exact release artifacts, sizes, hashes, source revision,
  loading instructions and updated budget/handoff are delivered and integrated.

## Tracking and boundaries

Project: MSX Game Ports #7. Type: Task (native issue types unavailable).
Priority: P1. Size: XL. Initial estimate:64 hours, exploratory implementation and
verification, not a deadline; revise after the byte inventory. The repository
has no priority labels; retain `enhancement` and set project Priority=P1.
No established milestone is assigned. Do not change shared labels/settings.

Issue39 retains the unmet original-cadence goal;15/16 remain final timing,
full-game and physical qualification. Legacy deletion remains issue17. This
task may remove measured dead active code after preservation, not erase history.
