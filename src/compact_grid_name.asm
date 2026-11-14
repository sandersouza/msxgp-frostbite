; Rebuild32-byte prepared NAME row. C7F0 phase0..159, C7F1 owner0..7.
; C200..C21F output, C7F2..C7F3 scratch. Inputs immutable.
; Owner is page*4+lane. No mapper/VDP accesses; preserve IX/IY/SP/IFF.
    IFNDEF CG_OUTPUT
CG_OUTPUT EQU $C200
    ENDIF
cg_build:
    LD A,($C7F1)
    LD L,A
    LD H,0
    LD DE,cg_bases
    ADD HL,DE
    LD C,(HL)
    LD L,A
    LD H,0
    LD DE,cg_waters
    ADD HL,DE
    LD A,(HL)
    LD ($C7F3),A
    LD A,($C7F0)
    LD L,A
    LD H,0
    LD DE,cg_directory
    ADD HL,DE
    LD L,(HL)
    LD H,0
    LD E,L
    LD D,H
    DUP 4
    ADD HL,HL
    EDUP
    OR A
    SBC HL,DE
    LD DE,cg_rows
    ADD HL,DE
    LD DE,CG_OUTPUT
    LD B,15
.pair:
    LD A,(HL)
    LD ($C7F2),A
    DUP 4
    RRCA
    EDUP
    AND 15
    CALL .store
    LD A,($C7F2)
    AND 15
    CALL .store
    INC HL
    DJNZ .pair
    XOR A
    LD (DE),A
    INC DE
    LD (DE),A
    RET
.store:
    CP 8
    JR Z,.water
    ADD A,C
    JR .write
.water:
    LD A,($C7F3)
.write:
    LD (DE),A
    INC DE
    RET
cg_end:
