; A=normal P0 pattern0..69. Exact32 bytes atC500, using the already resident
; source expansion table. Packed offset bit15 selects the horizontal phase.
np0_build:
    PUSH IX
    PUSH IY
    LD L,A
    LD H,0
    ADD HL,HL
    LD DE,np0_directory
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    LD A,D
    RLCA
    AND 1
    ADD A,A
    ADD A,HIGH np0_expansion
    LD C,A
    RES 7,D
    LD HL,np0_rows
    ADD HL,DE
    PUSH HL
    POP IY
    LD IX,$C500
    LD B,16
.row:
    LD L,(IY+0)
    LD H,0
    ADD HL,HL
    LD A,H
    ADD A,C
    LD H,A
    LD A,(HL)
    LD (IX+0),A
    INC HL
    LD A,(HL)
    LD (IX+16),A
    INC IY
    INC IX
    DJNZ .row
    POP IY
    POP IX
    LD HL,$C500
    RET
np0_end:
