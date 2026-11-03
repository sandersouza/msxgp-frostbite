; Exact typed header output, reading only the source rows used by each band.
; The existing six-byte grammar and complete16-byte representation are retained.
    ASSERT (p_static_header_data&7) = 0
    ASSERT p_static_header_data+1360 <= $C000
pt_h_offset EQU pt_mask
pt_h_target EQU pt_mask+1
pt_h_count EQU pt_mask+2
pt_h_first EQU pt_mask+3

p_template_header_construct:
    LD A,(pt_key)
    AND 63
    LD (pt_glyphs),A
    LD A,(pt_key)
    RLCA
    RLCA
    AND 3
    LD B,A
    LD A,(pt_key+1)
    ADD A,A
    ADD A,A
    AND 60
    OR B
    LD (pt_glyphs+1),A
    LD A,(pt_key+1)
    DUP 4
    RRCA
    EDUP
    AND 15
    LD B,A
    LD A,(pt_key+2)
    DUP 4
    RLCA
    EDUP
    AND 48
    OR B
    LD (pt_glyphs+2),A
    LD A,(pt_key+2)
    RRCA
    RRCA
    AND 63
    LD (pt_glyphs+3),A
    LD HL,pt_glyphs
    LD B,4
.glyph:
    LD A,(HL)
    CP 34
    JP NC,pt_fail
    INC L
    DJNZ .glyph
    LD A,(pt_key+4)
    DUP 4
    RRCA
    EDUP
    AND 15
    CP 5
    JP NC,pt_fail
    XOR A
    LD HL,pt_tile
    DUP 8
    LD (HL),A
    INC L
    EDUP
    LD A,p_static_header_bank
    LD ($7000),A
    LD A,(pt_kind)
    CP 18
    JR Z,.lower
    CP 16
    JR Z,.upper
    XOR A
    LD DE,$0500            ;upper glyph rows5..7 -> output rows0..2
    LD B,3
    CALL p_template_header_span
    RET C
    LD A,2
    LD DE,$0007            ;lower glyph row0 -> output row7
    LD B,1
    CALL p_template_header_span
    RET C
    JR .colours
.upper:
    XOR A
    LD DE,$0003            ;upper glyph rows0..4 -> output rows3..7
    LD B,5
    CALL p_template_header_span
    RET C
    JR .colours
.lower:
    LD A,2
    LD DE,$0100            ;lower glyph rows1..7 -> output rows0..6
    LD B,7
    CALL p_template_header_span
    RET C
.colours:
    LD A,(pt_key+4)
    AND 15
    LD B,A
    DUP 4
    RLCA
    EDUP
    OR B
    LD HL,pt_tile+8
    DUP 8
    LD (HL),A
    INC L
    EDUP
    LD A,(pt_kind)
    CP 18
    JR Z,.lower_colours
    LD A,(pt_key+3)
    AND 15
    CALL pt_header_color
    LD A,(pt_kind)
    CP 16
    LD A,C
    JR Z,.upper_colours
    LD HL,pt_tile+8
    DUP 3
    LD (HL),A
    INC L
    EDUP
    LD A,(pt_key+3)
    DUP 4
    RRCA
    EDUP
    AND 15
    CALL pt_header_color
    LD A,C
    LD (pt_tile+15),A
    XOR A
    RET
.upper_colours:
    LD HL,pt_tile+11
    DUP 5
    LD (HL),A
    INC L
    EDUP
    XOR A
    RET
.lower_colours:
    LD A,(pt_key+3)
    DUP 4
    RRCA
    EDUP
    AND 15
    CALL pt_header_color
    LD A,C
    LD HL,pt_tile+8
    DUP 7
    LD (HL),A
    INC L
    EDUP
    XOR A
    RET

; A=glyph pair0/2, D=source offset,E=target offset,B=count1/3/5/7.
p_template_header_span:
    LD (pt_pair),A
    LD A,D
    LD (pt_h_offset),A
    LD A,E
    LD (pt_h_target),A
    LD A,B
    LD (pt_h_count),A
    LD A,(pt_key+4)
    DUP 4
    RRCA
    EDUP
    AND 15
    ADD A,A
    LD E,A
    LD D,0
    LD HL,pt_header_parts
    ADD HL,DE
    LD A,(HL)
    INC HL
    LD C,(HL)
    PUSH BC
    CALL pt_header_fragment
    POP BC
    RET C
    LD A,(pt_h_offset)
    LD E,A
    LD D,0
    ADD HL,DE
    LD (pt_h_first),HL
    LD A,C
    CP 255
    JR Z,.single
    LD HL,pt_pair
    INC (HL)
    CALL pt_header_fragment
    RET C
    LD A,(pt_h_offset)
    LD E,A
    LD D,0
    ADD HL,DE
    EX DE,HL
    JR .pointers
.single:
    LD DE,p_template_header_zero
.pointers:
    LD HL,(pt_h_first)
    LD A,(pt_h_target)
    ADD A,pt_tile&255
    LD C,A
    LD B,pt_tile/256
    LD A,(pt_h_count)
    CP 7
    JR Z,.rows7
    CP 5
    JR Z,.rows5
    CP 3
    JR Z,.rows3
    JR .rows1
.rows7:
    DUP 2
    LD A,(DE)
    OR (HL)
    LD (BC),A
    INC L
    INC E
    INC C
    EDUP
.rows5:
    DUP 2
    LD A,(DE)
    OR (HL)
    LD (BC),A
    INC L
    INC E
    INC C
    EDUP
.rows3:
    DUP 2
    LD A,(DE)
    OR (HL)
    LD (BC),A
    INC L
    INC E
    INC C
    EDUP
.rows1:
    LD A,(DE)
    OR (HL)
    LD (BC),A
    XOR A
    RET
    ALIGN 8
p_template_header_zero:
    DS 8,0
