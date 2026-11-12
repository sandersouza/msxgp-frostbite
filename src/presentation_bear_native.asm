; Exact native bear cells. Foreign calls/data reads return through reserved RAM.
    INCLUDE "symbols.inc"
    ORG $EF33
ai_entry:
    CALL p_fast_primitive_dirty
    RET Z
    LD A,102
    CALL t_mapper
    JP ai_body
ai_call:
    CALL .via
    PUSH AF
    LD A,102
    CALL t_mapper
    POP AF
    RET
.via:
    JP (IX)
ai_copy:
    CALL t_mapper
    LDIR
    LD A,102
    JP t_mapper
ai_bulk_enter:
    LD A,112
    CALL t_mapper
    JP ai_bulk
ai_bulk_back:
    LD A,6
    LD (p_w_top),A
    XOR A
    LD (p_w_index),A
    LD (p_w_line),A
    LD A,(p_w_origin)
    LD (p_w_col),A
    LD A,102
    CALL t_mapper
    JP ai_body.row
ai_bulk_ids:
    CALL t_mapper
    PUSH HL
    POP IY
    LD HL,p_geo_ids
    LD DE,20
    LD C,12
.ids:
    LD A,(IY)
    LD (HL),A
    INC HL
    LD A,(IY+1)
    LD (HL),A
    INC HL
    ADD IY,DE
    DEC C
    JR NZ,.ids
    PUSH IY
    POP HL
    LD DE,3
    ADD HL,DE
    LD DE,$C500
    LD BC,12
    LDIR
    LD A,112
    JP t_mapper
ai_bulk_upload:
    CALL t_mapper
    PUSH DE
    LD B,32
    CALL vdp_write
    POP DE
    LD A,D
    ADD A,$20
    LD D,A
    LD B,32
    CALL vdp_write
    LD A,112
    JP t_mapper
ai_ram_end:
    ASSERT $ <= $F000

    ORG $B800
ai_body:
    LD A,(p_w_group)
    CP 16
    JP NC,p_world_primitive
    LD L,A
    LD H,0
    DUP 6
    ADD HL,HL
    EDUP
    LD A,(p_w_x)
    CP 160
    JP NC,p_world_primitive
    AND 15
    ADD A,A
    LD B,A
    LD A,(p_w_coarse)
    CP 2
    JP NC,p_world_primitive
    OR B
    ADD A,A
    LD E,A
    LD D,0
    ADD HL,DE
    LD DE,$B800
    ADD HL,DE
    LD DE,p_tf_cache
    LD BC,2
    LD A,66
    CALL ai_copy
    LD A,(p_tf_cache)
    LD B,A
    DUP 3
    SRL A
    EDUP
    ADD A,67
    LD (p_tf_column),A
    LD A,B
    AND 7
    ADD A,$B8
    LD H,A
    LD L,0
    LD (p_tf_cache),HL
    LD L,240
    LD DE,p_geo_columns
    LD BC,3
    LD A,(p_tf_column)
    CALL ai_copy
    CALL p_fast_clear_memo
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
    LD A,6
    LD (p_w_top),A
    XOR A
    LD (p_w_index),A
    LD (p_w_line),A
    JP ai_bulk_enter
.row:
    LD A,(p_w_top)
    CALL p_fast_row_dirty
    JR NZ,.dirty
    LD A,(p_w_index)
    LD B,A
    LD A,(p_geo_columns)
    ADD A,B
    LD (p_w_index),A
    JR .row_done
.dirty:
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
    CALL NC,ai_tile
    LD HL,p_w_index
    INC (HL)
    LD HL,p_w_line
    INC (HL)
    LD A,(p_geo_columns)
    CP (HL)
    JR Z,.row_done
    LD HL,p_w_col
    INC (HL)
    LD HL,p_w_name
    INC (HL)
    JR .cell
.row_done:
    LD A,(p_geo_stride)
    SRL A
    LD B,A
    LD A,(p_w_index)
    CP B
    RET Z
    LD HL,p_w_top
    INC (HL)
    XOR A
    LD (p_w_line),A
    LD A,(p_w_origin)
    LD (p_w_col),A
    JR .row

ai_tile:
    LD A,(p_w_index)
    LD L,A
    LD H,0
    ADD HL,HL
    ADD HL,HL
    PUSH HL
    ADD HL,HL
    ADD HL,HL
    POP DE
    ADD HL,DE
    LD DE,(p_tf_cache)
    ADD HL,DE
    LD A,(p_tf_column)
    LD DE,p_geo_ids
    LD BC,20
    CALL ai_copy
    LD DE,(p_geo_ids)
    LD A,D
    OR E
    RET Z
    LD HL,(p_w_name)
    LD A,(HL)
    CP 128
    JP C,.fallback
    LD (pf_key+2),A
    LD (pf_key),DE
    XOR A
    LD (pf_key+5),A
    LD A,(p_w_top)
    CP 8
    LD A,0
    JR NC,.clip
    LD A,(p_w_col)
    CP 2
    LD A,0
    JR NZ,.clip
    INC A
.clip:
    LD (pf_key+3),A
    LD A,(p_w_color)
    LD (pf_key+4),A
    CP 1
    LD BC,0
    JR Z,.color
    CP 15
    JP NZ,.fallback
    LD B,2
.color:
    LD A,(p_w_top)
    DUP 3
    SRL A
    EDUP
    LD (p_fx_bank),A
    LD H,0
    LD A,(pf_key+2)
    SUB 128
    LD L,A
    ADD HL,HL
    LD A,(p_fx_bank)
    LD H,A
    LD A,(pf_key+3)
    ADD A,L
    LD L,A
    ADD HL,BC
    LD DE,ai_contexts
    ADD HL,DE
    LD A,(HL)
    CP 9
    JP NC,.fallback
    ADD A,A
    ADD A,p_geo_ids+2 & 255
    LD L,A
    LD H,p_geo_ids/256
    LD E,(HL)
    INC HL
    LD D,(HL)
    BIT 7,D
    RET NZ                 ;same empty-left-clip skip as the original driver
    PUSH DE                ;precomposed tile index, below original caller return
    LD A,(p_w_top)
    SUB 6
    CP 2
    JR NZ,.role
    XOR A
.role:
    ADD A,A
    ADD A,A
    LD B,A
    LD A,(p_w_line)
    ADD A,B
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
    POP DE
    JR .name
.miss:
    POP DE
    LD A,D
    ADD A,A
    LD B,A
    LD A,E
    RLCA
    AND 1
    ADD A,B
    ADD A,79
    PUSH AF
    LD A,E
    DUP 4
    RRCA
    EDUP
    AND 7
    ADD A,$B8
    LD H,A
    LD A,E
    AND 15
    DUP 4
    RLCA
    EDUP
    LD L,A
    LD DE,pt_tile
    LD BC,16
    POP AF
    CALL ai_copy
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
    OR A
    RET
.fallback:
    LD DE,(p_geo_ids)
    LD IX,p_fast_world_tile
    JP ai_call
ai_body_end:
    ASSERT $ <= $BC00
    DS $BC00-$,$FF
ai_contexts:
    INCBIN "bear-contexts.bin"
ai_end:
    ASSERT $ == $C000

    ORG $B800
ai_bulk:
    LD A,(p_w_color)
    CP 15
    JP NZ,ai_bulk_back
    LD A,(p_w_origin)
    CP 3
    JP C,ai_bulk_back
    LD B,A
    LD A,(p_geo_columns)
    ADD A,B
    CP 32
    JP NC,ai_bulk_back
    LD A,255
    LD ($C50C),A
    LD A,6
    LD (p_w_top),A
    CALL ai_bulk_name
    LD DE,32
.cert_row:
    LD A,(p_w_top)
    CALL p_fast_row_dirty
    JR Z,.cert_next
    ; The sealed background writer fills columns3..30 with one static ID.
    ; Both cover tables require rows6..8 to take that complete fill.
    LD A,($C50C)
    CP 255
    JR NZ,.theme_ready
    LD A,(p_w_top)
    CP 8
    LD A,(HL)
    JR NC,.theme_lower
    CP 136
    LD A,0
    JR Z,.theme_set
    LD A,(HL)
    CP 128
    JP NZ,ai_bulk_back
    LD A,1
    JR .theme_set
.theme_lower:
    CP 129
    LD A,0
    JR Z,.theme_set
    LD A,(HL)
    CP 131
    JP NZ,ai_bulk_back
    LD A,1
.theme_set:
    LD ($C50C),A
.theme_ready:
    CALL ai_bulk_bg
    CP (HL)
    JP NZ,ai_bulk_back
.cert_next:
    ADD HL,DE
    LD A,(p_w_top)
    INC A
    LD (p_w_top),A
    CP 9
    JR NZ,.cert_row
    LD HL,(p_tf_cache)
    LD A,(p_tf_column)
    CALL ai_bulk_ids
    LD A,6
    LD (p_w_top),A
    CALL ai_bulk_name
    PUSH HL
    POP IY
    LD HL,p_geo_ids
.row:
    LD A,(p_w_top)
    CALL p_fast_row_dirty
    JR NZ,.dirty
    LD A,(p_geo_columns)
    ADD A,A
    LD E,A
    LD D,0
    ADD HL,DE
    LD DE,32
    ADD IY,DE
    JP .next_row
.dirty:
    PUSH HL                ;next source logical-ID row
    LD A,(PAGE)
    LD B,A
    ADD A,A
    ADD A,B
    LD B,A
    LD A,(p_w_top)
    SUB 6
    ADD A,B
    LD L,A
    LD H,0
    LD D,H
    LD E,L
    ADD HL,HL
    ADD HL,DE
    ADD HL,HL
    LD DE,ai_bulk_roles
    ADD HL,DE
    LD A,(HL)
    LD (p_fx_bank),A
    INC HL
    LD A,(HL)
    LD (p_w_tile),A
    INC HL
    LD E,(HL)
    INC HL
    LD D,(HL)
    LD (p_fx_meta),DE
    INC HL
    LD E,(HL)
    INC HL
    LD D,(HL)
    PUSH DE                ;PGT address for all four fixed roles
    LD HL,(p_fx_meta)
    LD D,H
    LD E,L
    INC DE
    LD (HL),255
    LD BC,23
    LDIR
    LD A,(p_w_top)
    SUB 6
    ADD A,A
    LD B,A
    LD A,($C50C)
    OR A
    LD A,B
    JR Z,.strip_index
    ADD A,6
.strip_index:
    LD L,A
    LD H,$C5
    LD E,(HL)
    INC HL
    LD D,(HL)
    LD A,D
    DUP 3
    ADD A,A
    EDUP
    LD B,A
    LD A,E
    DUP 5
    RRCA
    EDUP
    AND 7
    ADD A,B
    ADD A,103
    PUSH AF
    LD A,E
    DUP 2
    RRCA
    EDUP
    AND 7
    ADD A,$B8
    LD H,A
    LD A,E
    AND 3
    DUP 6
    RLCA
    EDUP
    LD L,A
    POP AF
    POP DE
    CALL ai_bulk_upload
    CALL ai_bulk_bg
    LD ($C50D),A
    POP HL
    LD IX,(p_fx_meta)
    LD A,(p_w_tile)
    LD B,A
    LD A,(p_geo_columns)
    LD C,A
.cell:
    LD E,(HL)
    INC HL
    LD D,(HL)
    INC HL
    LD A,D
    OR E
    JR Z,.advance
    LD (IX),E
    LD (IX+1),D
    LD A,($C50D)
    LD (IX+2),A
    LD (IX+3),0
    LD (IX+4),15
    LD (IX+5),0
    LD (IY),B
.advance:
    LD DE,6
    ADD IX,DE
    INC IY
    INC B
    DEC C
    JR NZ,.cell
    LD A,(p_geo_columns)
    LD E,A
    LD A,32
    SUB E
    LD E,A
    LD D,0
    ADD IY,DE
.next_row:
    LD A,(p_w_top)
    INC A
    LD (p_w_top),A
    CP 9
    JP NZ,.row
    OR A
    RET
ai_bulk_name:
    LD A,(PAGE)
    OR A
    LD HL,$C8C0
    JR Z,.page
    LD H,$CD
.page:
    LD A,(p_w_origin)
    ADD A,L
    LD L,A
    RET
ai_bulk_roles:
    DB 0,0
    DW $D000,$4000
    DB 0,4
    DW $D018,$4020
    DB 1,0
    DW $D180,$4800
    DB 0,64
    DW $D480,$4200
    DB 0,68
    DW $D498,$4220
    DB 1,64
    DW $D600,$4A00
ai_bulk_bg:
    LD A,($C50C)
    OR A
    LD A,(p_w_top)
    JR NZ,.night
    CP 8
    LD A,136
    RET C
    LD A,129
    RET
.night:
    CP 8
    LD A,128
    RET C
    LD A,131
    RET
ai_bulk_end:
    ASSERT $ <= $C000
    DS $C000-$,$FF
ai_bulk_padded_end:
