; Exact nine certified contexts. InputDE packed mask/context, outputC520..C52F.
; No scratch apart from the original tile. IX/IY/SP/IFF preserved.
cb_build:
    PUSH IX
    PUSH IY
    LD A,D
    SRL A
    AND 15
    LD IYL,A
    LD A,D
    AND 1
    LD H,A
    LD L,E
    DUP 3
    ADD HL,HL
    EDUP
    LD DE,cb_patterns
    ADD HL,DE
    PUSH HL
    LD A,IYL
    LD L,A
    LD H,0
    DUP 4
    ADD HL,HL
    EDUP
    LD DE,cb_bases
    ADD HL,DE
    LD DE,$C520
    LD BC,16
    LDIR
    POP HL
    LD A,IYL
    OR A
    JP Z,.done
    LD DE,$C520
    CP 6
    JR Z,.clip
    CP 8
    JR Z,.mixed_clip
    LD B,8
    CP 1
    JR NZ,.palette
    LD BC,6
    ADD HL,BC
    LD DE,$C526
    LD B,2
.palette:
    CP 4
    JR Z,.white
    CP 5
    JR Z,.white
    CP 1
    JR Z,.white
    LD IYH,$10
    LD IYL,$11
    JR .rows
.white:
    LD IYH,$F0
    LD IYL,$FF
.rows:
    LD A,(HL)
    OR A
    JR Z,.next
    LD C,A
    EX DE,HL
    SET 3,L
    LD A,(HL)
    CP IYL
    JR Z,.same
    AND 15
    OR IYH
    LD (HL),A
    RES 3,L
    LD (HL),C
    JR .restore
.same:
    RES 3,L
.restore:
    EX DE,HL
.next:
    INC HL
    INC DE
    DJNZ .rows
.done:
    POP IY
    POP IX
    RET
.clip:
    LD B,8
.clip_row:
    LD A,(HL)
    CPL
    AND 15
    LD (DE),A
    INC HL
    INC DE
    DJNZ .clip_row
    JR .done
.mixed_clip:
    LD B,8
.mixed_row:
    LD A,(HL)
    AND 15
    LD C,A
    LD A,E
    CP $22
    LD A,C
    JR Z,.white_clip
    CPL
    AND 15
    LD (DE),A
    JR .mixed_next
.white_clip:
    OR A
    JR Z,.mixed_next
    LD (DE),A
    EX DE,HL
    SET 3,L
    LD (HL),$1F
    RES 3,L
    EX DE,HL
.mixed_next:
    INC HL
    INC DE
    DJNZ .mixed_row
    JR .done
cb_end:
