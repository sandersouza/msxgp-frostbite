; Six-byte header/igloo/footer keys. Canonical score arithmetic is untouched.
pfh_upper EQU $C247
pfh_lower EQU $C248
pfh_sky EQU $C249
pfh_bottom EQU $C24A
pfh_footer_pointer EQU $C24B

p_fast_header_prepare:
    LD A,(p_fd_rows)
    AND 7
    JP Z,p_fast_igloo_prepare
    IFDEF WITH_PRESENTATION_TEMPLATES
    LD A,(PAGE)
    CP 2
    JP NC,p_fixed_fail
    XOR A
    LD (p_fx_bank),A        ;all header cells have fixed roles in SCREEN2 bank0
    ENDIF
    LD A,(p_h_color)
    LD (pfh_upper),A
    LD (pfh_lower),A
    LD A,(p_bg_theme)
    AND 1
    LD A,132
    JR Z,.sky
    LD A,128
.sky:
    CALL p_world_color
    LD A,(p_w_color)
    LD (pfh_sky),A
    LD A,(p_h_codes+6)
    CP $50
    JR NZ,.rows
    LD A,($C071)
    OR A
    JR NZ,.rows
    LD A,($C001)
    AND 8
    JR NZ,.rows
    LD A,(pfh_sky)
    LD (pfh_lower),A
.rows:
    IFDEF WITH_PRESENTATION_TEMPLATES
    CALL p_template_header_keys
    JP C,p_world_fail
    ENDIF
    XOR A
    LD (p_h_y),A
.band:
    XOR A
    LD (p_h_index),A
    IFDEF WITH_PRESENTATION_TEMPLATES
    LD A,(p_h_y)
    LD (p_w_top),A
    LD A,5
    LD (p_w_col),A
    CALL p_fast_cell
    LD A,(p_h_y)
    ADD A,A
    LD B,A
    ADD A,A
    ADD A,A
    ADD A,B
    ADD A,8
    CALL p_fixed_dynamic_id
    LD (p_w_tile),A
    CALL p_fixed_key_address
    LD (p_fx_meta),HL
    ENDIF
.column:
    IFDEF WITH_PRESENTATION_TEMPLATES
    CALL p_template_header_key
    JP C,p_world_fail
    ELSE
    LD A,(p_h_index)
    LD E,A
    LD D,0
    LD L,E
    LD H,D
    ADD HL,HL
    ADD HL,DE
    LD DE,p_fast_header_columns
    ADD HL,DE
    PUSH HL
    POP IX
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
    JR NZ,.active_bands
.second:
    LD A,(IX+1)
    CALL p_fast_header_glyph
    LD (pt_glyphs+1),A
    LD A,(IX+1)
    ADD A,6
    CALL p_fast_header_glyph
    LD (pt_glyphs+3),A
.active_bands:
    LD A,(pfh_upper)
    LD B,A
    LD A,(pfh_lower)
    LD C,A
    LD A,(p_h_y)
    OR A
    JR NZ,.upper_active
    LD C,0
    LD (pt_glyphs+2),A
    LD (pt_glyphs+3),A
.upper_active:
    LD A,(p_h_y)
    CP 2
    JR NZ,.colors
    XOR A
    LD B,A
    LD (pt_glyphs),A
    LD (pt_glyphs+1),A
.colors:
    LD A,C
    DUP 4
    RLCA
    EDUP
    OR B
    LD (pf_key+3),A
    LD A,(pt_glyphs+1)
    RRCA
    RRCA
    AND $C0
    LD B,A
    LD A,(pt_glyphs)
    OR B
    LD (pf_key),A
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
    LD (pf_key+1),A
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
    LD (pf_key+2),A
    LD A,(IX+2)
    DUP 4
    RLCA
    EDUP
    LD B,A
    LD A,(pfh_sky)
    OR B
    LD (pf_key+4),A
    LD A,(p_h_y)
    LD (p_w_top),A
    ADD A,16
    LD (pf_key+5),A
    ENDIF
    IFDEF WITH_PRESENTATION_TEMPLATES
    CALL p_fixed_put_header
    JP C,p_world_fail
    LD HL,(p_w_name)
    INC HL
    LD (p_w_name),HL
    LD HL,(p_fx_meta)
    LD DE,6
    ADD HL,DE
    LD (p_fx_meta),HL
    LD HL,p_w_tile
    INC (HL)
    ELSE
    LD A,(p_h_index)
    ADD A,5
    LD (p_w_col),A
    CALL p_fast_cell
    CALL p_fast_put
    ENDIF
    LD HL,p_h_index
    INC (HL)
    LD A,(HL)
    CP 10
    JP NZ,.column
    LD HL,p_h_y
    INC (HL)
    LD A,(HL)
    CP 3
    JP NZ,.band
    JP p_fast_igloo_prepare

p_fast_header_glyph:
    CP 8
    LD B,32
    JR Z,.special
    CP 9
    JR NZ,.font
    LD B,A
    LD A,($C04B)
    CP 20
    LD A,B
    JR C,.font
    LD B,33
.special:
    LD A,B
    RET
.font:
    ADD A,p_h_codes&255
    LD L,A
    LD H,p_h_codes/256
    LD A,(HL)
    DUP 3
    SRL A
    EDUP
    RET
p_fast_header_columns:
    DB 0,0,0, 0,1,1, 1,0,2, 1,2,3, 2,3,1
    DB 3,0,2, 3,4,3, 4,5,1, 5,0,2, 5,0,4

p_fast_igloo_prepare:
    XOR A
    LD (p_h_level),A
.row:
    LD A,(p_h_level)
    ADD A,3
    CALL p_fast_row_dirty
    JP Z,.next_row
    LD A,(p_h_level)
    OR A
    JR NZ,.paired
    LD (p_h_bits),A
    LD A,($C044)
    JR .bottom
.paired:
    LD B,A
    LD A,$45
    SUB B
    SUB B
    LD L,A
    LD H,$C0
    LD A,(HL)
    LD (p_h_bits),A
    DEC HL
    LD A,(HL)
.bottom:
    LD (pfh_bottom),A
    XOR A
    LD (p_h_bit),A
.column:
    LD A,(p_h_bits)
    CALL p_fast_igloo_mask
    LD (pf_key),A
    LD A,(pfh_bottom)
    CALL p_fast_igloo_mask
    LD (pf_key+1),A
    LD B,A
    LD A,(pf_key)
    OR B
    JR Z,.next
    LD A,(p_h_level)
    ADD A,3
    LD (p_w_top),A
    LD A,(p_h_bit)
    ADD A,22
    LD (p_w_col),A
    CALL p_fast_cell
    LD HL,(p_w_name)
    LD A,(HL)
    LD (pf_key+2),A
    LD A,14
    LD (pf_key+3),A
    XOR A
    LD (pf_key+4),A
    LD A,5
    LD (pf_key+5),A
    CALL p_fast_put
.next:
    LD HL,p_h_bit
    INC (HL)
    LD A,(HL)
    CP 6
    JR NZ,.column
.next_row:
    LD HL,p_h_level
    INC (HL)
    LD A,(HL)
    CP 3
    JP NZ,.row
    RET
p_fast_igloo_mask:
    LD C,A
    LD A,(p_h_bit)
    LD E,A
    LD D,0
    LD HL,p_fast_igloo_shifts
    ADD HL,DE
    LD B,(HL)
    LD A,B
    OR A
    LD A,C
    JR Z,.shifted
.shift:
    SRL A
    DJNZ .shift
.shifted:
    AND 3
    LD C,A
    LD A,E
    CP 3
    JR C,.part
    SUB 3
.part:
    ADD A,A
    ADD A,A
    OR C
    LD E,A
    LD HL,p_fast_igloo_masks
    ADD HL,DE
    LD A,(HL)
    RET
p_fast_igloo_shifts:
    DB 0,1,2,4,5,6
p_fast_igloo_masks:
    DB 0,$FC,$03,$FF,0,$F0,$0F,$FF,0,$C0,$3F,$FF

p_fast_footer_prepare:
    IFDEF WITH_PRESENTATION_TEMPLATES
    JP p_template_footer_prepare
    ELSE
    LD A,(p_fd_rows+2)
    AND 192
    RET Z
    LD A,(p_h_footer_phase)
    ADD A,A
    LD B,A
    LD A,(p_w_coarse)
    OR B
    LD L,A
    LD H,0
    LD E,L
    LD D,H
    ADD HL,HL
    ADD HL,DE
    ADD HL,HL
    ADD HL,HL
    OR A
    SBC HL,DE
    ADD HL,HL
    ADD HL,HL
    LD DE,p_static_footer_names_data
    ADD HL,DE
    LD (pfh_footer_pointer),HL
    XOR A
    LD (p_h_footer_index),A
.cell:
    LD A,p_static_footer_names_bank
    LD ($7000),A
    LD HL,(pfh_footer_pointer)
    LD E,(HL)
    INC HL
    LD D,(HL)
    INC HL
    LD (pfh_footer_pointer),HL
    LD A,D
    OR E
    JR Z,.next
    LD (pf_key),DE
    XOR A
    LD (pf_key+2),A
    LD (pf_key+3),A
    LD (pf_key+4),A
    LD A,6
    LD (pf_key+5),A
    LD A,(p_h_footer_index)
    LD B,22
    CP 11
    JR C,.position
    SUB 11
    INC B
.position:
    ADD A,4
    LD (p_w_col),A
    LD A,B
    LD (p_w_top),A
    CALL p_fast_cell
    CALL p_fast_put
.next:
    LD HL,p_h_footer_index
    INC (HL)
    LD A,(HL)
    CP 22
    JR NZ,.cell
    RET
    ENDIF
