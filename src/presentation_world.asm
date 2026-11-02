; Read-only P1 foreground compositor. Correctness candidate: full inactive-page
; reconstruction, exact16-byte cache; not a qualified complete-frame budget.
p_w_x EQU $C220
p_w_y EQU $C221
p_w_color EQU $C222
p_w_coarse EQU $C223
p_w_row EQU $C224
p_w_copy EQU $C225
p_w_group EQU $C226
p_w_family EQU $C227
p_w_origin EQU $C228
p_w_col EQU $C229
p_w_top EQU $C22A
p_w_line EQU $C22B
p_w_index EQU $C22C
p_w_name EQU $C22D
p_w_tile EQU $C22F
p_w_cachegroup EQU $C230
p_w_fault EQU $C231
p_w_delta EQU $C232
p_w_base EQU $C233
p_w_mode EQU $C234
p_w_plane EQU $C243
p_w_mask EQU $CC90

presentation_world_prepare:
    XOR A
    LD (p_w_fault),A
    LD A,($C03F)
    BIT 7,A
    RET NZ
    LD A,($C068)
    CP 150
    LD A,0
    ADC A,0
    XOR 1
    LD (p_w_coarse),A
    ; Source bear P1 origin includes the coarse-reset left-edge correction.
    LD A,($C068)
    LD B,1
    CP 15
    JR NC,.bear_x
    LD B,6
.bear_x:
    ADD A,B
    CALL normalize_x
    LD (p_w_x),A
    LD A,(p_w_coarse)
    ADD A,51
    LD (p_w_y),A
    LD A,($C06F)
    ADD A,A
    LD B,A
    LD A,($C06C)
    AND 16
    RRCA
    RRCA
    RRCA
    RRCA
    OR B
    LD (p_w_group),A
    LD A,(p_bg_theme)
    AND 1
    LD B,A
    LD A,($C04B)
    CP 3
    LD A,10
    JR C,.bear_shore
    LD A,4
    DEC B
    JR NZ,.bear_color
    LD A,12
    JR .bear_color
.bear_shore:
    DEC B
    JR NZ,.bear_color
    LD A,2
.bear_color:
    CALL p_world_color
    LD A,2
    LD (p_w_family),A
    CALL p_world_primitive
    ; Objects and floes use canonical row selectors, copy modes and motion.
    XOR A
    LD (p_w_row),A
.row:
    LD A,1
    LD ($7000),A
    LD A,(p_w_row)
    LD E,A
    LD D,0
    LD HL,$C023
    ADD HL,DE
    LD L,(HL)
    LD H,p_geo_row_map_data/256
    LD A,(HL)
    CP 33
    JP NC,p_world_fail
    ADD A,A
    LD B,A
    LD HL,$C011
    ADD HL,DE
    LD A,(HL)
    RLCA
    AND 1
    OR B
    LD (p_w_group),A
    LD HL,$C027
    ADD HL,DE
    LD A,(HL)
    CALL p_world_color
    LD A,(p_w_row)
    LD E,A
    LD D,0
    LD HL,$C058
    ADD HL,DE
    LD A,(HL)
    CP 4
    JP NC,p_world_fail
    LD (p_w_mode),A
    LD HL,$C054
    ADD HL,DE
    LD A,(HL)
    LD (p_w_base),A
    XOR A
    LD (p_w_copy),A
    LD (p_w_family),A
.object:
    LD A,(p_w_mode)
    ADD A,A
    ADD A,A
    LD E,A
    LD D,0
    LD HL,p_world_copies
    ADD HL,DE
    LD A,(p_w_copy)
    LD E,A
    ADD HL,DE
    LD A,(HL)
    CP 255
    JR Z,.floes
    LD B,A
    LD A,(p_w_base)
    ADD A,B
    CALL normalize_x
    LD (p_w_x),A
    CALL p_world_row_y
    ADD A,153
    LD (p_w_y),A
    CALL p_world_primitive
    LD HL,p_w_copy
    INC (HL)
    JR .object
.floes:
    LD A,($C01D)
    AND 2
    JP NZ,p_world_fail
    LD A,($C01C)
    CALL p_world_nibble
    LD B,A
    LD A,($C01D)
    CALL p_world_nibble
    LD C,A
    LD A,B
    SUB C
    ADD A,4
    LD (p_w_delta),A
    CP 9
    JR C,.union
    XOR A                   ;separated source segments retain their gap
.union:
    LD (p_w_group),A
    XOR A
    LD (p_w_plane),A
    LD A,(p_w_row)
    LD E,A
    LD D,0
    LD HL,$C01F
    ADD HL,DE
    LD A,(HL)
    SUB B
    SUB 8
    JR NC,.anchor
    ADD A,160
.anchor:
    CALL normalize_x
    LD (p_w_base),A
    LD HL,$C02B
    ADD HL,DE
    LD A,(HL)
    CALL p_world_color
    LD A,1
    LD (p_w_family),A
    XOR A
    LD (p_w_copy),A
