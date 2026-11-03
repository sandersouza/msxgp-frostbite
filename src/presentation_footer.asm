; Exclusive footer roles: map one finite source program, compare full keys,
; stream all required PGT/CGT bytes directly, then restore its CPU NAME cell.
    ASSERT p_static_footer_names_bank = p_static_footer_tiles_bank
    ASSERT p_static_footer_tile_count < 256
    ASSERT p_static_footer_tiles_data+p_static_footer_tile_count*16 <= $C000
    ASSERT p_static_footer_names_data+704 <= $C000
p_template_footer_prepare:
    LD A,(p_fd_rows+2)
    AND 192
    RET Z
    LD A,(PAGE)
    CP 2
    JP NC,p_template_footer_fail
    LD A,(p_w_coarse)
    CP 2
    JP NC,p_template_footer_fail
    LD A,(p_h_footer_phase)
    CP 8
    JP NC,p_template_footer_fail
    ADD A,A
    LD B,A
    LD A,(p_w_coarse)
    OR B
    LD L,A
    LD H,0
    LD E,L
    LD D,H
    ADD HL,HL
    ADD HL,DE
    ADD HL,HL
    ADD HL,HL
    OR A
    SBC HL,DE
    ADD HL,HL
    ADD HL,HL
    LD DE,p_static_footer_names_data
    ADD HL,DE
    PUSH HL
    POP IX
    LD IY,$D900
    LD A,(PAGE)
    OR A
    LD A,160
    JR Z,.metadata
    LD DE,132
    ADD IY,DE
    LD A,182
.metadata:
    LD (p_w_tile),A
    XOR A
    LD (p_h_footer_index),A
    LD (pf_key+2),A
    LD (pf_key+3),A
    LD (pf_key+4),A
    LD A,6
    LD (pf_key+5),A
    LD A,22
    LD (p_w_top),A
    LD A,4
    LD (p_w_col),A
    CALL p_fast_cell
    LD A,p_static_footer_names_bank
    LD ($7000),A
.cell:
    LD E,(IX)
    LD D,(IX+1)
    INC IX
    INC IX
    LD A,D
    OR E
    JP Z,.next             ;zero leaves the caller's prepared background intact
    LD A,D
    OR A
    JP NZ,p_template_footer_fail
    LD A,E
    CP p_static_footer_tile_count
    JP NC,p_template_footer_fail
    LD (pf_key),DE
    LD HL,pf_key
    DUP 6,i
    LD A,(HL)
    CP (IY+i)
    JR NZ,.miss
    INC L
    EDUP
    JR .name
.miss:
    LD HL,(pf_key)
    DUP 4
    ADD HL,HL
    EDUP
    LD DE,p_static_footer_tiles_data
    ADD HL,DE
    PUSH HL
    LD A,(p_w_tile)
    LD L,A
    LD H,0
    DUP 3
    ADD HL,HL
    EDUP
    LD DE,$5000
    ADD HL,DE
    EX DE,HL
    POP HL
    LD B,8
    CALL vdp_write
    LD A,D
    ADD A,$20
    LD D,A
    LD B,8                 ;HL already points to this record's complete CGT
    CALL vdp_write
    PUSH IY
    POP DE
    LD HL,pf_key
    LD BC,6
    LDIR                   ;publish only after both complete table writes
.name:
    LD HL,(p_w_name)
    LD A,(p_w_tile)
    LD (HL),A
.next:
    LD HL,p_h_footer_index
    INC (HL)
    LD A,(HL)
    CP 22
    RET Z
    LD HL,p_w_tile
    INC (HL)
    LD DE,6
    ADD IY,DE
    LD HL,(p_w_name)
    INC HL
    LD A,(p_h_footer_index)
    CP 11
    JR NZ,.advance
    LD DE,21
    ADD HL,DE
.advance:
    LD (p_w_name),HL
    JP .cell
p_template_footer_fail:
    CALL p_world_fail
    SCF
    RET
