# Constant dirty-row spans under development

TEMPLATE object and floe rows have fixed source-derived vertical origins:
153−26×row and167−26×row, plus the coarse 0/1 shift, with heights 8 and7.
A resident helper ORs their precomputed 24-bit spans into the row mask. It keeps
the original four-row caller loops, histories, normalized state and every
resulting row bit. It uses no new RAM, mapper writes or hardware assumptions.
Other profiles retain the prior span code and bytes.

The actual-Z80 state checker now includes 2,048 derived operations for all 256
combinations of four object/four floe changes and both coarse positions. Each
combination first primes both generations, then checks the isolated union on
both. An independent inclusive Y/height formula verifies that union before
native execution. These supplement 2,115 original observations, four view flags
and 2,560 arithmetic boundaries: 6,727 complete state/mask operations, guarded
source/C6/heap/SP/IFF/slot/VRAM and retained history tails.

The old candidate exceeds the 12,500-cycle component bound at 14,474. The new
candidate passes at 10,532, including RPC; unchanged-state maximum remains 8,832.
Last-frame dirty preparation in the keyboard probe falls 13,944→10,002 cycles.

Private ROM SHA-256:
a704108f49d7dd319427865b8f1a1fb8615554841bd87b7485a067e90d6c328c.
All 2,115 original full-scene/ownership cases pass, maximum 595,103 controlled
preparation cycles. The 120-frame keyboard run still fails: 571,692 maximum busy
cycles, 22 overruns and 48 skipped frames. The unchanged world stage remains
141,042 cycles in the compared last frame. The default control is still exactly
0b98f3cb89e99f6e79ad9f1a3fb237c2cbfadebcd5759025a123ce33e09fcf78.
All 469 host tests pass. These component gains do not qualify real-time graphics,
ordered PSG, integrated acceptance or a new human-ROM delivery.
