# Owned HUD publication under development

These Task 3 optimizations preserve the source-derived six-byte tile grammar,
complete physical PGT/CGT bytes, inactive generations and CPU NAME positions.
They do not establish a complete-frame deadline.

The footer has 22 exclusive cells per generation. Its finite program and all
tile records occupy the same mapped asset bank, asserted at assembly time.
The publisher validates page/coarse/phase once, advances its owned pointers,
compares all six metadata bytes and streams complete PGT/CGT records directly
from ROM on a MISS. It publishes the key afterward. Zero descriptors retain the
background already prepared by the caller.

Actual Z80 footer checks cover all 16 programs, both generations, repeated
programs, dirty selectors and invalid page/coarse/phase: 78 stateful operations.
The proof compares the whole 264-byte footer pool, both CPU NAME pages, 16 KiB
VRAM, carry/fault and RAM/ABI/device guards. Maximum 30,436 cycles includes RPC.
The game integration passes all 2,115 original full-scene and ownership cases.
In the keyboard probe, cold footer work falls from 49,867 to 23,442 cycles;
the start transition falls from 36,764 to 18,703.

The header still has its thirty exclusive bank0 cells. Its driver validates the
page once and computes the NAME, physical ID and metadata pointer once per row.
An internal resolver entry receives that prevalidated role; the public resolver
retains its existing checks. Six-byte comparison, full constructor output,
offscreen upload and metadata publication are unchanged. A separate actual Z80
component passes 1,212 operations, including first/last slots of all six groups,
whole metadata/VRAM and unchanged NAME pages on the internal resolver path.
Its constructor stub remains separate from the real constructor and full-scene
proofs.

The TEMPLATE profile now packs each header column's four glyph selectors once
in a bounded 43-byte temporary table (E620..E64A), then derives the exact three
six-byte band keys. It preserves every original selector, color and fragment
phase. The independent actual-Z80 check passes 3,295 cases: every byte value of
each selector, level boundaries, all colors, every column/band and invalid
inputs. Guards cover the complete table, generated keys, source RAM, ABI, heap,
VRAM, stack, interrupts and mapper/slot state.

A separate header constructor reads only the source glyph rows consumed by each
band. It still validates all four glyph IDs and the fragment phase before
writing. Its actual-Z80 typed-constructor check passes 4,718 cases across all
existing kinds, including invalid unused glyph IDs; expected whole PGT/CGT bytes
are unchanged. On identical valid keys, mean savings are 243, 508 and 440 cycles
for bands 16, 17 and 18 respectively. These are component measurements, not
complete-frame acceptance.

Private ROM SHA-256:
83799b853ff55fb17956746285b205bb5674e20dc110ff3ca22a2e99ffc6639b.
It passes all 2,115 original full-scene/physical ownership/active-byte cases;
controlled preparation still reaches 612,756 cycles. The 120-frame keyboard
probe still fails: maximum 605,274 busy cycles, 22 overruns and 50 skipped frames.
The new default control remains byte-identical at
0b98f3cb89e99f6e79ad9f1a3fb237c2cbfadebcd5759025a123ce33e09fcf78.
The host suite passes 464 original-free tests.

These are private research artifacts. PSG, hard complete-frame budgets,
combined route acceptance, final review and human-ROM release remain pending.