.floe:
    LD A,(p_w_copy)
    DUP 5
    ADD A,A
    EDUP
    LD B,A
    LD A,(p_w_base)
    ADD A,B
    CALL normalize_x
    LD (p_w_x),A
    CALL p_world_row_y
    ADD A,167
    LD (p_w_y),A
    CALL p_world_primitive
    LD HL,p_w_copy
    INC (HL)
    LD A,(HL)
    CP 3
    JR NZ,.floe
    LD A,(p_w_delta)
    CP 9
    JR C,.row_done
    LD A,(p_w_plane)
    OR A
    JR NZ,.row_done
    INC A
    LD (p_w_plane),A
    LD A,(p_w_delta)
    LD B,A
    LD A,(p_w_base)
    ADD A,B
    CALL normalize_x
    LD (p_w_base),A
    XOR A
    LD (p_w_copy),A
    JP .floe
.row_done:
    LD HL,p_w_row
    INC (HL)
    LD A,(HL)
    CP 4
    JP NZ,.row
    RET

p_world_row_y:
    LD A,(p_w_row)
    LD E,A
    LD D,0
    LD HL,p_world_row_offsets
    ADD HL,DE
    LD A,(p_w_coarse)
    ADD A,(HL)
    RET
p_world_nibble:
    DUP 4
    SRA A
    EDUP
    RET
p_world_color:
    PUSH DE
    LD E,A
    LD A,1
    LD ($7000),A
    LD D,0
    LD HL,p_world_color_data
    ADD HL,DE
    LD A,(HL)
    LD (p_w_color),A
    POP DE
    RET

p_world_primitive:
    IFDEF WITH_PRESENTATION_FAST
    LD A,(p_w_family)
    CP 3
    JP Z,p_world_fail
    CP 2
    JR NC,.fast_visible
    LD A,(p_w_color)
    CP 4
    RET Z
.fast_visible:
    ENDIF
    LD A,(p_w_family)
    CP 3
    JR Z,.ready
    LD A,(p_w_x)
    AND 15
    LD B,A
    LD A,(p_w_family)
    CP 2
    LD A,B
    JR Z,.bear_phase
    ADD A,A
    ADD A,A
    ADD A,A
    LD B,A
    LD A,(p_w_y)
    AND 7
    OR B
    JR .lookup
.bear_phase:
    ADD A,A
    LD B,A
    LD A,(p_w_coarse)
    OR B
.lookup:
    LD C,A
    LD A,(p_w_group)
    LD B,A
    LD A,(p_w_family)
    CALL presentation_geometry_lookup
    JP C,p_world_fail
.ready:
    LD A,(p_w_x)
    LD L,A
    LD H,0
    LD D,H
    LD E,L
    ADD HL,HL
    ADD HL,DE
    SRL H
    RR L
    LD DE,8
    ADD HL,DE
    DUP 3
    SRL H
    RR L
    EDUP
    LD A,L
    LD (p_w_origin),A
    LD (p_w_col),A
    LD A,(p_w_y)
    DUP 3
    SRL A
    EDUP
    LD (p_w_top),A
    XOR A
    LD (p_w_index),A
    LD (p_w_line),A
.tile:
    LD A,(p_w_col)
    CP 31
    JR C,.column
    SUB 30
    LD (p_w_col),A
.column:
    CP 1
    JR Z,.next
    OR A
    JR Z,.next
    IFDEF WITH_PRESENTATION_FAST
    LD A,(p_w_index)
    ADD A,A
    LD E,A
    LD D,0
    LD HL,p_geo_ids
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    CALL p_fast_world_tile
    JP .next
    ELSE
    LD A,(p_w_family)
    CP 3
    JR Z,.glyph
    LD A,(p_w_index)
    ADD A,A
    LD E,A
    LD D,0
    LD HL,p_geo_ids
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    CALL presentation_geometry_pattern
    JP C,p_world_fail
    LD HL,$CC80
    JR .copy
.glyph:
    LD A,(p_w_index)
    LD L,A
    LD H,0
    ADD HL,HL
    ADD HL,HL
    ADD HL,HL
    LD DE,$C480
    ADD HL,DE
.copy:
    LD DE,p_w_mask
    LD BC,8
    LDIR
    LD A,(p_w_col)
    CP 2
    CALL Z,p_world_clip
    LD HL,p_w_mask
    LD B,8
    XOR A
.nonzero:
    OR (HL)
    INC HL
    DJNZ .nonzero
    CALL NZ,p_world_merge
    ENDIF
.next:
    LD HL,p_w_index
    INC (HL)
    LD A,(p_w_index)
    LD B,A
    LD A,(p_geo_stride)
    SRL A
    CP B
    RET Z
    LD HL,p_w_col
    INC (HL)
    LD HL,p_w_line
    INC (HL)
    LD A,(p_geo_columns)
    CP (HL)
    JP NZ,.tile
    LD (HL),0
    LD HL,p_w_top
    INC (HL)
    LD A,(p_w_origin)
    LD (p_w_col),A
    JP .tile
