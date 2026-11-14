; Same512-case original-glyph grid contract as native_bear_grid.asm.
; Literal grammar:22 unique24-bit source rows, eight horizontal shifts;
; six20-byte row-selector pictures. No expanded tile/geometry dictionary.
ng_shift EQU $C500
ng_y EQU $C501
ng_base EQU $C502
ng_columns EQU $C506

ng_build:
    PUSH IX
    PUSH IY
    PUSH AF
    LD A,C
    ADD A,3
    LD (ng_y),A
    LD A,B
    SRL A
    ADD A,B
    AND 7
    LD (ng_shift),A
    LD A,3
    JR Z,.columns
    INC A
.columns:
    LD (ng_columns),A
    LD A,(ng_shift)
    LD L,A
    LD H,0
    DUP 3
    ADD HL,HL
    EDUP
    LD D,H
    LD E,L
    DUP 3
    ADD HL,HL
    EDUP
    ADD HL,DE
    ADD HL,DE
    ADD HL,DE
    LD DE,ng_shifted
    ADD HL,DE
    LD (ng_base),HL
    POP AF
    ADD A,A
    LD L,A
    LD H,0
    LD DE,ng_info
    ADD HL,DE
    LD L,(HL)
    LD H,0
    ADD HL,HL
    ADD HL,HL
    LD D,H
    LD E,L
    ADD HL,HL
    ADD HL,HL
    ADD HL,DE
    LD DE,ng_rows
    ADD HL,DE
    PUSH HL
    POP IY
    ; Only rows not overwritten by the20-row constructor need clearing.
    ; Both vertical phases start at3 or4; row23 is uncovered for phase0.
    LD HL,0
    LD ($C480),HL
    LD ($C482),HL
    LD ($C488),HL
    LD ($C48A),HL
    LD ($C490),HL
    LD ($C492),HL
    LD ($C498),HL
    LD ($C49A),HL
    XOR A
    LD ($C4C7),A
    LD ($C4CF),A
    LD ($C4D7),A
    LD ($C4DF),A
    LD IX,$C480
    LD A,(ng_y)
    LD E,A
    LD D,0
    ADD IX,DE
    LD B,20
.row:
    LD L,(IY+0)
    LD H,0
    ADD HL,HL
    ADD HL,HL
    LD DE,(ng_base)
    ADD HL,DE
    LD A,(HL)
    LD (IX+0),A
    INC HL
    LD A,(HL)
    LD (IX+8),A
    INC HL
    LD A,(HL)
    LD (IX+16),A
    INC HL
    LD A,(HL)
    LD (IX+24),A
    INC IY
    INC IX
    LD A,IXL
    AND 7
    JR NZ,.next
    LD DE,24
    ADD IX,DE
.next:
    DJNZ .row
    POP IY
    POP IX
    RET
ng_end:
