    INCLUDE "symbols.inc"
    ORG $FD00
xh_header:
    JP C,p_world_fail
    XOR A
    LD (p_h_y),A
    LD (p_fx_bank),A
    LD HL,$C805
    LD IX,$D030
    LD A,(PAGE)
    OR A
    LD A,8
    JR Z,.page
    LD HL,$CD05
    LD IX,$D4B0
    LD A,72
.page:
    LD (p_w_tile),A
    PUSH HL
    POP IY
    LD B,3
.names_row:
    PUSH BC
    LD C,10
.names:
    LD (HL),A
    INC L
    INC A
    DEC C
    JR NZ,.names
    LD DE,22
    ADD HL,DE
    POP BC
    DJNZ .names_row
    LD BC,(w_changed)
    LD A,B
    OR C
    JP Z,w_save
.band:
    LD BC,(w_changed)
    XOR A
    LD (p_h_index),A
.bit:
    SRL B
    RR C
    JR NC,.next
    PUSH BC
    LD (p_fx_meta),IX
    LD (p_w_name),IY
    CALL p_template_header_key
    JR C,.key_fail
    CALL xh_put
    POP BC
    JP C,p_world_fail
.next:
    INC IY
    LD DE,6
    ADD IX,DE
    LD HL,p_w_tile
    INC (HL)
    LD HL,p_h_index
    INC (HL)
    LD A,B
    OR C
    JR NZ,.bit
    LD A,10
    SUB (HL)
    LD B,A
    LD HL,p_w_tile
    ADD A,(HL)
    LD (HL),A
    LD A,B
    ADD A,A
    ADD A,B
    ADD A,A
    LD E,A
    LD D,0
    ADD IX,DE
    LD A,B
    ADD A,22
    LD E,A
    ADD IY,DE
    LD HL,p_h_y
    INC (HL)
    LD A,(HL)
    CP 3
    JR NZ,.band
    JP w_save
.key_fail:
    POP BC
    JP p_world_fail

; Preserve the original full constructor whenever physical color identity differs.
; Identical color/fragment/role metadata permits PGT-only updates, valid last.
xh_put:
    LD HL,(p_fx_meta)
    LD DE,3
    ADD HL,DE
    LD DE,pf_key+3
    DUP 3
    LD A,(DE)
    CP (HL)
    JP NZ,p_fixed_put_header
    INC DE
    INC HL
    EDUP
    LD HL,(p_fx_meta)
    LD DE,pf_key
    DUP 3
    LD A,(DE)
    CP (HL)
    JR NZ,.shape
    INC DE
    INC HL
    EDUP
    JP .name
.shape:
    XOR A
    LD (pt_error),A
    LD A,(p_h_index)
    LD L,A
    LD H,0
    DUP 4
    ADD HL,HL
    EDUP
    LD DE,p_th_masks
    ADD HL,DE
    PUSH HL
    XOR A
    LD HL,pt_tile
    DUP 8
    LD (HL),A
    INC L
    EDUP
    POP HL
    LD A,(p_h_y)
    OR A
    JR Z,.top
    CP 2
    JR Z,.bottom
    LD DE,5
    ADD HL,DE
    LD DE,pt_tile
    DUP 3
    LDI
    EDUP
    LD DE,pt_tile+7
    LDI
    JR .upload
.top:
    LD DE,pt_tile+3
    DUP 5
    LDI
    EDUP
    JR .upload
.bottom:
    LD DE,9
    ADD HL,DE
    LD DE,pt_tile
    DUP 7
    LDI
    EDUP
.upload:
    LD A,(p_w_tile)
    LD L,A
    LD H,0
    DUP 3
    ADD HL,HL
    EDUP
    LD DE,$4000
    ADD HL,DE
    EX DE,HL
    LD HL,pt_tile
    LD B,8
    CALL vdp_write
    LD HL,pf_key
    LD DE,(p_fx_meta)
    LD BC,6
    LDIR
.name:
    LD HL,(p_w_name)
    LD A,(p_w_tile)
    LD (HL),A
    OR A
    RET
xh_end:
    ASSERT $ <= $FF00
