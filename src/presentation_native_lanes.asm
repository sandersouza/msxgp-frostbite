    INCLUDE "symbols.inc"
    ORG $F400
x_world:
    ; Original bear/coarse prologue has completed. Snapshot reads are F000.
    LD A,($F01C)
    CALL p_world_nibble
    LD (p_w_plane),A
    LD B,A
    LD A,($F01D)
    CALL p_world_nibble
    LD C,A
    LD A,B
    SUB C
    ADD A,4
    LD (p_w_delta),A
    SUB 7
    JR NC,.delta
    XOR A
.delta:
    LD (p_tl_delta_index),A
.floes:
    CALL x_floe
    LD HL,p_w_row
    INC (HL)
    LD A,(HL)
    CP 4
    JR NZ,.floes
    XOR A
    LD (p_w_row),A
.actors:
    CALL x_actor
    LD HL,p_w_row
    INC (HL)
    LD A,(HL)
    CP 4
    JR NZ,.actors
    RET

x_floe:
    LD A,(p_w_row)
    LD E,A
    LD D,0
    LD HL,$F02B
    ADD HL,DE
    LD A,(HL)
    CALL p_world_color
    CP 4
    RET Z
    CALL p_world_row_y
    ADD A,167
    LD (p_w_y),A
    LD (p_tl_y),A
    LD A,1
    LD (p_w_family),A
    CALL x_span_dirty
    RET Z
    LD A,(p_w_row)
    LD E,A
    LD D,0
    LD HL,$F01F
    ADD HL,DE
    LD L,(HL)
    LD H,0
    LD A,(p_w_plane)
    LD E,A
    ADD A,A
    SBC A,A
    LD D,A
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
    AND 15
    LD (p_tf_tuple),A
    LD A,(p_w_delta)
    LD (p_tf_tuple+1),A
    LD (p_tl_delta),A
    LD A,(p_w_y)
    AND 7
    LD (p_tf_tuple+2),A
    LD A,(p_w_color)
    LD (p_tf_tuple+3),A
    LD A,(p_tf_tuple+2)
    LD B,A
    ADD A,A
    ADD A,A
    ADD A,B
    ADD A,A
    LD B,A
    LD A,(p_tl_delta_index)
    ADD A,B
    ADD A,35
    LD (pk_bank),A
    LD A,(p_tf_tuple)
    LD L,A
    LD H,0
    DUP 7
    ADD HL,HL
    EDUP
    LD DE,$B800
    ADD HL,DE
    LD (pk_pointer),HL
    CALL x_owner
    ADD A,A
    ADD A,A
    ADD A,$C0
    LD L,A
    LD H,$E5
    LD (p_tf_identity),HL
    LD DE,p_tf_tuple
    LD B,4
.match:
    LD A,(DE)
    CP (HL)
    JR NZ,.upload
    INC DE
    INC HL
    DJNZ .match
    JR .names
.upload:
    LD A,(p_w_row)
    LD E,A
    LD D,0
    LD HL,p_template_strip_bases
    ADD HL,DE
    LD B,(HL)
    LD A,(PAGE)
    DUP 6
    ADD A,A
    EDUP
    OR B
    LD (p_w_tile),A
    LD A,(p_w_row)
    CP 2
    LD A,2
    JR C,.bank
    DEC A
.bank:
    LD (p_fx_bank),A
    LD A,(pk_bank)
    CALL t_mapper
    LD HL,(pk_pointer)
    LD DE,112
    ADD HL,DE
    LD DE,pk_pending
    LD BC,4
    LDIR
    LD A,(pk_pending+3)
    LD (p_tl_count),A
    CALL x_owner
    ADD A,A
    ADD A,A
    ADD A,pk_records&255
    LD L,A
    LD H,pk_records/256
    LD (pk_ownerptr),HL
    LD A,7
    CALL t_mapper
    CALL pk_publish
    LD HL,p_tf_tuple
    LD DE,(p_tf_identity)
    LD BC,4
    LDIR
.names:
    LD A,(pk_bank)
    CALL t_mapper
    LD HL,(pk_pointer)
    LD A,(PAGE)
    LD E,A
    ADD A,A
    ADD A,E
    ADD A,117
    LD E,A
    LD D,0
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    INC HL
    LD A,(HL)
    LD (p_tf_cache),DE
    CALL t_mapper
    LD A,(p_w_y)
    AND 7
    CP 2
    LD A,1
    JR C,.count
    INC A
.count:
    LD (p_tf_column),A
    XOR A
    LD (p_tf_row),A
.row:
    LD A,(p_w_y)
    DUP 3
    SRL A
    EDUP
    LD B,A
    LD A,(p_tf_row)
    ADD A,B
    LD (p_w_top),A
    CALL x_row_dirty
    JR Z,.next
    ; Absolute inactive NAME row; public cell ABI is unnecessary here.
    LD A,(p_w_top)
    LD L,A
    LD H,0
    DUP 5
    ADD HL,HL
    EDUP
    LD A,(PAGE)
    OR A
    LD DE,$C800
    JR Z,.page
    LD D,$CD
.page:
    ADD HL,DE
    EX DE,HL
    LD HL,(p_tf_cache)
    LD A,(p_tf_row)
    OR A
    JR Z,.copy
    LD BC,30
    ADD HL,BC
.copy:
    CALL x_name_row
.next:
    LD HL,p_tf_row
    INC (HL)
    LD A,(p_tf_column)
    CP (HL)
    JR NZ,.row
    RET

x_owner:
    LD A,(PAGE)
    ADD A,A
    ADD A,A
    LD B,A
    LD A,(p_w_row)
    ADD A,B
    RET

x_name_row:
    LD A,(p_tl_root)
    DUP 4
    SRL A
    EDUP
    LD B,A
    ADD A,A
    ADD A,B
    LD C,A
    LD B,0
    PUSH DE
    LD A,128
    LD (DE),A
    INC DE
    PUSH HL
    PUSH BC
    LD A,30
    SUB C
    LD C,A
    ADD HL,BC
    POP BC
    LD A,C
    OR A
    JR Z,.head
    LDIR
.head:
    POP HL
    LD A,E
    AND 31
    LD C,A
    LD A,31
    SUB C
    LD C,A
    LD B,0
    LDIR
    LD A,128
    LD (DE),A
    POP DE
    INC DE
    LD (DE),A
    RET

x_actor:
    LD A,(p_w_row)
    LD E,A
    LD D,0
    LD HL,$F027
    ADD HL,DE
    LD A,(HL)
    CALL p_world_color
    CP 4
    RET Z
    LD HL,$F023
    ADD HL,DE
    LD L,(HL)
    LD H,p_geo_row_map_data/256
    LD A,(HL)
    ADD A,A
    LD B,A
    LD HL,$F011
    ADD HL,DE
    LD A,(HL)
    RLCA
    AND 1
    OR B
    LD (p_w_group),A
    LD HL,$F058
    ADD HL,DE
    LD A,(HL)
    LD (p_w_mode),A
    LD HL,$F054
    ADD HL,DE
    LD A,(HL)
    LD (p_w_base),A
    LD (p_w_x),A
    CALL p_world_row_y
    ADD A,153
    LD (p_w_y),A
    XOR A
    LD (p_w_family),A
    LD A,7
    CALL t_mapper
    CALL $A50D
    RET C
    CALL x_span_dirty
    RET Z
    XOR A
    LD (i_valid),A
    LD (p_w_copy),A
    CALL p_fast_clear_memo
    LD A,1
    LD (i_active),A
    LD A,(p_w_x)
    AND 15
    DUP 3
    ADD A,A
    EDUP
    LD B,A
    LD A,(p_w_y)
    AND 7
    OR B
    LD C,A
    LD A,(p_w_group)
    LD B,A
    CALL v_geometry
    CALL qe_bulk
.copy:
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
    JP Z,.done
    LD B,A
    LD A,(p_w_base)
    ADD A,B
    CALL normalize_x
    LD (p_w_x),A
    LD L,A
    LD H,0
    LD D,H
    LD E,L
    ADD HL,HL
    ADD HL,DE
    DUP 4
    SRL H
    RR L
    EDUP
    INC L
    LD A,L
    LD (qe_origin),A
    LD A,(p_w_y)
    DUP 3
    SRL A
    EDUP
    LD (p_w_top),A
    XOR A
    LD (qe_row),A
    LD (p_w_index),A
.row:
    LD A,(p_w_top)
    CALL x_row_dirty
    JP Z,.nextrow
    XOR A
    LD (p_w_col),A
    CALL p_fast_cell
    LD HL,(p_w_name)
    LD (qe_rowbase),HL
    LD A,(qe_row)
    LD B,A
    LD A,(p_w_row)
    CP 1
    JR NZ,.segment
    LD A,(p_w_coarse)
    OR A
    JR Z,.segment
    LD B,1
.segment:
    LD HL,(qe_rolesptr)
    LD DE,4
    ADD HL,DE
    LD A,B
    OR A
    JR Z,.role
    LD DE,6
    ADD HL,DE
.role:
    LD E,(HL)
    LD A,E
    LD (qe_roleid),A
    LD A,(qe_origin)
    LD D,A
    LD HL,(qe_rowbase)
    LD C,A
    LD B,0
    ADD HL,BC
    LD A,(p_geo_columns)
    LD B,A
    LD A,(v_mask)
    LD C,A
    LD A,(qe_row)
    OR A
    JR Z,.mask
    PUSH BC
.shift:
    SRL C
    DJNZ .shift
    POP AF                 ;restore column count from saved B (AF high byte)
    LD B,A
.mask:
.cell:
    SRL C
    JR NC,.nextcell
    LD A,D
    CP 2
    JR C,.nextcell
    LD A,(HL)
    CP 128
    JR C,.fuse
    LD (HL),E
    LD A,E
    LD (p_w_tile),A
    JR .nextcell
