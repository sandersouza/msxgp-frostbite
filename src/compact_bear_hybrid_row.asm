; HL ten-byte recipe, DE PGT destination. Both physical keys at C520..C52B.
; Exact original four8-byte planes streamed with the existing VDP pacing.
; Caller maps the shared dictionaries. IX/IY and DE preserved.
bh_row:
    PUSH IX
    PUSH IY
    PUSH DE
    PUSH HL
    POP IX
    LD HL,$C520
    LD A,(IX+0)
    LD (HL),A
    INC HL
    LD A,(IX+1)
    LD (HL),A
    INC HL
    CALL bh_key
    LD A,(IX+2)
    LD (HL),A
    INC HL
    LD A,(IX+3)
    LD (HL),A
    INC HL
    CALL bh_key
    POP DE
    PUSH DE
    LD A,(IX+4)
    LD BC,bh_patterns
    CALL bh_pointer
    LD B,8
    CALL vdp_write
    LD A,(IX+5)
    LD BC,bh_patterns
    CALL bh_pointer
    LD B,8
    CALL vdp_stream
    POP DE
    PUSH DE
    LD HL,BH_COLOR_OFFSET
    ADD HL,DE
    EX DE,HL
    LD A,(IX+6)
    LD BC,bh_colors
    CALL bh_pointer
    LD B,8
    CALL vdp_write
    LD A,(IX+7)
    LD BC,bh_colors
    CALL bh_pointer
    LD B,8
    CALL vdp_stream
    POP DE
    POP IY
    POP IX
    RET
bh_key:
    ; A is high byte of the just-emitted logical ID. IDs never exceed3FFF.
    CP $FF
    JR Z,.empty
    LD A,(IX+8)
    LD (HL),A
    INC HL
    LD (HL),0
    INC HL
    LD A,(IX+9)
    LD (HL),A
    INC HL
    LD (HL),0
    INC HL
    RET
.empty:
    DUP 4
    LD (HL),$FF
    INC HL
    EDUP
    RET
bh_pointer:
    LD L,A
    LD H,0
    ADD HL,HL
    ADD HL,HL
    ADD HL,HL
    ADD HL,BC
    LD C,$98
    RET
bh_end:
