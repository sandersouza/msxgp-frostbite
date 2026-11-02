; Complete original-control floe masks. Geometry is compiled; state stays live.
; Exclusive physical roles permit retaining published masks on an exact tuple.
p_tf_cursor EQU $C2F2
p_tf_row EQU $C2F3
p_tf_column EQU $C2F4
p_tf_identity EQU $C2F5
p_tf_water EQU $C2F8
p_tf_namebase EQU $C2F9
p_tf_cache EQU $C2FA
p_tf_base EQU $C2FC
p_tf_slot EQU $C2FD
p_tf_tuple EQU $E2E0

p_fixed_floe_prepare:
    LD A,($C01D)
    AND 2
    JP NZ,p_world_fail
    LD A,(p_w_row)
    LD E,A
    LD D,0
    LD HL,$C02B
    ADD HL,DE
    LD A,(HL)
    CALL p_world_color
    LD A,(p_w_color)
    CP 4
    RET Z
    CALL p_world_row_y
    ADD A,167
    LD (p_w_y),A
    LD A,1
    LD (p_w_family),A
    CALL p_fast_primitive_dirty
    RET Z
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
    LD A,B
    ADD A,A
    SBC A,A
    LD D,A
    LD E,B
    LD A,(p_w_row)
    LD L,A
    LD H,0
    LD BC,$C01F
    ADD HL,BC
    LD L,(HL)
    LD H,0
    OR A
    SBC HL,DE
    BIT 7,H
    JR Z,.positive
    LD DE,160
    ADD HL,DE
.positive:
    LD A,L
    CP 160
    JR C,.root
    SUB 160
.root:
    LD (p_tl_root),A
    LD A,(p_w_y)
    LD (p_tl_y),A
    LD A,(p_w_delta)
    LD (p_tl_delta),A
    LD A,(p_tl_root)
    AND 15
    LD (p_tf_tuple),A
    LD A,(p_tl_delta)
    LD (p_tf_tuple+1),A
    LD A,(p_tl_y)
    AND 7
    LD (p_tf_tuple+2),A
    LD A,(p_w_color)
    LD (p_tf_tuple+3),A
    LD A,(PAGE)
    DUP 4
    ADD A,A
    EDUP
    LD B,A
    LD A,(p_w_row)
    ADD A,A
    ADD A,A
    ADD A,B
    LD E,A
    ADD A,$C0
    LD L,A
    LD H,$E5
    LD (p_tf_identity),HL
    LD L,E
    LD H,0
    DUP 4
    ADD HL,HL
    EDUP
    LD DE,$DE00
    ADD HL,DE
    LD (p_tf_cache),HL
    LD HL,(p_tf_identity)
    LD DE,p_tf_tuple
    LD B,4
.identity:
    LD A,(DE)
    CP (HL)
    JR NZ,.publish
    INC DE
    INC HL
    DJNZ .identity
    JP .draw
.publish:
    LD A,(p_tl_delta)
    LD B,A
    LD A,(p_tl_y)
    LD C,A
    LD A,(p_tl_root)
    CALL p_template_load
    JP C,p_world_fail
    CALL p_template_strip_publish
    JP C,p_world_fail
    ; Expand the compiled local codes ONCE into this generation's immutable
    ; sixty-byte NAME template. Other roles never write its cache or tiles.
    LD HL,p_tl_names
    LD DE,(p_tf_cache)
    LD A,(p_tf_namebase)
    DEC A
    LD C,A
    XOR A
    LD (p_tf_cursor),A
.cache_byte:
    LD A,(HL)
    LD B,A
    AND 15
    JR Z,.lower_background
    ADD A,C
    JR .lower
.lower_background:
    LD A,(p_tf_water)
.lower:
    LD (DE),A
    INC DE
    LD A,B
    DUP 4
    RRCA
    EDUP
    AND 15
    JR Z,.upper_background
    ADD A,C
    JR .upper
.upper_background:
    LD A,(p_tf_water)
.upper:
    LD (DE),A
    INC DE
    INC HL
    PUSH HL
    LD HL,p_tf_cursor
    INC (HL)
    LD A,(HL)
    POP HL
    CP 30
    JR NZ,.cache_byte
    LD HL,p_tf_tuple
    LD DE,(p_tf_identity)
    LD BC,4
    LDIR                    ;identity follows every tile AND completed NAME cache
.draw:
    LD A,(p_w_y)
    AND 7
    CP 2
    LD A,1
    JR C,.row_count
    INC A
.row_count:
    LD (p_tf_column),A       ;seven source rows occupy one or two SCREEN2 rows
    XOR A
    LD (p_tf_row),A
.row:
    LD A,(p_tf_row)
    LD B,A
    LD A,(p_w_y)
    DUP 3
    SRL A
    EDUP
    ADD A,B
    LD (p_w_top),A
    CALL p_fast_row_dirty
    JR Z,.next_row
    XOR A
    LD (p_w_col),A
    CALL p_fast_cell
    LD DE,(p_w_name)
    LD HL,(p_tf_cache)
    LD A,(p_tf_row)
    OR A
    JR Z,.copy
    LD BC,30
    ADD HL,BC
.copy:
    LD A,(p_tl_root)
    CALL p_template_name_row
    JP C,p_world_fail
.next_row:
    LD HL,p_tf_row
    INC (HL)
    LD A,(p_tf_column)
    CP (HL)
    JR NZ,.row
    RET

; The shared scanline sets are disjoint. Objects can therefore be fused after
; complete floes without changing a mapped pixel or source update ordering.
p_template_object_fuse:
    LD A,(p_w_family)
    OR A
    JP NZ,p_world_fail
    CALL p_fast_old_key
    LD A,(pfw_old+5)
    CP 9
    JP NZ,p_world_fail
    LD A,(p_w_top)
    CP 16
    LD D,51
    JR C,.base
    LD D,41
.base:
    LD A,(p_w_copy)
    LD B,A
    ADD A,A
    ADD A,B
    LD B,A
    LD A,(p_w_line)
    ADD A,B
    ADD A,D
    CALL p_fixed_dynamic_id
    LD (p_fx_force),A
    LD DE,(pfw_old)
    CALL p_template_floe_pattern
    JP C,p_world_fail
    LD HL,$CC80
    LD DE,pfw_mask
    LD BC,8
    LDIR
    LD DE,(pfw_id)
    CALL presentation_geometry_pattern
    JP C,p_world_fail
    CALL p_fast_shared_kind
    OR A
    JP Z,p_world_fail
    LD (pf_key+5),A
    CP 1
    JR NZ,.other
    LD A,($CC80)
    LD (pf_key),A
    LD A,(pfw_mask+7)
    LD (pf_key+1),A
    XOR A
    LD (pf_key+2),A
    JR .colour
.other:
    CP 2
    JR NZ,.coarse
    LD A,(pfw_mask)
    LD (pf_key),A
    LD A,(pfw_mask+1)
    LD (pf_key+1),A
    LD A,($CC87)
    LD (pf_key+2),A
    JR .colour
.coarse:
    LD A,(pfw_mask)
    LD (pf_key),A
    LD A,($CC86)
    LD (pf_key+1),A
    LD A,($CC87)
    LD (pf_key+2),A
.colour:
    LD A,(p_w_color)
    DUP 4
    RLCA
    EDUP
    LD B,A
    LD A,(pfw_old+4)
    OR B
    LD (pf_key+3),A
    XOR A
    LD (pf_key+4),A
    JP p_fixed_put

