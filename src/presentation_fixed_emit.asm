; Intern the FINAL complete strip in stable row/column order, including cells
; outside this dirty transaction. Publish only dirty rows of the inactive page.
p_fe_index EQU $C2FB
p_fe_base EQU $C2FC
p_fe_slot EQU $C2FD
p_fe_seen EQU $E2F0

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
    CALL p_fixed_floe_build
    JP C,p_world_fail
    CALL p_fixed_pool_init
    LD HL,p_fe_seen
    LD DE,p_fe_seen+1
    LD BC,15
    LD (HL),0
    LDIR
    LD A,(p_w_row)
    LD E,A
    LD D,0
    LD HL,p_fixed_floe_bases
    ADD HL,DE
    LD A,(HL)
    LD (p_fe_base),A
    XOR A
    LD (p_fe_index),A
.cell:
    LD A,(p_fe_index)
    LD L,A
    LD H,p_ff_counts/256
    LD A,(HL)
    OR A
    JP Z,.next
    LD B,A
    LD A,L
    ADD A,A
    LD L,A
    LD H,p_ff_first/256
    LD E,(HL)
    INC L
    LD D,(HL)
    LD (p_fp_key),DE
    LD DE,0
    LD A,B
    CP 2
    JR NZ,.pair
    DEC L
    LD H,p_ff_second/256
    LD E,(HL)
    INC L
    LD D,(HL)
.pair:
    LD (p_fp_key+2),DE
    CALL p_fixed_pool_resolve
    JP C,p_world_fail
    LD B,A
    LD A,(p_fe_base)
    ADD A,B
    LD (p_fe_slot),A
    LD A,(p_fe_index)
    AND 32
    DUP 5
    RRCA
    EDUP
    LD B,A
    LD A,(p_w_y)
    DUP 3
    SRL A
    EDUP
    ADD A,B
    LD (p_w_top),A
    CALL p_fast_row_dirty
    JP Z,.next
    LD A,(p_fe_index)
    AND 31
    LD (p_w_col),A
    CALL p_fast_cell
    LD HL,(p_w_name)
    LD A,(HL)
    CP 128
    JR C,.fused
    LD A,(p_fe_slot)
    LD B,A
    LD A,(p_fe_base)
    LD C,A
    LD A,B
    SUB C
    ADD A,p_fe_seen&255
    LD L,A
    LD H,p_fe_seen/256
    LD A,(HL)
    OR A
    JR Z,.publish
    LD A,B
    CALL p_fixed_dynamic_id
    LD HL,(p_w_name)
    LD (HL),A
    JP .next
.publish:
    INC (HL)
    CALL p_fixed_floe_key
    LD A,(p_fe_slot)
    CALL p_fixed_dynamic_id
    LD (p_fx_force),A
    CALL p_fixed_put
    JP .next
.fused:
    CALL p_fast_old_key
    LD A,(pfw_old+5)
    OR A
    JP NZ,p_world_fail
    LD A,(p_w_top)
    CP 16
    LD E,p_fx_fuse1&255
    LD B,51
    JR C,.fuse_map
    LD E,p_fx_fuse2&255
    LD B,41
.fuse_map:
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
    CALL p_fixed_floe_fused_key
    CALL p_fixed_put
.next:
    LD HL,p_fe_index
    INC (HL)
    LD A,(HL)
    CP 64
    JP C,.cell
    RET

p_fixed_floe_key:
    LD HL,(p_fp_key)
    LD (pf_key),HL
    LD HL,(p_fp_key+2)
    LD A,H
    OR L
    JR NZ,.union
    LD A,(p_w_top)
    CP 16
    LD A,pt_water_id1
    JR C,.water
    LD A,pt_water_id2
.water:
    LD (pf_key+2),A
    XOR A
    LD (pf_key+3),A
    LD (pf_key+5),A
    LD A,(p_w_color)
    LD (pf_key+4),A
    RET
.union:
    LD (pf_key+2),HL
    LD A,(p_w_color)
    DUP 4
    RLCA
    EDUP
    OR 4
    LD (pf_key+4),A
    LD A,7
    LD (pf_key+5),A
    RET

p_fixed_floe_fused_key:
    LD DE,(p_fp_key)
    CALL presentation_geometry_pattern
    JP C,p_world_fail
    LD HL,$CC80
    LD DE,pfw_mask
    LD BC,8
    LDIR
    LD DE,(p_fp_key+2)
    LD A,D
    OR E
    JR Z,.object
    CALL presentation_geometry_pattern
    JP C,p_world_fail
    LD HL,$CC80
    LD DE,pfw_mask
    LD B,8
.merge:
    LD A,(DE)
    OR (HL)
    LD (DE),A
    INC DE
    INC HL
    DJNZ .merge
.object:
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

p_fixed_floe_bases:
    DB 25,9,35,19
