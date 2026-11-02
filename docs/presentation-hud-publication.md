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

Private ROM SHA-256:
1a9af5e527faa6ac2200c0d635f6dc3eb0f12fbe210a6c102be230a946f594ce.
It passes all 2,115 original full-scene/physical ownership/active-byte cases;
controlled preparation still reaches 635,803 cycles. The 120-frame keyboard
probe still fails: maximum 631,206 busy cycles, 22 overruns and 51 skipped frames.
Cold header work falls from 230,140 to 195,959 cycles; the start transition from
147,206 to 113,025. The new default control remains byte-identical at
0b98f3cb89e99f6e79ad9f1a3fb237c2cbfadebcd5759025a123ce33e09fcf78.
The host suite passes 461 original-free tests.

Further measured work remains: the header rebuilds the same full glyph tuple
three times, then masks inactive pairs for each row band. A bounded temporary
table can pack each column once and derive the three exact keys. At the start
transition twelve keys change, while only six resulting PGTs change and all CGTs
remain identical; fragment aliases and independent PGT/CGT publication may help
after their equivalence is proved. The current header constructor also reads
full glyph fragments before copying only the required row spans.

These are private research artifacts. PSG, hard complete-frame budgets,
combined route acceptance, final review and human-ROM release remain pending.
