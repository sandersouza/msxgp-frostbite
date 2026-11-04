# Shared physical ice residency — issue #42

Owner-approved direction: replace architecture to preserve original graphics
and mechanics at original cadence. Routine choices below are engineering calls.
No further approval is needed for this reversible implementation and measurement.

M-C is the sealed control. N's small traversal improvement is not carried into
this first implementation, so costs isolate physical residency and NAME mapping.
Keep SCREEN2, all original state/input/audio, actors, colors, phases and viewport.

Alternatives: a permanent all-level atlas lacks a complete VRAM fit; extending
the per-page pool retains generation churn. Select shared residency across both
pages, using the existing 64 ice slots per bank. No complete-frame speed promise
is inferred from the offline semantic-miss model.

Each of eight page/row caches retains a count and up to 14 physical pool indices.
Reference counts cover both pages, including clean rows and hidden col1. A changed
inactive row releases its old list before preparing its replacement. Every new
key is acquired immediately; eviction is limited to zero-reference slots. This
also protects already prepared rows while later rows are allocated. A row's
unchanged identity retains its slot list and decoded names. Source render failure
is fatal and cannot present a partly prepared page.

Keys are exact raw pattern ID plus color. Hash lookup is bounded to 64 slots;
clock eviction is bounded to 64 probes and removes the old hash membership.
Physical metadata still holds full six-byte tag9 keys for independent checking
and enemy fusion. Old-key recovery must use the referenced physical ID's page
bit, rather than the target generation. Decoded NAME programs map local codes
through the newly resolved physical IDs; K's fixed-base decoder cache is bypassed
for these changed rows. Unchanged row identities retain their current cache.

Use proven-unreachable bank7 A10C..AA68 for code and authenticated resident
padding for mapper trampolines. Runtime book-keeping explicitly occupies a
declared bounded portion of E800..EDFF; remaining EDFF/F33F gap stays guarded.
Page3 RAM remains selected and DI is retained. No low-page RAM assumptions.

Independent validation follows actual displayed NAME references when protecting
PGT/CGT and validates all published keys against real VRAM. Only ice may refer
across generations; actor/UI/footer role restrictions remain. Explicitly check
reference counts and row lists against decoded strip caches. Retain complete
source pixels, source CPU/all128RAM chains, VDP IO spacing and active SAT/SGT
protection. A test must reject writes to a referenced tile from either ID page.

Measure the real Z80 implementation first in isolated lifecycle cases, then
full source scenes and matched NTSC/PAL routes plus dense synthetic scenes.
Report full-frame mean/P95/max and remaining budget. Publish a useful ROM only
after independent review; keep rejected experiments sealed. Update a new workbook.
