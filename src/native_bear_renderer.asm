; Full native bear fallback. Only source picture masks, canonical solid-row
; palette and explicit kind10 keys; complete sprite path remains unchanged.
nb_base EQU $C508
nb_mask EQU $C50A
nb_body:
    LD A,(p_w_group)
    CP 16
    JP NC,nb_error
    LD A,(p_w_x)
    CP 160
    JP NC,nb_error
    AND 15
    LD B,A
    LD A,(p_w_coarse)
    CP 2
    JP NC,nb_error
    LD C,A
    LD A,(p_w_group)
    CALL ng_build
    LD A,(p_w_group)
    ADD A,A
    LD H,A
    LD A,(p_w_x)
    AND 15
    LD B,A
    DUP 3
    RRCA
    EDUP
    AND 1
    OR H
    LD H,A
    LD A,B
    DUP 5
    ADD A,A
    EDUP
    LD L,A
    LD A,(p_w_coarse)
    DUP 4
    ADD A,A
    EDUP
    OR L
    LD L,A
    LD (nb_base),HL
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
    LD A,6
    LD (p_w_top),A
.row:
    LD A,(p_w_top)
    CALL p_fast_row_dirty
    JR Z,.next_row
    LD A,(p_w_top)
    SUB 6
    ADD A,A
    ADD A,A
    LD (p_w_index),A
    XOR A
    LD (p_w_line),A
    LD A,(p_w_origin)
    LD (p_w_col),A
    CALL p_fast_cell
.cell:
    LD A,(p_w_col)
    CP 31
    JR C,.column
    SUB 30
    LD (p_w_col),A
    CALL p_fast_cell
    LD A,(p_w_col)
.column:
    CP 2
    CALL NC,nb_tile
    LD HL,p_w_index
    INC (HL)
    LD HL,p_w_line
    INC (HL)
    LD A,(ng_columns)
    CP (HL)
    JR Z,.next_row
    LD HL,p_w_col
    INC (HL)
    LD HL,p_w_name
    INC (HL)
    JR .cell
.next_row:
    LD HL,p_w_top
    INC (HL)
    LD A,(HL)
    CP 9
    JR NZ,.row
    RET

nb_tile:
    LD A,(p_w_index)
    LD L,A
    LD H,0
    DUP 3
    ADD HL,HL
    EDUP
    LD DE,$C480
    ADD HL,DE
    LD (nb_mask),HL
    LD B,8
    XOR A
.empty:
    OR (HL)
    INC HL
    DJNZ .empty
    RET Z
    LD HL,(p_w_name)
    LD A,(HL)
    CP 128
    JP C,nb_error
    LD (pf_key+2),A
    LD HL,(nb_base)
    LD A,(p_w_index)
    OR L
    LD L,A
    LD (pf_key),HL
    XOR A
    LD (pf_key+3),A
    LD A,(p_w_color)
    LD (pf_key+4),A
    LD A,10
    LD (pf_key+5),A
    LD A,(p_w_top)
    CP 8
    LD A,0
    JR C,.bank
    INC A
.bank:
    LD (p_fx_bank),A
    LD A,(p_w_index)
    JR C,.role
    AND 3
.role:
    LD B,A
    LD A,(PAGE)
    DUP 6
    ADD A,A
    EDUP
    ADD A,B
    LD (p_w_tile),A
    CALL p_fixed_key_address
    LD (p_fx_meta),HL
    LD DE,pf_key
    LD B,6
.match:
    LD A,(DE)
    CP (HL)
    JR NZ,.miss
    INC DE
    INC HL
    DJNZ .match
    JR .name
.miss:
    LD HL,(nb_mask)
    LD DE,pt_tile
    LD BC,8
    LDIR
    LD A,(p_fx_bank)
    OR A
    LD A,(pf_key+2)
    JR NZ,.bank1
    LD HL,nb_palette
    CP 136
    JR Z,.paint
    CP 128
    JP NZ,nb_error
    LD HL,nb_palette+8
    JR .paint
.bank1:
    LD HL,nb_palette+16
    CP 129
    JR Z,.paint
    LD HL,nb_palette+24
    CP 131
    JR Z,.paint
    LD HL,nb_palette+32
    CP 132
    JP NZ,nb_error
.paint:
    LD A,(p_w_color)
    LD DE,pt_tile+8
    CALL np_paint
    LD A,(p_w_tile)
    LD L,A
    LD H,0
    DUP 3
    ADD HL,HL
    EDUP
    LD A,(p_fx_bank)
    DUP 3
    ADD A,A
    EDUP
    ADD A,$40
    ADD A,H
    LD H,A
    EX DE,HL
    PUSH DE
    LD HL,pt_tile
    LD B,8
    CALL vdp_write
    POP DE
    LD A,D
    ADD A,$20
    LD D,A
    LD HL,pt_tile+8
    LD B,8
    CALL vdp_write
    LD DE,(p_fx_meta)
    LD HL,pf_key
    LD BC,6
    LDIR
.name:
    LD HL,(p_w_name)
    LD A,(p_w_tile)
    LD (HL),A
    RET
nb_error:
    LD A,1
    LD (pt_error),A
    RET
nb_palette:
    DB $FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF
    DB $11,$11,$11,$11,$11,$11,$11,$11
    DB $FF,$FF,$FF,$FF,$FF,$FF,$11,$44
    DB $11,$11,$11,$11,$11,$11,$11,$44
    DB $FF,$FF,$FF,$FF,$FF,$FF,$FF,$11
