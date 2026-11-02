; Complete original-control floe masks. Geometry is compiled; state stays live.
; Exclusive physical roles permit retaining published masks on an exact tuple.
p_tf_cursor EQU $C2F2
p_tf_row EQU $C2F3
p_tf_column EQU $C2F4
p_tf_identity EQU $C2F5
p_tf_start EQU $C2F7
p_tf_program_row EQU $C2F8
p_tf_namebase EQU $C2F9
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
    LD B,A
    LD A,(p_w_y)
    LD C,A
    LD A,(p_w_delta)
    LD D,A
    LD A,B
    LD B,D
    CALL p_template_load
    JP C,p_world_fail
    LD A,(p_w_row)
    LD E,A
    LD D,0
    LD HL,p_template_floe_bases
    ADD HL,DE
    LD A,(HL)
    LD (p_tf_base),A
    CALL p_fixed_dynamic_id
    LD (p_tf_namebase),A
    LD A,(p_tl_root)
    DUP 4
    SRL A
    EDUP
    LD B,A
    ADD A,A
    ADD A,B
    INC A
    LD (p_tf_start),A
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
    ADD A,$C0
    LD L,A
    LD H,$E5
    LD (p_tf_identity),HL
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
    ; Publish every local mask, including a mask currently hidden by an object
    ; or the left border. A later identity HIT can use any of its roles safely.
    LD A,(p_w_y)
    DUP 3
    SRL A
    EDUP
    LD (p_w_top),A
    XOR A
    LD (p_w_col),A
    LD (p_tf_cursor),A
    CALL p_fast_cell
    LD A,(p_w_y)
    CP 128
    LD A,pt_water_id1
    JR C,.water
    LD A,pt_water_id2
.water:
    LD (pf_key+2),A
    XOR A
    LD (pf_key+3),A
    LD A,(p_w_color)
    LD (pf_key+4),A
    LD A,9
    LD (pf_key+5),A
.mask:
    LD A,(p_tf_cursor)
    ADD A,A
    ADD A,p_tl_keys&255
    LD L,A
    LD H,p_tl_keys/256
    LD E,(HL)
    INC L
    LD D,(HL)
    LD (pf_key),DE
    LD A,(p_tf_cursor)
    LD B,A
    LD A,(p_tf_namebase)
    ADD A,B
    LD (p_fx_force),A
    CALL p_fixed_resolve
    JP C,p_world_fail
    LD HL,p_tf_cursor
    INC (HL)
    LD A,(p_tl_count)
    CP (HL)
    JR NZ,.mask
    LD HL,p_tf_tuple
    LD DE,(p_tf_identity)
    LD BC,4
    LDIR                    ;identity validity follows ALL completed uploads
.draw:
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
    JP Z,.next_row
    LD A,(p_tf_row)
    OR A
    LD A,0
    JR Z,.program_row
    LD A,30
.program_row:
    LD (p_tf_program_row),A
    XOR A
    LD (p_tf_column),A
    LD A,(p_tf_start)
    LD (p_w_col),A
    CALL p_fast_cell
.cell:
    LD A,(p_tf_column)
    LD B,A
    LD A,(p_tf_program_row)
    ADD A,B
    LD C,A
    SRL A
    ADD A,p_tl_names&255
    LD L,A
    LD H,p_tl_names/256
    LD A,(HL)
    BIT 0,C
    JR Z,.low
    DUP 4
    RRCA
    EDUP
.low:
    AND 15
    JR Z,.next_cell
    LD B,A
    LD A,(p_tl_count)
    CP B
    JP C,p_world_fail
    LD A,B
    DEC A
    LD (p_tf_slot),A
    LD A,(p_w_col)
    CP 2
    JR C,.next_cell
    LD HL,(p_w_name)
    LD A,(HL)
    CP 128
    JR C,.fused
    LD A,(p_tf_namebase)
    ADD A,B
    DEC A
    LD (HL),A
    JR .next_cell
.fused:
    CALL p_fast_old_key
    LD A,(pfw_old+5)
    OR A
    JP NZ,p_world_fail
    LD A,(p_w_top)
    CP 16
    LD E,p_fx_fuse1&255
    LD B,51
    JR C,.fusion_map
    LD E,p_fx_fuse2&255
    LD B,41
.fusion_map:
    LD A,(p_w_col)
    ADD A,E
    LD L,A
    LD H,p_fx_fuse1/256
    LD A,(HL)
    CP 9
    JP NC,p_world_fail
    ADD A,B
    CALL p_fixed_dynamic_id
    LD (p_fx_force),A
    CALL p_template_fused_key
    CALL p_fixed_put
.next_cell:
    LD HL,p_w_name
    INC (HL)
    LD HL,p_w_col
    INC (HL)
    LD A,(HL)
    CP 31
    JR C,.column_ready
    LD (HL),1
    CALL p_fast_cell
.column_ready:
    LD HL,p_tf_column
    INC (HL)
    LD A,(HL)
    CP 30
    JP C,.cell
.next_row:
    LD HL,p_tf_row
    INC (HL)
    LD A,(HL)
    CP 2
    JP C,.row
    RET

p_template_fused_key:
    LD A,(p_tf_slot)
    ADD A,A
    ADD A,p_tl_keys&255
    LD L,A
    LD H,p_tl_keys/256
    LD E,(HL)
    INC L
    LD D,(HL)
    CALL p_template_floe_pattern
    JP C,p_world_fail
    LD HL,$CC80
    LD DE,pfw_mask
    LD BC,8
    LDIR
    LD DE,(pfw_old)
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
    LD A,(pfw_old+4)
    DUP 4
    RLCA
    EDUP
    LD B,A
    LD A,(p_w_color)
    OR B
    LD (pf_key+3),A
    XOR A
    LD (pf_key+4),A
    RET

p_template_floe_bases:
    DB 25,9,35,19
