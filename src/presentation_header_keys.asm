; Pack each live glyph column once; derive the three exact six-byte band keys.
p_th_columns EQU $E620
p_th_colours EQU $E648
p_template_header_keys:
    LD HL,pfh_upper
    LD B,3
.validate:
    LD A,(HL)
    OR A
    JP Z,p_template_header_key_fail
    CP 16
    JP NC,p_template_header_key_fail
    INC HL
    DJNZ .validate
    LD A,(pfh_upper)
    LD (p_th_colours),A
    LD B,A
    LD A,(pfh_lower)
    DUP 4
    RLCA
    EDUP
    LD (p_th_colours+2),A
    OR B
    LD (p_th_colours+1),A
    LD IX,p_fast_header_columns
    LD IY,p_th_columns
    XOR A
    LD (p_h_index),A
.column:
    LD A,(IX)
    CALL p_fast_header_glyph
    LD (pt_glyphs),A
    LD A,(IX)
    ADD A,6
    CALL p_fast_header_glyph
    LD (pt_glyphs+2),A
    XOR A
    LD (pt_glyphs+1),A
    LD (pt_glyphs+3),A
    LD A,(IX+2)
    CP 1
    JR Z,.second
    CP 3
    JR NZ,.pack
.second:
    LD A,(IX+1)
    CALL p_fast_header_glyph
    LD (pt_glyphs+1),A
    LD A,(IX+1)
    ADD A,6
    CALL p_fast_header_glyph
    LD (pt_glyphs+3),A
.pack:
    LD A,(pt_glyphs+1)
    RRCA
    RRCA
    AND $C0
    LD B,A
    LD A,(pt_glyphs)
    OR B
    LD (IY),A
    LD A,(pt_glyphs+2)
    DUP 4
    RLCA
    EDUP
    AND $F0
    LD B,A
    LD A,(pt_glyphs+1)
    SRL A
    SRL A
    OR B
    LD (IY+1),A
    LD A,(pt_glyphs+2)
    DUP 4
    RRCA
    EDUP
    AND 3
    LD B,A
    LD A,(pt_glyphs+3)
    ADD A,A
    ADD A,A
    OR B
    LD (IY+2),A
    LD A,(IX+2)
    DUP 4
    RLCA
    EDUP
    LD B,A
    LD A,(pfh_sky)
    OR B
    LD (IY+3),A
    LD DE,3
    ADD IX,DE
    INC DE
    ADD IY,DE
    LD HL,p_h_index
    INC (HL)
    LD A,(HL)
    CP 10
    JP NZ,.column
    OR A
    RET

p_template_header_key:
    LD A,(p_h_y)
    CP 3
    JP NC,p_template_header_key_fail
    LD A,(p_h_index)
    CP 10
    JP NC,p_template_header_key_fail
    ADD A,A
    ADD A,A
    ADD A,p_th_columns&255
    LD L,A
    LD H,p_th_columns/256
    LD B,(HL)
    INC L
    LD C,(HL)
    INC L
    LD D,(HL)
    INC L
    LD A,(HL)
    LD (pf_key+4),A
    LD A,(p_h_y)
    OR A
    JR Z,.top
    CP 2
    JR Z,.bottom
    LD A,B
    LD (pf_key),A
    LD A,C
    LD (pf_key+1),A
    LD A,D
    LD (pf_key+2),A
    JR .colour
.top:
    LD A,B
    LD (pf_key),A
    LD A,C
    AND 15
    LD (pf_key+1),A
    XOR A
    LD (pf_key+2),A
    JR .colour
.bottom:
    XOR A
    LD (pf_key),A
    LD A,C
    AND $F0
    LD (pf_key+1),A
    LD A,D
    LD (pf_key+2),A
.colour:
    LD A,(p_h_y)
    ADD A,p_th_colours&255
    LD L,A
    LD H,p_th_colours/256
    LD A,(HL)
    LD (pf_key+3),A
    LD A,(p_h_y)
    ADD A,16
    LD (pf_key+5),A
    OR A
    RET
p_template_header_key_fail:
    SCF
    RET