p_world_clip:
    LD HL,p_w_mask
    LD B,8
.row:
    LD A,(HL)
    AND 15
    LD (HL),A
    INC HL
    DJNZ .row
    RET

; Load exact old tile; merge the new monochrome fragment row by row. A third
; actual color traps instead of approximating. New cache misses upload only
; this inactive generation's8pattern+8color bytes.
p_world_merge:
    IFDEF WITH_PRESENTATION_FAST
    JP p_world_fail
    ELSE
    LD A,(p_w_top)
    CP 24
    RET NC
    LD L,A
    LD H,0
    DUP 5
    ADD HL,HL
    EDUP
    LD A,(p_w_col)
    LD E,A
    LD D,0
    ADD HL,DE
    LD A,(PAGE)
    OR A
    LD DE,$C800
    JR Z,.names
    LD D,$CD
.names:
    ADD HL,DE
    LD (p_w_name),HL
    LD A,(HL)
    LD (p_w_tile),A
    LD A,(p_w_top)
    DUP 3
    SRL A
    EDUP
    LD B,A
    LD A,(PAGE)
    LD C,A
    ADD A,A
    ADD A,C
    ADD A,B
    LD (p_w_cachegroup),A
    LD A,(p_w_tile)
    CP 128
    JR NC,.static
    AND 63
    LD L,A
    LD H,0
    DUP 4
    ADD HL,HL
    EDUP
    LD A,(p_w_cachegroup)
    ADD A,A
    ADD A,A
    ADD A,$D0
    ADD A,H
    LD H,A
    LD DE,$CC80
    LD BC,16
    LDIR
    JR .merge
.static:
    SUB 128
    LD L,A
    LD H,0
    ADD HL,HL
    ADD HL,HL
    ADD HL,HL
    PUSH HL
    LD A,1
    LD ($7000),A
    LD A,B
    ADD A,A
    ADD A,A
    LD E,A
    LD D,0
    PUSH DE
    LD HL,p_world_bg_roots
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    POP BC
    POP HL
    PUSH HL
    ADD HL,DE
    LD DE,$CC80
    PUSH BC
    LD BC,8
    LDIR
    POP DE
    LD HL,p_world_bg_roots+2
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    POP HL
    ADD HL,DE
    LD DE,$CC88
    LD BC,8
    LDIR
.merge:
    LD IX,$CC80
    LD IY,p_w_mask
    LD B,8
.row:
    LD A,(IY)
    OR A
    JR Z,.row_next
    LD E,A
    LD A,(IX+8)
    AND 15
    LD C,A
    LD A,(IX+8)
    DUP 4
    RRCA
    EDUP
    AND 15
    LD D,A
    LD A,(p_w_color)
    CP D
    JR Z,.foreground
    CP C
    JR Z,.background
    LD A,D
    CP C
    JR Z,.replace
    LD A,E
    CPL
    AND (IX)
    JR Z,.replace
    LD A,(IX)
    OR E
    INC A
    JP NZ,p_world_fail
    LD C,D
.replace:
    LD A,(p_w_color)
    DUP 4
    RLCA
    EDUP
    OR C
    LD (IX+8),A
    LD (IX),E
    JR .row_next
.foreground:
    LD A,(IX)
    OR E
    LD (IX),A
    JR .row_next
.background:
    LD A,E
    CPL
    AND (IX)
    LD (IX),A
.row_next:
    INC IX
    INC IY
    DJNZ .row
    LD A,(p_w_cachegroup)
    CALL presentation_cache_tile
    JP C,p_world_fail
    LD (p_w_tile),A
    LD HL,(p_w_name)
    LD (HL),A
    LD A,(p_cache_miss)
    OR A
    RET Z
    LD A,(p_w_tile)
    LD L,A
    LD H,0
    ADD HL,HL
    ADD HL,HL
    ADD HL,HL
    LD A,(p_w_top)
    AND 24
    ADD A,$40
    ADD A,H
    LD H,A
    EX DE,HL
    PUSH DE
    LD HL,$CC80
    LD B,8
    CALL vdp_write
    POP DE
    LD A,D
    ADD A,$20
    LD D,A
    LD HL,$CC88
    LD B,8
    JP vdp_write

    ENDIF
p_world_fail:
    LD A,1
    LD (p_w_fault),A
    RET
p_world_copies:
    DB 0,255,255,255,0,16,255,255,0,32,255,255,0,16,32,255
p_world_row_offsets:
    DB 0,-26,-52,-78
p_world_bg_roots:
    DW p_bg_patterns0_data,p_bg_colors0_data
    DW p_bg_patterns1_data,p_bg_colors1_data
    DW p_bg_patterns2_data,p_bg_colors2_data
