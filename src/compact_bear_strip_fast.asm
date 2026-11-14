; HL=four packed mask/context words, one of the210 certified strip recipes.
; Native bulk contexts are0/1/4/5; all four cells share their context.
; Output C480..C4BF, no other scratch. Preserve IX/IY/SP/IFF.
bf_build:
    PUSH IX
    PUSH IY
    PUSH HL
    POP IX
    INC HL
    LD A,(HL)
    SRL A
    AND 15
    LD IYL,A
    OR A
    JR NZ,.colored
    LD HL,$C480
    LD DE,$C481
    LD BC,63
    LD (HL),255
    LDIR
    JP .done
.colored:
    LD HL,$C480
    LD DE,$C481
    LD BC,31
    LD (HL),255
    LDIR
    LD A,IYL
    CP 1
    LD HL,bf_colors
    JR Z,.palette
    CP 4
    LD HL,bf_colors+8
    JR Z,.palette
    LD HL,bf_colors+16
.palette:
    LD DE,$C4A0
    DUP 4
    PUSH HL
    LD BC,8
    DUP 8
    LDI
    EDUP
    POP HL
    EDUP
    LD DE,$C480
    LD IYH,4
.column:
    LD L,(IX+0)
    LD A,(IX+1)
    AND 1
    LD H,A
    INC IX
    INC IX
    DUP 3
    ADD HL,HL
    EDUP
    LD BC,cb_patterns
    ADD HL,BC
    LD A,IYL
    CP 1
    LD B,8
    JR NZ,.rows
    LD BC,6
    ADD HL,BC
    LD A,E
    ADD A,6
    LD E,A
    LD B,2
.rows:
    LD A,(HL)
    INC HL
    OR A
    JR Z,.next
    LD (DE),A
    PUSH HL
    LD H,D
    LD L,E
    SET 5,L
    LD A,(HL)
    OR $F0
    LD (HL),A
    POP HL
.next:
    INC DE
    DJNZ .rows
    DEC IYH
    JR NZ,.column
.done:
    POP IY
    POP IX
    RET
bf_colors:
    DB $FF,$FF,$FF,$FF,$FF,$FF,$11,$44
    DB $11,$11,$11,$11,$11,$11,$11,$11
    DB $11,$11,$11,$11,$11,$11,$11,$44
bf_end:
