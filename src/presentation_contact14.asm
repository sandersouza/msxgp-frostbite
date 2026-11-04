; Bank number stays id/512. 512 packed28-byte blocks leave a2KiB asset tail.
    INCLUDE "symbols.inc"
    ORG $4B6E
c14_slot:
    LD A,D
    AND 1
    LD H,A
    LD L,E
    ADD HL,HL
    ADD HL,HL             ;4*local slot
    LD D,H
    LD E,L
    ADD HL,HL
    ADD HL,HL
    ADD HL,HL             ;32*local slot
    OR A
    SBC HL,DE             ;28*local slot
    SET 7,H
    RET

; HL=packed block, hazard_leaf0..15; returns exact DE, preserves IX/IY.
c14_read:
    PUSH HL
    LD A,(hazard_leaf)
    LD B,A
    LD E,A
    LD D,0
    LD HL,c14_offsets
    ADD HL,DE
    LD E,(HL)
    POP HL
    ADD HL,DE
    LD A,B
    AND 3
    NEG
    AND 3
    ADD A,A
    LD B,A
    LD E,(HL)
    INC HL
    LD D,(HL)
    INC HL
    LD A,(HL)
    INC B
    DEC B
    JR Z,.mask
.shift:
    SRL A
    RR D
    RR E
    DJNZ .shift
.mask:
    LD A,D
    AND 63
    LD D,A
    RET
c14_offsets:
    DB 0,1,3,5,7,8,10,12,14,15,17,19,21,22,24,26
c14_end:
    ASSERT $ <= $4C00
