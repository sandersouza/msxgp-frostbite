; A=foreground1..15, HL=original eight row colors with identical nibbles,
; DE=eight output CGT bytes. Masks are unchanged: all background rows are solid.
np_paint:
    DUP 4
    RLCA
    EDUP
    LD C,A
    DUP 8
    LD A,(HL)
    AND 15
    OR C
    LD (DE),A
    INC HL
    INC DE
    EDUP
    RET
np_end:
