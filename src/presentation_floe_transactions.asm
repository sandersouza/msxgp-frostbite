; Native floe transaction, AA diagnostic. Entry x_floe keeps its call contract.
; Reuses F43D..F5D1 and retired typed-header code60B6..6248 only.
; No new RAM/VRAM. NAME program/helper and original packet bytes stay unchanged.
; Persistent owner/tuple publication follows complete PGT/CGT writes.
; Color LUT is copied exactly from the verified parent by the maintained builder.
; See docs/floe-transactions.md for scratch and retired-constructor ABI.
    INCLUDE "symbols.inc"
    ORG $F43D
aa_floe:
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
    LD A,(p_w_coarse)
    ADD A,(HL)
    LD (p_w_y),A
    AND 7
    LD (p_tf_tuple+2),A
    CP 2
    LD A,2
    SBC A,0
    LD (p_tf_column),A
    LD A,(p_w_y)
    DUP 3
    SRL A
    EDUP
    LD (p_w_top),A
    LD L,A
    LD H,$FC
    LD B,(HL)
    LD A,(p_tf_column)
    DEC A
    JR Z,.one
    INC L
    LD A,(HL)
    OR B
    JR .gate
.one:
    LD A,B
    OR A
.gate:
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
    LD A,(p_w_top)
    CALL aa_dirty
    JR Z,.second
    LD DE,(p_w_name)
    LD HL,(p_tf_cache)
    CALL x_name_row
.second:
    LD A,(p_tf_column)
    DEC A
    RET Z
    LD A,(p_w_top)
    INC A
    CALL aa_dirty
    RET Z
    LD HL,(p_w_name)
    LD DE,32
    ADD HL,DE
    EX DE,HL
    LD HL,(p_tf_cache)
    LD BC,30
    ADD HL,BC
    JP x_name_row
aa_floe_end:
    ASSERT $ <= $F5D2
    DS $F5D2-$,0

    ORG $60B6
aa_publish:
    CALL vdp_write
    LD HL,(pk_ownerptr)
    LD A,L
    SUB pk_records&255
    RRCA
    RRCA
    ADD A,pk_colors&255
    LD L,A
    LD A,(p_w_color)
    CP (HL)
    JR Z,.done
    PUSH HL
    DUP 4
    RLCA
    EDUP
    OR 4
    LD B,128
    LD C,A
    LD A,D
    ADD A,$20
    LD D,A
    LD A,C
    CALL pk_fill
    POP HL
    LD A,(p_w_color)
    LD (HL),A
.done:
    LD HL,pk_pending
    LD DE,(pk_ownerptr)
    LD BC,4
    LDIR
    LD A,(p_tl_count)
    DEC A
    LD (p_ts_cursor),A
    XOR A
    LD (pt_error),A
    LD (p_tr_error),A
    RET
    DS $6100-$,0
    INCBIN "color-lut.bin"
aa_dirty:
    LD L,A
    LD H,$FC
    LD A,(HL)
    OR A
    RET
aa_y:
    DB 167,141,115,89
aa_pgt:
    DW $50C8,$5048,$4918,$4898
aa_resident_end:
    ASSERT $ <= $6249
