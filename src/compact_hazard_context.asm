; Isolated ordinary-copy coordinate helper, unlinked from the game.
; Inputs C780playerX0..159, C781objectX0..159, C782NUSIZ0..3.
; Outputs C790visible distance+7 orFF, C791hidden distance+7 orFF,
; C792source sample at clock8 orFF, C793playerX. No other scratch.
; Preserve IX/IY/SP/IFF; clobber AF/BC/DE. No mapper or VDP access.
cx_context:
    LD A,($C781)
    LD B,A
    LD A,($C782)
    LD C,A
    LD A,($C780)
    CALL cx_find_distance
    LD ($C790),A
    XOR A
    CALL cx_find_distance
    LD ($C791),A
    LD A,8
    CALL cx_find_distance
    CP 7
    JR C,.no_sample
    CP 15
    JR NC,.no_sample
    SUB 7
    JR .sample
.no_sample:
    LD A,255
.sample:
    LD ($C792),A
    LD A,($C780)
    LD ($C793),A
    RET

; A source point, B objectX, C NUSIZ. At most one copy lies within-7..7:
; the candidate interval spans15pixels, whereas copy spacing is at least16.
cx_find_distance:
    SUB B
    JR NC,.distance
    ADD A,160
.distance:
    LD D,A
    CALL cx_test_distance
    RET C
    BIT 0,C
    JR Z,.copy32
    LD A,D
    SUB 16
    JR NC,.distance16
    ADD A,160
.distance16:
    CALL cx_test_distance
    RET C
.copy32:
    BIT 1,C
    JR Z,.miss
    LD A,D
    SUB 32
    JR NC,.distance32
    ADD A,160
.distance32:
    CALL cx_test_distance
    RET C
.miss:
    LD A,255
    RET

cx_test_distance:
    CP 8
    JR C,.hit
    CP 153
    JR C,.miss
    SUB 160
.hit:
    ADD A,7
    SCF
    RET
.miss:
    OR A
    RET
cx_end:
