# Bear Sprites Experiment Plan

> **For agentic workers:** Use superpowers:executing-plans inline; root is the only tracked writer. Steps use checkbox syntax.

**Goal:** Determine whether exact bear sprites improve full-game presentation over v0.0.17.
**Architecture:** Prepared four-sprite bear, page-specific SGT and exact tile fallback; unchanged source clock and dirty union.
**Tech Stack:** Python/Z80/sjasmplus/openMSX; artifact-tool workbook.
**Spec:** `docs/superpowers/specs/2026-11-12-bear-sprites-design.md`.

## Global Constraints

Standard-speed MSX1,64KiB RAM/16KiB VRAM,TMS9918/PSG. Preserve graphics and mechanics.
Use new ignored AE roots; every sealed AD/earlier root is immutable. Same issue42 chat/branch.

## Review Focus

Full 16-row rectangles, active SGT protection, bear/player priority, wrap/coarse
shift and mapper restoration. Do not equate lower constructor cost with a full-frame win.

### Task1: Isolated experiment and complete-route gate

- [x] Verify v17 artifact/source closure; inspect allocation and compile all bear states.
- [x] Independently compare compiled patterns/geometry and capacity decisions before runtime use.
- [x] Build only in a new ignored AE directory; run exact NTSC and expanded-PAL routes.
- [x] Measure whole cadence/gaps/landing coverage and passive full foreground/ISR, including fallback effects.
- [x] Reject or qualify based on the whole-frame evidence; preserve every result and limitation.

### Task2: Analysis, workbook and delivery

- [x] Rank optional visual adaptations by measured cost and likely visual effect; apply none.
- [x] Preserve all30 AD workbook tabs; add AE comparisons and honest acceptance scope; export/audit/view.
- [x] For a worthwhile candidate only, complete full qualification/review/rebuild/CI and exact-asset prerelease. **Gate not met: no promotion or release.**
- [x] Commit/synchronize documentation and issue42/PR43; In review, keep acceptance issues open.
