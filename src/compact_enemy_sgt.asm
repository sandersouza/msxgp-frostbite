; A one of132 exact group/reflection/parity SGT patterns. OutputC500..C51F.
; Uses native core glyphs, expansion and reverse data; no literal SGT atlas.
; Preserves IX/IY/SP/IFF, writes only the original SGT staging buffer.
sx_build:
    PUSH IX
    PUSH IY
    PUSH AF
    LD HL,$C500
    LD DE,$C501
    LD BC,31
    LD (HL),0
    LDIR
    POP AF
    LD C,A
    SRL A
    SRL A
    ADD A,LOW sx_shapes
    LD L,A
    LD H,HIGH sx_shapes
    LD A,(HL)
    ADD A,7
    LD L,A
    LD H,HIGH sx_glyphs
    PUSH HL
    POP IY
    LD A,C
    AND 1
    ADD A,A
    ADD A,HIGH sx_expansion
    LD B,A
    LD A,C
    AND 2
    JR Z,.page
    RES 0,B
.page:
    LD C,B
    LD B,8
    LD IX,$C500
.row:
    LD A,(IY+0)
    DEC IY
    BIT 0,C
    JR NZ,.normal
    LD L,A
    LD H,HIGH sx_reverse
    LD A,(HL)
.normal:
    LD L,A
    LD H,0
    ADD HL,HL
    LD A,C
    OR 1
    ADD A,H
    LD H,A
    LD D,(HL)
    INC HL
    LD E,(HL)
    BIT 1,C
    IF (HIGH sx_expansion) & 2
    JR NZ,.pixels
    ELSE
    JR Z,.pixels
    ENDIF
    SRL D
    RR E
.pixels:
    LD (IX+0),D
    LD (IX+16),E
    INC IX
    DJNZ .row
    POP IY
    POP IX
    LD HL,$C500
    RET
sx_end:
