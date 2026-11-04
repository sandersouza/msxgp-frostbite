; Fixed physical mono transactions plus exact selective NAME/fusion traversal.
qe_caches EQU $E800
qe_tuple EQU $E820
qe_cacheptr EQU $E823
qe_rolesptr EQU $E825
qe_origin EQU $E827
qe_row EQU $E829
qe_roleid EQU $E82A
qe_rowbase EQU $E82B
qe_keyindex EQU $E82F
qe_oldcolor EQU $E830
qe_segment EQU $E831
qe_column EQU $E832
qe_metadata EQU $E840

qe_primitive:
    PUSH IX
    PUSH IY
    LD A,(p_w_copy)
    OR A
    JR NZ,.ready
    LD (i_valid),A
    CALL p_fast_clear_memo
.ready:
    LD A,1
    LD (i_active),A
    CALL qe_body
    PUSH AF
    XOR A
    LD (i_active),A
    POP AF
    POP IY
    POP IX
    RET

qe_body:
    LD A,(p_w_family)
    OR A
    JP NZ,p_world_fail
    LD A,(p_w_color)
    CP 4
    RET Z
    CALL p_fast_primitive_dirty
    RET Z
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
    XOR A
    CALL qe_geometry
    JP C,p_world_fail
    CALL qe_bulk
    JP C,p_world_fail
    ; Same integer1.5x projection as the original primitive.
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
    LD (qe_origin),A
    LD A,(p_w_y)
    DUP 3
    SRL A
    EDUP
    LD (p_w_top),A
    XOR A
    LD (p_w_index),A
    LD (qe_row),A
.row:
    LD A,(p_w_top)
    CALL p_fast_row_dirty
    JR NZ,.dirty
    LD A,(p_geo_columns)
    LD B,A
    LD A,(p_w_index)
    ADD A,B
    LD (p_w_index),A
    JP .nextrow
.dirty:
    LD A,(qe_origin)
    LD (p_w_col),A
    CALL p_fast_cell
    LD HL,(p_w_name)
    LD A,(p_w_col)
    LD E,A
    LD D,0
    OR A
    SBC HL,DE
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
    LD A,B
    OR A
    JR Z,.role
    LD DE,6
    ADD HL,DE
.role:
    LD DE,4
    ADD HL,DE
    LD A,(HL)
    LD (qe_roleid),A
    XOR A
    LD (p_w_line),A
.cell:
    LD A,(p_w_index)
    ADD A,A
    ADD A,p_geo_ids&255
    LD L,A
    LD H,p_geo_ids/256
    LD E,(HL)
    INC L
    LD D,(HL)
    LD A,D
    OR E
    JR Z,.nextcell
    LD A,(p_w_col)
    CP 2
    JR C,.nextcell
    LD (pfw_id),DE
    LD HL,(p_w_name)
    LD A,(HL)
    CP 128
    JR NC,.mono
    CALL qe_fuse
    JP C,p_world_fail
    JR .nextcell
.mono:
    LD A,(p_w_line)
    LD B,A
    LD A,(qe_roleid)
    ADD A,B
    LD (HL),A
    LD (p_w_tile),A
    CALL p_fixed_mark_object
.nextcell:
    LD HL,p_w_index
    INC (HL)
    LD HL,p_w_col
    INC (HL)
    LD A,(HL)
    CP 31
    JR C,.advance
    LD (HL),1
    LD HL,(qe_rowbase)
    INC HL
    JR .pointer
.advance:
    LD HL,(p_w_name)
    INC HL
.pointer:
    LD (p_w_name),HL
    LD HL,p_w_line
    INC (HL)
    LD A,(p_geo_columns)
    CP (HL)
    JP NZ,.cell
.nextrow:
    LD HL,p_w_top
    INC (HL)
    LD HL,qe_row
    INC (HL)
    LD A,(p_geo_rows)
    CP (HL)
    JP NZ,.row
    OR A
    RET

qe_bulk:
    CALL qe_select_roles    ;even a cache hit must select this owner's roles
    LD A,(PAGE)
    ADD A,A
    ADD A,A
    LD B,A
    LD A,(p_w_row)
    ADD A,B
    LD E,A
    ADD A,A
    ADD A,A
    LD L,A
    LD H,qe_caches/256
    LD (qe_cacheptr),HL
    LD A,(p_w_group)
    LD (qe_tuple),A
    LD A,(pfw_geo_variant)
    LD B,A
    LD A,(p_w_coarse)
    RRCA                   ;coarse split is part of the physical packet identity
    OR B
    LD (qe_tuple+1),A
    LD A,(p_w_color)
    LD (qe_tuple+2),A
    LD DE,qe_tuple
    LD B,3
.match:
    LD A,(DE)
    CP (HL)
    JR NZ,.miss
    INC DE
    INC HL
    DJNZ .match
    OR A
    RET
