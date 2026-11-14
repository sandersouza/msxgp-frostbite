; Isolated ordinary-copy coordinate helper, unlinked from the game.
; Inputs C780playerX0..159, C781objectX0..159, C782NUSIZ0..3.
; Outputs C790visible distance+7 orFF, C791hidden distance+7 orFF,
; C792source sample at clock8 orFF, C793playerX. No other scratch.
; Preserve IX/IY/SP/IFF; clobber AF/BC/DE. No mapper or VDP access.
    IFNDEF CX_INPUT_ORIGIN
    DEFINE CX_INPUT_ORIGIN $C780
    ENDIF
    IFNDEF CX_OUTPUT_ORIGIN
    DEFINE CX_OUTPUT_ORIGIN $C790
    ENDIF
cx_context:
    LD A,(CX_INPUT_ORIGIN+1)
    LD B,A
    LD A,(CX_INPUT_ORIGIN+2)
    LD C,A
    LD A,(CX_INPUT_ORIGIN+0)
    CALL cx_find_distance
    LD (CX_OUTPUT_ORIGIN+0),A
    XOR A
    CALL cx_find_distance
    LD (CX_OUTPUT_ORIGIN+1),A
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
    LD (CX_OUTPUT_ORIGIN+2),A
    LD A,(CX_INPUT_ORIGIN+0)
    LD (CX_OUTPUT_ORIGIN+3),A
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
