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
    JR C,.exact
    CP 138
    JR NC,.exact
    LD A,7
    RET
.exact:
    LD D,A
    LD A,($C066)
    SUB D
    JR NC,.distance
    ADD A,160
.distance:
    CP 16
    JR C,.build
    CP 153
    JR NC,.build
    LD A,D
    CP 9
    JR C,.build
    CP 145
    JR NC,.build
    LD A,(hazard_x)
.mod15:
    CP 15
    JR C,.remainder
    SUB 15
    JR .mod15
.remainder:
    NEG
    ADD A,14
    ADD A,D
    SUB 8
    CALL ws_wrap
    CP 16
    JR C,.build
    CP 145
    JR NC,.build
    LD A,7
    RET
.build:
    INCLUDE "compact_shore_cached_edge_query.asm"
