; Optional grid24 view. Reuses phase0 packets and existing owner transactions.
    INCLUDE "symbols.inc"
    ORG $F43D
ag_floe:
    LD A,(p_w_row)
    ADD A,$2B
    LD L,A
    LD H,$F0
    LD A,(HL)
    LD L,A
    LD H,$61
    LD A,(HL)
    LD (p_w_color),A
    CP 4
    RET Z
    LD A,(p_w_row)
    LD L,A
    LD H,0
    LD DE,aa_y
    ADD HL,DE
    LD A,(HL)
    LD (p_w_y),A
    DUP 3
    SRL A
    EDUP
    LD (p_w_top),A
    LD L,A
    LD H,$FC
    LD A,(HL)
    OR A
    RET Z
    LD A,(p_w_row)
    ADD A,$1F
    LD L,A
    LD H,$F0
    LD A,(p_w_plane)
    LD B,A
    LD A,(HL)
    SUB B
    CP 160
    JR C,.root
    CP 248
    JR C,.above
    ADD A,160
    JR .root
.above:
    SUB 160
.root:
    LD (p_tl_root),A
    AND 15
    LD (p_tf_tuple),A
    RRCA
    LD H,A
    AND 128
    LD L,A
    LD A,H
    AND 7
    ADD A,$B8
    LD H,A
    LD (pk_pointer),HL
    LD A,(p_w_delta)
    LD (p_tf_tuple+1),A
    XOR A
    LD (p_tf_tuple+2),A
    LD A,(p_w_color)
    LD (p_tf_tuple+3),A
    LD A,(p_tl_delta_index)
    ADD A,35
    LD (pk_bank),A
    CALL t_mapper
    LD A,(PAGE)
    ADD A,A
    ADD A,A
    LD B,A
    LD A,(p_w_row)
    ADD A,B
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
    LD A,(p_tf_identity)
    ADD A,$11
    LD L,A
    LD H,$C1
    LD (pk_ownerptr),HL
    LD HL,(pk_pointer)
    LD DE,112
    ADD HL,DE
    LD DE,pk_pending
    LD BC,4
    LDIR
    LD A,(pk_pending+3)
    LD (p_tl_count),A
    LD A,(p_w_row)
    ADD A,A
    LD L,A
    LD H,0
    LD DE,aa_pgt
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    LD A,(PAGE)
    ADD A,A
    ADD A,D
    LD D,A
    LD HL,(pk_pointer)
    LD A,(p_tl_count)
    ADD A,A
    ADD A,A
    ADD A,A
    LD B,A
    CALL aa_publish
    LD HL,p_tf_tuple
    LD DE,(p_tf_identity)
    LD BC,4
    LDIR
.names:
    IF GRID_PREPARED_NAMES
    LD A,(p_w_top)
    LD L,A
    LD H,0
    DUP 5
    ADD HL,HL
    EDUP
    LD A,(PAGE)
    OR A
    LD DE,$C800
    JR Z,.prepared_page
    LD D,$CD
.prepared_page:
    ADD HL,DE
    LD (p_w_name),HL
    LD A,(p_tl_delta_index)
    ADD A,A
    LD B,A
    LD A,(p_tl_root)
    AND 8
    DUP 3
    RRCA
    EDUP
    ADD A,B
    ADD A,45
    CALL t_mapper
    LD A,(PAGE)
    ADD A,A
    ADD A,A
    LD B,A
    LD A,(p_w_row)
    ADD A,B
    LD B,A
    LD A,(p_tl_root)
    AND 7
    DUP 3
    RLCA
    EDUP
    OR B
    LD L,A
    LD H,0
    DUP 5
    ADD HL,HL
    EDUP
    LD DE,$B800
    ADD HL,DE
    LD DE,(p_w_name)
    JP x_name_row
    ELSE
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
    LD (p_w_name),HL
    LD A,(p_w_row)
    LD L,A
    LD H,0
    LD DE,p_template_strip_bases
    ADD HL,DE
    LD A,(HL)
    SUB 25
    LD C,A
    LD A,(p_w_row)
    CP 2
    LD A,129
    JR C,.water
    INC A
.water:
    LD (p_tf_column),A
    LD A,(p_tl_root)
    DUP 4
    SRL A
    EDUP
    LD B,A
    ADD A,A
    ADD A,B
    LD (p_tf_row),A
    LD E,A
    LD A,30
    SUB E
    LD E,A
    LD D,0
    LD HL,(p_tf_cache)
    ADD HL,DE
    LD A,(p_tf_row)
    LD B,A
    LD DE,(p_w_name)
    LD A,128
    LD (DE),A
    INC DE
    LD A,B
    OR A
    CALL NZ,ag_copy
    LD HL,(p_tf_cache)
    LD A,(p_tf_row)
    LD B,A
    LD A,30
    SUB B
    LD B,A
    CALL ag_copy
    LD A,128
    LD (DE),A
    LD HL,(p_w_name)
    INC HL
    LD (HL),128
    RET
    ENDIF
    IF !GRID_PREPARED_NAMES
ag_copy:
    LD A,(HL)
    CP 128
    JR NC,.water
    ADD A,C
    JR .store
.water:
    LD A,(p_tf_column)
.store:
    LD (DE),A
    INC HL
    INC DE
    DJNZ ag_copy
    RET
    ENDIF
ag_floe_end:
    ASSERT $ <= $F5D2
    DS $F5D2-$,0
