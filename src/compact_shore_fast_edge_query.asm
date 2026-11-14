; Called only for PX0..8 or153..159 by the expanded common dispatcher.
; Body24..137 reaches neither the clipped visible player nor hidden clocks.
se_fast_query:
    LD A,(hazard_x)
    CP 15
    LD B,1
    JR NC,.offset
    LD B,6
.offset:
    ADD A,B
    CP 160
    JR C,.body
    SUB 160
.body:
    CP 24
    JR C,.build
    CP 138
    JR NC,.build
    LD A,7
    RET
.build:
    INCLUDE "compact_shore_edge_query.asm"
