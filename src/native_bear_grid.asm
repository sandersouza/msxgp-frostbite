; A=group0..15,B=source X phase0..15,C=coarse0/1.
; Build a fixed4x3 SCREEN2 mask grid atC480..C4DF from the same six pictures
; used by the full three-sprite bear. No expanded geometry or raw-ID atlas.
; Existing scratchC500..C50F only; preserve IX/IY/SP/IFF.
ng_shift EQU $C500
ng_y EQU $C501
ng_packet EQU $C502
ng_dy EQU $C504
ng_row EQU $C505
ng_columns EQU $C506
ng_thin EQU $C507

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
    POP AF
    ADD A,A
    LD L,A
    LD H,0
    LD DE,ng_info
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD A,(HL)
    LD (ng_dy),A
    LD L,E
    LD H,0
    LD D,H
    ADD HL,HL
    ADD HL,DE
    DUP 5
    ADD HL,HL
    EDUP
    LD DE,ng_pool
    ADD HL,DE
    LD (ng_packet),HL
    LD HL,$C480
    LD DE,$C481
    LD BC,95
    LD (HL),0
    LDIR
    LD HL,(ng_packet)
    LD DE,8
    ADD HL,DE
    PUSH HL
    POP IY
    LD HL,(ng_packet)
    LD DE,64
    ADD HL,DE
    LD A,(ng_dy)
    NEG
    LD E,A
    LD D,0
    ADD HL,DE
    LD (ng_thin),HL
    LD IX,$C480
    LD A,(ng_y)
    LD E,A
    LD D,0
    ADD IX,DE
    XOR A
    LD (ng_row),A
.row:
    LD D,(IY+0)
    LD E,(IY+16)
    LD HL,(ng_thin)
    LD C,(HL)
    INC HL
    LD (ng_thin),HL
    LD A,(ng_shift)
    LD B,A
    OR A
    JR Z,.shifted
    XOR A
.shift:
    SRL D
    RR E
    RR C
    RRA
    DJNZ .shift
.shifted:
    LD (IX+0),D
    LD (IX+8),E
    LD (IX+16),C
    LD (IX+24),A
    INC IY
    INC IX
    LD A,IXL
    AND 7
    JR NZ,.next
    LD DE,24
    ADD IX,DE
.next:
    LD HL,ng_row
    INC (HL)
    LD A,(HL)
    CP 8
    JR NZ,.count
    LD DE,16
    ADD IY,DE
.count:
    CP 20
    JR NZ,.row
    POP IY
    POP IX
    RET
ng_end:
