    INCLUDE "symbols.inc"
    ORG $7A08
i_buffer EQU $C180
i_active EQU $C1B0
i_valid EQU $C1B1
i_base EQU $C1B2
i_lines EQU $C1B4
i_source EQU $C1B8
i_skip EQU $C1C0

i_init:
    XOR A
    LD (i_active),A
    LD (i_valid),A
    LD HL,$C080
    RET

; The unchanged copy driver owns source wrap, visibility and dirty rows.
i_primitive:
    LD A,(p_w_copy)
    OR A
    JR NZ,.ready
    LD (i_valid),A
.ready:
    LD A,1
    LD (i_active),A
    CALL p_world_primitive
    PUSH AF
    XOR A
    LD (i_active),A
    POP AF
    RET

; Known actor role selected by original p_fixed_put_actor. Only the complete
; solid-water monochrome grammar uses this direct publication path.
i_actor:
    LD A,(i_active)
    OR A
    JP Z,p_fixed_resolve_known
    LD A,(pf_key+5)
    OR A
    JP NZ,p_fixed_resolve_known
    LD A,(pf_key+3)
    OR A
    JP NZ,p_fixed_resolve_known
    PUSH HL
    LD A,(p_fx_bank)
    LD E,A
    LD D,0
    LD HL,pt_water_ids
    ADD HL,DE
    LD A,(pf_key+2)
    CP (HL)
    POP HL
    JP NZ,p_fixed_resolve_known
    LD (p_fx_meta),HL
    LD DE,pf_key
    DUP 6
    LD A,(DE)
    CP (HL)
    JR NZ,.miss
    INC E
    INC HL
    EDUP
    OR A
    RET
.miss:
    XOR A
    LD (i_skip),A
    ; A prior exact same water/type/clip grammar permits plane independence.
    LD HL,(p_fx_meta)
    INC HL
    INC HL
    LD A,(pf_key+2)
    CP (HL)
    JR NZ,.pattern
    INC HL
    LD A,(HL)
    OR A
    JR NZ,.pattern
    INC HL
    LD B,(HL)
    INC HL
    LD A,(HL)
    OR A
    JR NZ,.pattern
    LD A,(pf_key+4)
    CP B
    JR NZ,.color_changed
    LD A,2
    LD (i_skip),A
.color_changed:
    LD HL,(p_fx_meta)
    LD A,(pf_key)
    CP (HL)
    JR NZ,.pattern
    INC HL
    LD A,(pf_key+1)
    CP (HL)
    JR NZ,.pattern
    LD A,(i_skip)
    OR 1
    LD (i_skip),A
    JR .color
.pattern:
    LD A,(i_valid)
    OR A
    CALL Z,i_generate
    LD A,(p_geo_columns)
    LD B,A
    LD A,(p_w_index)
    CP B
    JR C,.offset
    SUB B
    ADD A,3
.offset:
    LD L,A
    LD H,0
    DUP 3
    ADD HL,HL
    EDUP
    LD DE,i_buffer
    ADD HL,DE
    PUSH HL
    CALL i_vram_address
    POP HL
    LD B,8
    CALL vdp_write
.color:
    LD A,(i_skip)
    BIT 1,A
    JR NZ,.published
    LD A,(pf_key+4)
    DUP 4
    RLCA
    EDUP
    OR 4
    LD HL,pt_tile+8
    DUP 8
    LD (HL),A
    INC L
    EDUP
    CALL i_vram_address
    LD A,D
    ADD A,$20
    LD D,A
    LD HL,pt_tile+8
    LD B,8
    CALL vdp_write
.published:
    LD HL,pf_key
    LD DE,(p_fx_meta)
    LD BC,6
    LDIR
    XOR A
    LD (pt_error),A
    RET

i_vram_address:
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
    RET

; Complete horizontal packets are already expanded in ROM. Only vertical
; byte placement into the six-cell packet remains; no per-pixel composition.
i_generate:
    XOR A
    LD HL,i_buffer
    DUP 48
    LD (HL),A
    INC L
    EDUP
    LD A,(p_w_group)
    LD L,A
    LD H,0
    DUP 4
    ADD HL,HL
    EDUP
    LD A,(p_w_x)
    AND 15
    LD E,A
    LD D,0
    ADD HL,DE
    LD E,L
    LD D,H
    ADD HL,HL
    ADD HL,DE
    LD DE,i_packets
    ADD HL,DE
    LD A,i_packets_bank
    LD ($7000),A
    LD E,(HL)
    INC HL
    LD D,(HL)
    INC HL
    LD A,(HL)
    LD ($7000),A
    EX DE,HL
    LD A,L
    AND 1
    LD (i_lines),A          ;1 means the third horizontal column is all zero
    RES 0,L
    PUSH HL
    LD A,(p_w_y)
    AND 7
    ADD A,A
    LD E,A
    LD D,0
    LD HL,i_shifts
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    EX DE,HL
    POP DE
    JP (HL)
i_done:
    LD A,1
    LD (i_valid),A
    RET
i_shifts:
    DW i_shift0,i_shift1,i_shift2,i_shift3
    DW i_shift4,i_shift5,i_shift6,i_shift7
i_shift0:
    EX DE,HL
    LD DE,i_buffer+0
    LDI
    LDI
    LDI
    LDI
    LDI
    LDI
    LDI
    LDI
    LD DE,i_buffer+8
    LDI
    LDI
    LDI
    LDI
    LDI
    LDI
    LDI
    LDI
    LD A,(i_lines)
    OR A
    JP NZ,i_done
    LD DE,i_buffer+16
    LDI
    LDI
    LDI
    LDI
    LDI
    LDI
    LDI
    LDI
    JP i_done
i_shift1:
    EX DE,HL
    LD DE,i_buffer+1
    LDI
    LDI
    LDI
    LDI
    LDI
    LDI
    LDI
    LD DE,i_buffer+24
    LDI
    LD DE,i_buffer+9
    LDI
    LDI
    LDI
    LDI
    LDI
    LDI
    LDI
    LD DE,i_buffer+32
    LDI
    LD A,(i_lines)
    OR A
    JP NZ,i_done
    LD DE,i_buffer+17
    LDI
    LDI
    LDI
    LDI
    LDI
    LDI
    LDI
    LD DE,i_buffer+40
    LDI
    JP i_done
i_shift2:
    EX DE,HL
    LD DE,i_buffer+2
    LDI
    LDI
    LDI
    LDI
    LDI
    LDI
    LD DE,i_buffer+24
    LDI
    LDI
    LD DE,i_buffer+10
    LDI
    LDI
    LDI
    LDI
    LDI
    LDI
    LD DE,i_buffer+32
    LDI
    LDI
    LD A,(i_lines)
    OR A
    JP NZ,i_done
    LD DE,i_buffer+18
    LDI
    LDI
    LDI
    LDI
    LDI
    LDI
    LD DE,i_buffer+40
    LDI
    LDI
    JP i_done
i_shift3:
    EX DE,HL
    LD DE,i_buffer+3
    LDI
    LDI
    LDI
    LDI
    LDI
    LD DE,i_buffer+24
    LDI
    LDI
    LDI
    LD DE,i_buffer+11
    LDI
    LDI
    LDI
    LDI
    LDI
    LD DE,i_buffer+32
    LDI
    LDI
    LDI
    LD A,(i_lines)
    OR A
    JP NZ,i_done
    LD DE,i_buffer+19
    LDI
    LDI
    LDI
    LDI
    LDI
    LD DE,i_buffer+40
    LDI
    LDI
    LDI
    JP i_done
i_shift4:
    EX DE,HL
    LD DE,i_buffer+4
    LDI
    LDI
    LDI
    LDI
    LD DE,i_buffer+24
    LDI
    LDI
    LDI
    LDI
    LD DE,i_buffer+12
    LDI
    LDI
    LDI
    LDI
    LD DE,i_buffer+32
    LDI
    LDI
    LDI
    LDI
    LD A,(i_lines)
    OR A
    JP NZ,i_done
    LD DE,i_buffer+20
    LDI
    LDI
    LDI
    LDI
    LD DE,i_buffer+40
    LDI
    LDI
    LDI
    LDI
    JP i_done
i_shift5:
    EX DE,HL
    LD DE,i_buffer+5
    LDI
    LDI
    LDI
    LD DE,i_buffer+24
    LDI
    LDI
    LDI
    LDI
    LDI
    LD DE,i_buffer+13
    LDI
    LDI
    LDI
    LD DE,i_buffer+32
    LDI
    LDI
    LDI
    LDI
    LDI
    LD A,(i_lines)
    OR A
    JP NZ,i_done
    LD DE,i_buffer+21
    LDI
    LDI
    LDI
    LD DE,i_buffer+40
    LDI
    LDI
    LDI
    LDI
    LDI
    JP i_done
i_shift6:
    EX DE,HL
    LD DE,i_buffer+6
    LDI
    LDI
    LD DE,i_buffer+24
    LDI
    LDI
    LDI
    LDI
    LDI
    LDI
    LD DE,i_buffer+14
    LDI
    LDI
    LD DE,i_buffer+32
    LDI
    LDI
    LDI
    LDI
    LDI
    LDI
    LD A,(i_lines)
    OR A
    JP NZ,i_done
    LD DE,i_buffer+22
    LDI
    LDI
    LD DE,i_buffer+40
    LDI
    LDI
    LDI
    LDI
    LDI
    LDI
    JP i_done
i_shift7:
    EX DE,HL
    LD DE,i_buffer+7
    LDI
    LD DE,i_buffer+24
    LDI
    LDI
    LDI
    LDI
    LDI
    LDI
    LDI
    LD DE,i_buffer+15
    LDI
    LD DE,i_buffer+32
    LDI
    LDI
    LDI
    LDI
    LDI
    LDI
    LDI
    LD A,(i_lines)
    OR A
    JP NZ,i_done
    LD DE,i_buffer+23
    LDI
    LD DE,i_buffer+40
    LDI
    LDI
    LDI
    LDI
    LDI
    LDI
    LDI
    JP i_done
    INCLUDE "phase.inc"
i_end:
    ASSERT $ <= $8000
