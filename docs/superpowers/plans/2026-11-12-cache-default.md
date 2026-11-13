# AP — remove redundant default cache selection

**Stopped by owner after v26 on2026-11-12.** Preserve WIP and resume only on
request; see docs/handoffs/issue-42-owner-stop-after-v26.md. The owner prefers
removing the left stripe/enlarging the visible playfield and adding
`Activision - Retroworks` in the next round. No full-height stripe implementation.

Continue autonomous Issue42 from the published/sealed v26; same root writer and
checkout. Preserve all214 parent sources and67 prior evidence roots, original
source CPU/RAM/mechanics/input/PSG/graphics and the approved lower-left closure.
No new memory, mapper change or presentation shortcut.

The single active NTSC bear long gap is picture214/source318→320. A fresh passive
baseline reproduces all five v26 buffers. It observes two identical352-cycle
default selections inside this cache lookup. The caller already validates PAGE
and selects way0, then constructs the key without changing way/pointer/pattern
base. The intervening inherited l_eligible call preserves that selection. The
callee repeats the default before its existing scan entry.

- [x] RED native trace regression for at most one default per cache lookup.
- [ ] Independently verify the call-site invariant, side effects and IRQ/PAGE
  stability. Keep the standalone public lookup unchanged.
- [ ] One guarded caller-operand patch to the existing scan entry; exact v26
  rollback, no allocation. Measure whole bear NTSC before promotion.
- [ ] Native differential/IRQ and four whole-route/landing/foreground/passive
  measurements; complete relevant clean qualification and exact-source CI.
- [ ] If useful, update the historical workbook and publish a new exact-ROM
  prerelease/WebMSX/human tests, then seal evidence and continue remaining spikes.

Uniform/all-level30FPS remains open. A local352-cycle saving is not an FPS win
until the whole route confirms it. Human testing is separate from source/native,
emulator and physical hardware acceptance.