.miss:
    LD HL,(qe_cacheptr)
    INC L
    INC L
    LD A,(HL)
    LD (qe_oldcolor),A
    CALL qe_generate
    LD A,(p_w_row)
    CP 1
    JR NZ,.keys
    LD A,(p_w_coarse)
    OR A
    JR Z,.keys
    LD HL,i_buffer
    LD DE,i_buffer+24
    LD BC,24
    LDIR
    LD HL,i_buffer
    LD B,24
    XOR A
.clear:
    LD (HL),A
    INC L
    DJNZ .clear
.keys:
    IFNDEF WITH_LAZY_ENEMY
    CALL qe_build_keys
    ENDIF
    XOR A
    LD (qe_segment),A
.upload:
    CALL qe_role_pointer
    LD E,(HL)
    INC HL
    LD D,(HL)
    LD A,(qe_segment)
    OR A
    LD HL,i_buffer
    JR Z,.pattern
    LD HL,i_buffer+24
.pattern:
    LD B,24
    CALL vdp_write
    LD A,(qe_oldcolor)
    LD B,A
    LD A,(p_w_color)
    CP B
    JR Z,.nextupload
    DUP 4
    RLCA
    EDUP
    OR 4
    LD C,A
    LD A,D
    ADD A,$20
    LD D,A
    LD A,C
    LD B,24
    CALL pk_fill
.nextupload:
    LD HL,qe_segment
    INC (HL)
    LD A,(HL)
    CP 2
    JR NZ,.upload
    IFNDEF WITH_LAZY_ENEMY
    XOR A
    LD (qe_segment),A
.publish:
    CALL qe_role_pointer
    INC HL
    INC HL
    LD E,(HL)
    INC HL
    LD D,(HL)
    LD A,(qe_segment)
    OR A
    LD HL,qe_metadata
    JR Z,.copy
    LD HL,qe_metadata+18
.copy:
    LD BC,18
    LDIR
    LD HL,qe_segment
    INC (HL)
    LD A,(HL)
    CP 2
    JR NZ,.publish
    ENDIF
    LD HL,qe_tuple
    LD DE,(qe_cacheptr)
    LD BC,3
    LDIR                   ;all physical planes and typed keys precede validity
    OR A
    RET

qe_select_roles:
    LD A,(PAGE)
    ADD A,A
    ADD A,A
    LD B,A
    LD A,(p_w_row)
    ADD A,B
    LD L,A
    LD H,0
    LD D,H
    LD E,L
    ADD HL,HL
    ADD HL,DE
    ADD HL,HL
    ADD HL,HL
    LD DE,qe_roles_data
    ADD HL,DE
    LD (qe_rolesptr),HL
    RET
qe_role_pointer:
    LD HL,(qe_rolesptr)
    LD A,(qe_segment)
    OR A
    RET Z
    LD DE,6
    ADD HL,DE
    RET

    IFNDEF WITH_LAZY_ENEMY
qe_build_keys:
    XOR A
    LD (qe_keyindex),A
.key:
    LD A,(qe_keyindex)
    LD B,0
    CP 3
    JR C,.column
    SUB 3
    INC B
.column:
    LD (qe_column),A
    LD C,A
    LD A,(p_w_row)
    CP 1
    JR NZ,.source
    LD A,(p_w_coarse)
    OR A
    JR Z,.source
    LD A,B
    OR A
    JR Z,.zero
    LD B,0
.source:
    LD A,(p_geo_rows)
    CP B
    JR Z,.zero
    LD A,(p_geo_columns)
    CP C
    JR Z,.zero
    JR C,.zero
    LD A,B
    OR A
    LD A,C
    JR Z,.index
    LD B,A
    LD A,(p_geo_columns)
    ADD A,B
.index:
    ADD A,A
    ADD A,p_geo_ids&255
    LD L,A
    LD H,p_geo_ids/256
    LD E,(HL)
    INC L
    LD D,(HL)
    JR .store
.zero:
    LD DE,0
.store:
    PUSH DE
    LD A,(qe_keyindex)
    LD L,A
    LD H,0
    LD D,H
    LD E,L
    ADD HL,HL
    ADD HL,DE
    ADD HL,HL
    LD DE,qe_metadata
    ADD HL,DE
    POP DE
    LD (HL),E
    INC HL
    LD (HL),D
    INC HL
    PUSH HL
    LD HL,(qe_rolesptr)
    LD A,(qe_keyindex)
    CP 3
    LD DE,5
    JR C,.water
    LD E,11
.water:
    ADD HL,DE
    LD A,(HL)
    POP HL
    LD (HL),A
    INC HL
    XOR A
    LD (HL),A
    INC HL
    LD A,(p_w_color)
    LD (HL),A
    INC HL
    XOR A
    LD (HL),A
    LD HL,qe_keyindex
    INC (HL)
    LD A,(HL)
    CP 6
    JP NZ,.key
    RET
    ENDIF

qe_roles_data:
    INCBIN "qe-roles.bin"
qe_end:
    ASSERT $ < $A800       ;unconditional F footer breakpoint must not alias