.fuse:
    LD (p_w_name),HL
    LD A,D
    LD (p_w_col),A
    LD A,(qe_roleid)
    NEG
    ADD A,E
    LD (p_w_line),A
    PUSH BC
    PUSH DE
    PUSH HL
    LD A,(p_w_group)
    LD B,A
    LD A,(pfw_geo_variant)
    LD C,A
    XOR A
    CALL qe_geometry
    LD A,(p_w_line)
    LD B,A
    LD A,(p_w_index)
    ADD A,B
    ADD A,A
    LD L,A
    LD H,0
    LD DE,p_geo_ids
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    LD (pfw_id),DE
    CALL qe_fuse
    POP HL
    POP DE
    POP BC
    JP C,p_world_fail
.nextcell:
    INC E
    INC D
    LD A,D
    CP 31
    JR C,.advance
    LD D,1
    LD HL,(qe_rowbase)
    INC HL
    JR .pointer
.advance:
    INC HL
.pointer:
    DJNZ .cell
.nextrow:
    LD A,(p_geo_columns)
    LD HL,p_w_index
    ADD A,(HL)
    LD (HL),A
    LD HL,p_w_top
    INC (HL)
    LD HL,qe_row
    INC (HL)
    LD A,(p_geo_rows)
    CP (HL)
    JP NZ,.row
    LD HL,p_w_copy
    INC (HL)
    JP .copy
.done:
    XOR A
    LD (i_active),A
    RET

x_row_dirty:
    LD E,A
    AND 7
    LD L,A
    LD H,0
    LD BC,x_bits
    ADD HL,BC
    LD B,(HL)
    LD A,E
    DUP 3
    SRL A
    EDUP
    LD L,A
    LD H,0
    LD DE,p_fd_rows
    ADD HL,DE
    LD A,(HL)
    AND B
    RET
x_span_dirty:
    LD A,(p_w_y)
    DUP 3
    SRL A
    EDUP
    LD (p_w_top),A
    CALL x_row_dirty
    RET NZ
    LD A,(p_w_family)
    NEG
    ADD A,7
    LD B,A
    LD A,(p_w_y)
    ADD A,B
    DUP 3
    SRL A
    EDUP
    LD B,A
    LD A,(p_w_top)
    CP B
    RET Z
    LD A,B
    JP x_row_dirty
x_bits:
    DB 1,2,4,8,16,32,64,128

x_pipeline:
    JP presentation_world_prepare
x_prepare_sat:
    LD A,($F068)
    CP 150
    LD A,0
    ADC A,0
    XOR 1
    LD (p_w_coarse),A
    LD A,($F046)
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
    LD A,2
    CALL t_mapper
    CALL presentation_sprites_prepare
    LD A,7
    CALL t_mapper
    CALL $AA00
    LD A,2
    CALL t_mapper
    JP p_dirty_describe
x_force_rows:
    LD A,7
    CALL t_mapper
    CALL $AA03
    JP p_fast_release_dirty
x_actor_dirty_gate:
    LD A,(p_w_row)
    LD L,A
    LD H,0
    LD BC,x_bits
    ADD HL,BC
    LD B,(HL)
    LD A,(p_s_reflect)
    CPL
    LD C,A
    LD A,(p_s_column)
    AND C
    AND B
    RET NZ
x_hidden_dirty:
    LD A,(p_w_row)
    LD B,A
    ADD A,A
    ADD A,A
    ADD A,B
    ADD A,23
    LD C,A
    PUSH IX
    POP HL
    LD A,L
    ADD A,C
    LD L,A
    LD A,(HL)
    INC L
    OR (HL)
    LD B,A
    PUSH IY
    POP HL
    LD A,L
    ADD A,C
    LD L,A
    LD A,(HL)
    INC L
    OR (HL)
    OR B
    RET Z
    JP p_template_dirty_object
x_sgt_upload:
    LD A,255
    CALL t_mapper
    LD B,32
    CALL vdp_write
    LD A,7
    JP t_mapper
x_pattern_read:
    PUSH DE
    LD A,255
    CALL t_mapper
    LD DE,$C500
    LD BC,32
    LDIR
    LD A,7
    CALL t_mapper
    POP DE
    RET
x_player_replace:
    LD A,(PAGE)
    ADD A,p_pc_next&255
    LD L,A
    LD H,p_pc_next/256
    LD A,(HL)
    LD B,A
    INC A
    CP 3
    JR C,.ready
    XOR A
.ready:
    LD (HL),A
    LD A,B
    CALL p_player_variant_set
    LD (IX),0
    SCF
    RET
x_world_dirty:
    OR B
    JR NZ,.continue
    LD A,(p_s_column)
    OR A
    JR NZ,.continue
    POP HL
    RET
.continue:
    XOR A
    RET
x_world_end:
    ASSERT $ <= $F900
