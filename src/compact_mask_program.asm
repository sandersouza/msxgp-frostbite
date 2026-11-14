; Accumulate interleaved (old, equal, unequal, exit, visible) mask rows.
; C7D0..D6: signed initial tag, row count, pose, shift, reflection, pointer.
; Scratch: C790..798 row frame, C7D7 tag, C7D8 remaining count.
; Input and program remain immutable. Return A=7 or135; preserve IX/IY/SP/IFF.
    IFNDEF MP_INPUT_ORIGIN
    DEFINE MP_INPUT_ORIGIN $C7D0
    ENDIF
    IFNDEF MP_SCRATCH_ORIGIN
    DEFINE MP_SCRATCH_ORIGIN $C7D7
    ENDIF
    IFNDEF CE_ROW_INPUT_ORIGIN
    DEFINE CE_ROW_INPUT_ORIGIN $C790
    ENDIF
mp_contact:
    LD A,(MP_INPUT_ORIGIN+1)
    OR A
    JR NZ,.start
    LD A,7
    RET
.start:
    LD (MP_SCRATCH_ORIGIN+1),A
    LD A,(MP_INPUT_ORIGIN+0)
    LD (MP_SCRATCH_ORIGIN+0),A
    PUSH IY
    LD IY,(MP_INPUT_ORIGIN+5)
    LD HL,MP_INPUT_ORIGIN+2
    LD DE,CE_ROW_INPUT_ORIGIN+1
    LD BC,3
    LDIR
.row:
    LD A,(MP_SCRATCH_ORIGIN+0)
    LD (CE_ROW_INPUT_ORIGIN+0),A
    PUSH IY
    POP HL
    LD DE,CE_ROW_INPUT_ORIGIN+4
    LD BC,5
    LDIR
    CALL ce_test_row
    BIT 7,A
    JR NZ,.done
    LD DE,5
    ADD IY,DE
    LD A,(MP_SCRATCH_ORIGIN+0)
    DEC A
    LD (MP_SCRATCH_ORIGIN+0),A
    LD A,(MP_SCRATCH_ORIGIN+1)
    DEC A
    LD (MP_SCRATCH_ORIGIN+1),A
    JR NZ,.row
    LD A,7
.done:
    POP IY
    RET
mp_end:
