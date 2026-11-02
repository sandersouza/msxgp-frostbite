; Literal original HUD glyph selectors and PF1 igloo bits. Read-only canonical
; state; glyph expansion is presentation only, with no score/temperature math.
p_h_src EQU $C235
p_h_height EQU $C237
p_h_index EQU $C238
p_h_y EQU $C23A
p_h_sky EQU $C23B
p_h_level EQU $C23F
p_h_bits EQU $C240
p_h_bit EQU $C241
p_h_color EQU $C242
p_h_codes EQU $C4C0

presentation_hud_prepare:
    LD A,($C03F)
    BIT 7,A
    RET NZ
    LD HL,$C048
    LD DE,p_h_codes
    LD B,3
.score:
    LD A,(HL)
    RRCA
    AND $78
    LD (DE),A
    INC DE
    LD A,(HL)
    DUP 3
    RLCA
    EDUP
    AND $78
    LD (DE),A
    INC DE
    INC HL
    DJNZ .score
    LD HL,p_h_codes
    LD B,5
.leading:
    LD A,(HL)
    OR A
    JR NZ,.status
    LD (HL),$50
    INC HL
    DJNZ .leading
.status:
    LD A,($C065)
    RRCA
    AND $78
    JR NZ,.upper
    LD A,$50
.upper:
    LD (p_h_codes+6),A
    LD A,($C065)
    DUP 3
    RLCA
    EDUP
    AND $78
    LD (p_h_codes+7),A
    LD A,$53
    LD (p_h_codes+8),A
    LD A,$50
    LD (p_h_codes+9),A
    LD (p_h_codes+10),A
    LD A,($C04C)
    OR A
    JR Z,.reserve
    DUP 3
    RLCA
    EDUP
    AND $F8
    JR .reserve_code
.reserve:
    LD A,$50
.reserve_code:
    LD (p_h_codes+11),A
    LD A,1
    LD ($7000),A
    LD A,($C047)
    CP 7
    JP NC,p_world_fail
    LD E,A
    LD D,0
    LD HL,$B3F9
    ADD HL,DE
    LD A,(HL)
    CALL p_world_color
    LD A,(p_w_color)
    LD (p_h_color),A
    IFDEF WITH_PRESENTATION_FAST
    JP p_fast_header_prepare
    ELSE
    XOR A
    LD (p_h_index),A
.glyph:
    LD A,1
    LD ($7000),A
    LD A,(p_h_color)
    LD (p_w_color),A
    LD A,(p_h_index)
    LD E,A
    LD D,0
    LD HL,p_h_codes
    ADD HL,DE
    LD L,(HL)
    LD H,$B3
    LD A,E
    CP 9
    JR NZ,.pointer
    LD A,($C04B)
    CP 20
    JR C,.pointer
    LD HL,$B16D
.pointer:
    LD DE,7
    ADD HL,DE
    LD (p_h_src),HL
    LD A,(p_h_index)
    CP 6
    LD B,3
    JR C,.position
    SUB 6
    LD B,15
.position:
    ADD A,A
    ADD A,A
    ADD A,A
    ADD A,22
    LD (p_w_x),A
    LD A,B
    LD (p_w_y),A
    CP 15
    JR NZ,.draw
    LD A,(p_h_codes+6)
    CP $50
    JR NZ,.draw
    LD A,($C071)
    OR A
    JR NZ,.draw
    LD A,($C001)
    AND 8
    JR NZ,.draw
    LD A,(p_bg_theme)
    AND 1
    LD A,132
    JR Z,.sky
    LD A,128
.sky:
    CALL p_world_color
.draw:
    LD A,8
    LD (p_h_height),A
    CALL presentation_glyph_prepare
    CALL p_world_primitive
    LD HL,p_h_index
    INC (HL)
    LD A,(HL)
    CP 12
    JP NZ,.glyph
    ; PF1 igloo consists of five independent literal8-bit block rows.
    LD A,6
    CALL p_world_color
    XOR A
    LD (p_h_level),A
.level:
    LD A,(p_h_level)
    LD E,A
    LD D,0
    LD HL,$C040
    ADD HL,DE
    LD A,(HL)
    LD (p_h_bits),A
    LD A,E
    ADD A,A
    ADD A,A
    LD B,A
    LD A,44
    SUB B
    LD (p_w_y),A
    LD A,112
    LD (p_w_x),A
    XOR A
    LD (p_h_bit),A
.block:
    LD HL,p_h_bits
    SRL (HL)
    JR NC,.next
    LD HL,p_h_solid+3
    LD (p_h_src),HL
    LD A,4
    LD (p_h_height),A
    CALL presentation_glyph_prepare
    CALL p_world_primitive
.next:
    LD A,(p_w_x)
    ADD A,4
    LD (p_w_x),A
    LD HL,p_h_bit
    INC (HL)
    LD A,(HL)
    CP 8
    JR NZ,.block
    LD HL,p_h_level
    INC (HL)
    LD A,(HL)
    CP 5
    JR NZ,.level
    RET

; Expand at most8 source rows into a3x2 mask grid in C480-C4AF. Source8-bit
; rows descend in ROM order; solid4x4 uses the same lossless expansion path.
presentation_glyph_prepare:
    LD A,1
    LD ($7000),A
    LD HL,$C480
    LD DE,$C481
    LD BC,47
    LD (HL),0
    LDIR
    LD A,3
    LD (p_w_family),A
    LD (p_geo_columns),A
    LD A,2
    LD (p_geo_rows),A
    LD A,12
    LD (p_geo_stride),A
    LD A,(p_w_y)
    AND 7
    LD (p_h_y),A
.row:
    LD A,(p_h_y)
    LD E,A
    AND 7
    LD L,A
    LD H,0
    BIT 3,E
    JR Z,.dest
    LD DE,24
    ADD HL,DE
.dest:
    LD DE,$C480
    ADD HL,DE
    PUSH HL
    LD HL,(p_h_src)
    LD E,(HL)
    DEC HL
    LD (p_h_src),HL
    LD D,0
    LD H,D
    LD L,E
    ADD HL,HL
    ADD HL,DE
    LD A,(p_w_x)
    AND 15
    LD E,A
    ADD A,A
    ADD A,E
    ADD A,$80
    ADD A,H
    LD H,A
    POP DE
    LD B,3
.column:
    LD A,(HL)
    LD (DE),A
    INC HL
    LD A,E
    ADD A,8
    LD E,A
    DJNZ .column
    LD HL,p_h_y
    INC (HL)
    LD HL,p_h_height
    DEC (HL)
    JR NZ,.row
    RET
p_h_solid:
    DB $F0,$F0,$F0,$F0
    ENDIF

p_h_footer_phase EQU $C244
p_h_footer_index EQU $C245
p_h_footer_row EQU $C246
presentation_footer_prepare:
    LD A,($C03F)
    BIT 7,A
    RET NZ
    LD A,($C046)
    AND 31
    SUB 12
    JR NC,.nonnegative
    XOR A
.nonnegative:
    CP 8
    JR C,.phase
    LD A,7
.phase:
    LD (p_h_footer_phase),A
    IFDEF WITH_PRESENTATION_FAST
    JP p_fast_footer_prepare
    ELSE
    LD A,12
    CALL p_world_color
    XOR A
    LD (p_h_footer_index),A
.prefix:
    LD A,(p_h_footer_phase)
    LD B,A
    INC A
    LD (p_h_height),A
    LD A,(p_h_footer_index)
    DUP 3
    ADD A,A
    EDUP
    ADD A,$90
    ADD A,B
    LD L,A
    LD H,$B3
    LD (p_h_src),HL
    LD A,(p_h_footer_index)
    DUP 3
    ADD A,A
    EDUP
    ADD A,22
    LD (p_w_x),A
    LD A,(p_w_coarse)
    ADD A,179
    LD (p_w_y),A
    CALL presentation_glyph_prepare
    CALL p_world_primitive
    LD HL,p_h_footer_index
    INC (HL)
    LD A,(HL)
    CP 6
    JR NZ,.prefix
    XOR A
    LD (p_h_footer_row),A
.row:
    LD A,1
    LD ($7000),A
    LD A,(p_h_footer_row)
    LD B,A
    LD A,$C7
    SUB B
    LD L,A
    LD H,$B3
    LD A,(HL)
    CALL p_world_color
    LD A,(p_h_footer_phase)
    LD B,A
    LD A,(p_h_footer_row)
    ADD A,B
    LD B,A
    LD A,(p_w_coarse)
    ADD A,B
    ADD A,181
    LD (p_w_y),A
    XOR A
    LD (p_h_footer_index),A
.piece:
    LD A,(p_h_footer_index)
    OR A
    LD A,20
    JR Z,.x
    LD A,(p_h_footer_index)
    CP 1
    LD A,28
    JR Z,.x
    LD A,(p_h_footer_row)
    LD B,A
    LD A,33
    SUB B
.x:
    LD (p_w_x),A
    LD HL,p_h_bar
    LD (p_h_src),HL
    LD A,1
    LD (p_h_height),A
    CALL presentation_glyph_prepare
    CALL p_world_primitive
    LD HL,p_h_footer_index
    INC (HL)
    LD A,(HL)
    CP 3
    JR NZ,.piece
    LD HL,p_h_footer_row
    INC (HL)
    LD A,(p_h_footer_phase)
    ADD A,(HL)
    CP 8
    JP NZ,.row
    RET
p_h_bar:
    DB $FF
    ENDIF
