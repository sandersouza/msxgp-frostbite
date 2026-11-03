; Only X24..83/Y19..29. All eight source pixels are past the latest prefix
; update (22) and before the earliest tail color change (91). The body is fully
; visible; its last virtual line65..75 is followed by a clear hold-table row.
; Coarse placement duplicates virtual56 exactly, then shifts later lines by1.
p_player_shore_stream:
    LD DE,18
    LD HL,(p_p_patternbase)
    ADD HL,DE
    PUSH HL
    POP IX
    LD HL,(p_p_colorbase)
    ADD HL,DE
    PUSH HL
    POP IY
    LD A,($C064)
    ADD A,21
    LD C,A
    LD A,($C064)
    ADD A,28
    LD (p_p_virtual),A
    CP 57
    LD A,C
    JR C,.target
    LD B,A
    LD A,(p_w_coarse)
    ADD A,B
.target:
    LD (p_p_target),A
    LD B,19
.row:
    LD A,(IX)
    DEC IX
    LD C,A
    LD A,($C06C)
    AND 8
    LD A,C
    JR Z,.pattern
    LD L,A
    LD H,p_sprite_reverse_data/256
    LD A,(HL)
.pattern:
    OR A
    LD (p_p_bit),A
    LD A,(IY)
    DEC IY
    PUSH BC
    JR Z,.coarse           ;16-bit DEC IY and the loads retain mask-zero flags
    LD L,A
    LD H,p_sprite_colors_data/256
    LD A,(HL)
    CALL p_player_store    ;C retains this mapped color for the duplicate line
.coarse:
    LD A,(p_p_virtual)
    CP 56
    JR NZ,.next
    LD A,(p_w_coarse)
    OR A
    JR Z,.next
    LD HL,p_p_target
    INC (HL)
    LD A,(p_p_bit)
    OR A
    JR Z,.next
    LD A,C
    CALL p_player_store
.next:
    POP BC
    LD HL,p_p_target
    INC (HL)
    LD HL,p_p_virtual
    INC (HL)
    DJNZ .row
    RET
