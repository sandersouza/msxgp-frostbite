; Same eight original colors; preserve BC as well as the caller's IX/IY.
np_paint:
    PUSH BC
    DUP 4
    RLCA
    EDUP
    LD C,A
    LD B,8
.row:
    LD A,(HL)
    AND 15
    OR C
    LD (DE),A
    INC HL
    INC DE
    DJNZ .row
    POP BC
    RET
np_end:
