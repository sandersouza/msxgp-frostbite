; Accumulate interleaved (old, equal, unequal, exit, visible) mask rows.
; C7D0..D6: signed initial tag, row count, pose, shift, reflection, pointer.
; Scratch: C790..798 row frame, C7D7 tag, C7D8 remaining count.
; Input and program remain immutable. Return A=7 or135; preserve IX/IY/SP/IFF.
mp_contact:
    LD A,($C7D1)
    OR A
    JR NZ,.start
    LD A,7
    RET
.start:
    LD ($C7D8),A
    LD A,($C7D0)
    LD ($C7D7),A
    PUSH IY
    LD IY,($C7D5)
    LD HL,$C7D2
    LD DE,$C791
    LD BC,3
    LDIR
.row:
    LD A,($C7D7)
    LD ($C790),A
    PUSH IY
    POP HL
    LD DE,$C794
    LD BC,5
    LDIR
    CALL ce_test_row
    BIT 7,A
    JR NZ,.done
    LD DE,5
    ADD IY,DE
    LD A,($C7D7)
    DEC A
    LD ($C7D7),A
    LD A,($C7D8)
    DEC A
    LD ($C7D8),A
    JR NZ,.row
    LD A,7
.done:
    POP IY
    RET
mp_end:
