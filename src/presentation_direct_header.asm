    INCLUDE "symbols.inc"
hy_up EQU $E620
hy_lo EQU $E622
hy_color EQU $E624
hy_first EQU $E625
hy_col EQU $E626
hy_flags EQU $E627
hy_tile EQU $E628
hy_meta EQU $E629
hy_packed EQU $E62B
hy_kind EQU $E62E
hy_half EQU $E62F
hy_colors EQU $E632

    ORG $5DD3
hy_header:
    LD A,(PAGE)
    CP 2
    JP NC,p_world_fail
    CALL w_owner
    PUSH HL
    POP IX
    XOR A
    LD (hy_color),A
    LD (hy_first),A
    LD HL,0
    LD (hy_up),HL
    LD (hy_lo),HL
    LD A,(IX+16)
    CP $5A
    JR Z,.known
    LD HL,1023
    LD (hy_up),HL
    LD (hy_lo),HL
    LD A,1
    LD (hy_color),A
    LD (hy_first),A
    JR .identity_done
.known:
    LD HL,pfh_upper
    LD A,(IX+12)
    CP (HL)
    JR NZ,.colors
    INC HL
    LD A,(IX+13)
    CP (HL)
    JR NZ,.colors
    INC HL
    LD A,(IX+14)
    CP (HL)
    JR Z,.level
.colors:
    LD A,1
    LD (hy_color),A
.level:
    CALL w_level
    CP (IX+15)
    JR Z,.glyphs
    LD HL,1023
    LD (hy_lo),HL
.glyphs:
    LD DE,p_h_codes
    LD IY,w_masks
    LD B,12
.glyph:
    LD A,(DE)
    CP (IX)
    JR Z,.next_glyph
    LD HL,hy_up
    LD A,B
    CP 7
    JR NC,.mask
    LD HL,hy_lo
.mask:
    LD A,(HL)
    OR (IY)
    LD (HL),A
    INC HL
    LD A,(HL)
    OR (IY+1)
    LD (HL),A
.next_glyph:
    INC DE
    INC IX
    INC IY
    INC IY
    DJNZ .glyph
.identity_done:
    CALL w_owner
    LD DE,16
    ADD HL,DE
    LD (HL),0
    LD HL,$C805
    LD IX,$D030
    LD A,(PAGE)
    OR A
    LD A,8
    JR Z,.page
    LD HL,$CD05
    LD IX,$D4B0
    LD A,72
.page:
    LD (hy_tile),A
    LD (hy_meta),IX
    LD B,3
.names_row:
    PUSH BC
    LD C,10
.name:
    LD (HL),A
    INC L
    INC A
    DEC C
    JR NZ,.name
    LD DE,22
    ADD HL,DE
    POP BC
    DJNZ .names_row
    LD A,(hy_first)
    OR A
    JR Z,.no_clear
    CALL hy_address
    XOR A
    LD B,240
    CALL t_fill
.no_clear:
    LD A,(hy_color)
    OR A
    CALL NZ,hy_make_colors
    XOR A
    LD (hy_col),A
    LD IY,p_fast_header_columns
.column:
    LD HL,(hy_up)
    SRL H
    RR L
    LD (hy_up),HL
    LD A,0
    RLA
    LD C,A
    LD HL,(hy_lo)
    SRL H
    RR L
    LD (hy_lo),HL
    LD A,0
    RLA
    ADD A,A
    OR C
    LD (hy_flags),A
    LD C,A
    LD A,(hy_color)
    OR C
    JP Z,.advance
    LD A,(IY)
    CALL p_fast_header_glyph
    LD (pt_glyphs),A
    LD A,(IY)
    ADD A,6
    CALL p_fast_header_glyph
    LD (pt_glyphs+2),A
    XOR A
    LD (pt_glyphs+1),A
    LD (pt_glyphs+3),A
    LD A,(IY+2)
    CP 1
    JR Z,.second
    CP 3
    JR NZ,.ready
.second:
    LD A,(IY+1)
    CALL p_fast_header_glyph
    LD (pt_glyphs+1),A
    LD A,(IY+1)
    ADD A,6
    CALL p_fast_header_glyph
    LD (pt_glyphs+3),A
.ready:
    LD A,(hy_flags)
    BIT 0,A
    JR Z,.lower
    XOR A
    LD (hy_half),A
    CALL hy_lookup
    CALL hy_address
    INC DE
    INC DE
    INC DE
    LD B,5
    CALL vdp_write
    CALL hy_address
    LD A,E
    ADD A,80
    LD E,A
    JR NC,.upper_address
    INC D
.upper_address:
    LD B,3
    CALL vdp_write
.lower:
    LD A,(hy_flags)
    BIT 1,A
    JR Z,.color
    LD A,2
    LD (hy_half),A
    CALL hy_lookup
    CALL hy_address
    LD A,E
    ADD A,87
    LD E,A
    JR NC,.lower_first_address
    INC D
.lower_first_address:
    LD B,1
    CALL vdp_write
    CALL hy_address
    LD A,E
    ADD A,160
    LD E,A
    JR NC,.lower_address
    INC D
.lower_address:
    LD B,7
    CALL vdp_write
.color:
    LD A,(hy_color)
    OR A
    JR Z,.metadata
    CALL hy_address
    LD A,D
    ADD A,$20
    LD D,A
    LD HL,hy_colors
    LD B,8
    CALL vdp_write
    LD A,E
    ADD A,80
    LD E,A
    JR NC,.middle_color
    INC D
.middle_color:
    LD B,8
    CALL vdp_write
    LD A,E
    ADD A,80
    LD E,A
    JR NC,.bottom_color
    INC D
.bottom_color:
    LD B,8
    CALL vdp_write
.metadata:
    CALL hy_metadata
.advance:
    LD DE,3
    ADD IY,DE
    LD HL,(hy_meta)
    LD DE,6
    ADD HL,DE
    LD (hy_meta),HL
    LD HL,hy_tile
    INC (HL)
    LD HL,hy_col
    INC (HL)
    LD A,(HL)
    CP 10
    JP NZ,.column
    JP w_save

; Preserve HL (ROM stream pointer) and BC, return DE=write-enabled PGT cell.
hy_address:
    PUSH HL
    LD A,(hy_tile)
    LD L,A
    LD H,0
    DUP 3
    ADD HL,HL
    EDUP
    LD DE,$4000
    ADD HL,DE
    EX DE,HL
    POP HL
    RET

hy_metadata:
    LD IX,(hy_meta)
    LD A,(pt_glyphs+1)
    RRCA
    RRCA
    AND $C0
    LD B,A
    LD A,(pt_glyphs)
    OR B
    LD (IX),A
    LD (IX+60),A
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
    LD (IX+61),A
    LD B,A
    AND 15
    LD (IX+1),A
    LD A,B
    AND $F0
    LD (IX+121),A
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
    LD (IX+62),A
    LD (IX+122),A
    XOR A
    LD (IX+2),A
    LD (IX+120),A
    LD A,(pfh_upper)
    LD (IX+3),A
    LD B,A
    LD A,(pfh_lower)
    DUP 4
    RLCA
    EDUP
    LD (IX+123),A
    OR B
    LD (IX+63),A
    LD A,(IY+2)
    DUP 4
    RLCA
    EDUP
    LD B,A
    LD A,(pfh_sky)
    OR B
    LD (IX+4),A
    LD (IX+64),A
    LD (IX+124),A
    LD (IX+5),16
    LD (IX+65),17
    LD (IX+125),18
    RET

hy_make_colors:
    LD A,(pfh_sky)
    LD C,A
    DUP 4
    RLCA
    EDUP
    OR C
    LD HL,hy_colors
    DUP 3
    LD (HL),A
    INC HL
    EDUP
    LD A,(pfh_upper)
    DUP 4
    RLCA
    EDUP
    OR C
    DUP 8
    LD (HL),A
    INC HL
    EDUP
    LD A,C
    DUP 4
    RLCA
    EDUP
    OR C
    DUP 4
    LD (HL),A
    INC HL
    EDUP
    LD A,(pfh_lower)
    DUP 4
    RLCA
    EDUP
    OR C
    DUP 8
    LD (HL),A
    INC HL
    EDUP
    LD A,C
    DUP 4
    RLCA
    EDUP
    OR C
    LD (HL),A
    RET
hy_main_end:
    ASSERT $ <= $6249

    ORG $FD00
hy_lookup:
    LD A,(hy_half)
    LD E,A
    LD D,0
    LD HL,pt_glyphs
    ADD HL,DE
    LD C,(HL)
    INC HL
    LD B,(HL)
    LD A,E
    OR A
    JR Z,.regular
    LD A,(hy_col)
    CP 3
    JR Z,.temp_icon
    CP 4
    JR Z,.icon_level
    CP 6
    JR Z,.level_blank
    CP 7
    JR Z,.blank_lives
.regular:
    LD A,(IY+2)
    CP 1
    JR Z,.pair1
    CP 3
    JR Z,.pair3
    LD DE,$B800
    OR A
    JR Z,.single
    LD DE,$B910
    CP 2
    JR Z,.single
    LD DE,$BA20
.single:
    LD L,C
    LD H,0
    DUP 3
    ADD HL,HL
    EDUP
    ADD HL,DE
    LD A,118
    JP t_mapper
.pair1:
    LD A,116
    JR .pair
.pair3:
    LD A,117
.pair:
    PUSH AF
    LD A,C
    DUP 4
    RLCA
    EDUP
    OR B
    LD L,A
    LD H,0
    DUP 3
    ADD HL,HL
    EDUP
    LD DE,$B800
    ADD HL,DE
    POP AF
    JP t_mapper
.temp_icon:
    LD DE,$BB30
    JR .single
.icon_level:
    LD A,B
    CP 33
    LD C,0
    JR NZ,.icon_ready
    INC C
.icon_ready:
    LD DE,$BBB0
    JR .single
.level_blank:
    LD A,C
    CP 33
    LD C,0
    JR NZ,.level_ready
    INC C
.level_ready:
    LD DE,$BBC0
    JR .single
.blank_lives:
    LD C,B
    LD DE,$BBD0
    JR .single
hy_lookup_end:
    ASSERT $ <= $FF00
