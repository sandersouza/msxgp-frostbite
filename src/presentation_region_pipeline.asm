; RAM-resident fixed regions; mapper-changing helpers cannot unmap this code.
    INCLUDE "symbols.inc"
    ORG r_init_origin
r_init:
    CALL qe_init
    LD A,115
    LD ($7000),A
    LD HL,$B800
    LD DE,r_header
    LD BC,r_end-r_header
    LDIR
    LD HL,$E880
    LD DE,$E881
    LD BC,127
    LD (HL),255
    LDIR
    LD A,1
    LD ($7000),A
    RET
r_init_end:
    ASSERT $ <= $7F5F

    ORG $E900
rh_owner EQU $E8E0
rh_changed EQU $E8E2
rh_mask EQU $E8E4
rh_bit EQU $E8E6
rh_top EQU $E8E8
rh_bottom EQU $E8E9
rh_pair EQU $E8EA
rh_class EQU $E8EB
rp_last EQU $E8FE

; Original prologue prepared colours; keep the authoritative glyph/key selector.
r_header:
    CALL p_template_header_keys
    JP C,p_world_fail
    LD HL,$E880
    LD A,(PAGE)
    OR A
    JR Z,.owner
    LD L,$B0
.owner:
    LD (rh_owner),HL
    LD DE,40
    ADD HL,DE
    LD DE,p_th_colours
    LD B,3
    CALL r_compare
    LD HL,$03FF
    JR NZ,.changed
    LD HL,0
    LD (rh_changed),HL
    INC HL
    LD (rh_bit),HL
    LD HL,(rh_owner)
    LD DE,p_th_columns
    XOR A
    LD (p_h_index),A
.column_identity:
    PUSH HL
    PUSH DE
    LD B,4
    CALL r_compare
    POP DE
    POP HL
    JR Z,.same_column
    PUSH HL
    LD HL,(rh_changed)
    LD BC,(rh_bit)
    LD A,L
    OR C
    LD L,A
    LD A,H
    OR B
    LD H,A
    LD (rh_changed),HL
    POP HL
.same_column:
    LD BC,4
    ADD HL,BC
    DUP 4
    INC DE
    EDUP
    PUSH HL
    LD HL,(rh_bit)
    ADD HL,HL
    LD (rh_bit),HL
    POP HL
    LD A,(p_h_index)
    INC A
    LD (p_h_index),A
    CP 10
    JR NZ,.column_identity
    LD HL,(rh_changed)
.changed:
    LD (rh_changed),HL
    XOR A
    LD (p_h_y),A
.band:
    XOR A
    LD (p_fx_bank),A
    LD (p_h_index),A
    LD A,(p_h_y)
    LD (p_w_top),A
    LD A,5
    LD (p_w_col),A
    CALL p_fast_cell
    LD A,(p_h_y)
    LD B,A
    ADD A,A
    ADD A,A
    ADD A,B
    ADD A,A
    LD B,A
    LD A,(PAGE)
    OR A
    LD A,B
    JR Z,.names
    ADD A,30
.names:
    LD L,A
    LD H,0
    LD DE,r_header_names
    ADD HL,DE
    LD DE,(p_w_name)
    LD BC,10
    LDIR
    LD HL,(rh_changed)
    LD (rh_mask),HL
    LD A,H
    OR L
    JR Z,.next_band
    LD A,(p_h_y)
    LD B,A
    ADD A,A
    ADD A,A
    ADD A,B
    ADD A,A
    ADD A,8
    CALL p_fixed_dynamic_id
    LD (p_w_tile),A
    CALL p_fixed_key_address
    LD (p_fx_meta),HL
.cell:
    LD HL,(rh_mask)
    SRL H
    RR L
    LD (rh_mask),HL
    JR NC,.skip
    CALL p_template_header_key
    JP C,p_world_fail
    CALL p_fixed_put_header
    JP C,p_world_fail
.skip:
    CALL r_advance
    LD A,(p_h_index)
    INC A
    LD (p_h_index),A
    CP 10
    JR NZ,.cell
.next_band:
    LD A,(p_h_y)
    INC A
    LD (p_h_y),A
    CP 3
    JP NZ,.band
    LD HL,p_th_columns
    LD DE,(rh_owner)
    LD BC,43
    LDIR                    ;validity follows every required plane and NAME
    JP r_igloo

r_compare:
    LD A,(DE)
    CP (HL)
    RET NZ
    INC DE
    INC HL
    DJNZ r_compare
    RET

r_advance:
    LD HL,(p_w_name)
    INC HL
    LD (p_w_name),HL
    LD HL,(p_fx_meta)
    LD DE,6
    ADD HL,DE
    LD (p_fx_meta),HL
    LD HL,p_w_tile
    INC (HL)
    RET

; Preserve exact background-specific PGT/CGT; only reachable interior BGs map.
r_igloo:
    XOR A
    LD (p_h_level),A
.row:
    LD A,(p_h_level)
    ADD A,3
    CALL p_fast_row_dirty
    JP Z,.next_row
    LD A,(p_h_level)
    OR A
    JR NZ,.paired
    LD (rh_top),A
    LD A,($C044)
    JR .bottom
.paired:
    ADD A,A
    LD B,A
    LD A,$45
    SUB B
    LD L,A
    LD H,$C0
    LD A,(HL)
    LD (rh_top),A
    DEC L
    LD A,(HL)
.bottom:
    LD (rh_bottom),A
    LD A,(p_h_level)
    ADD A,3
    LD (p_w_top),A
    LD A,22
    LD (p_w_col),A
    CALL p_fast_cell
    LD A,(p_h_level)
    LD B,A
    ADD A,A
    ADD A,B
    ADD A,A
    ADD A,38
    CALL p_fixed_dynamic_id
    LD (p_w_tile),A
    CALL p_fixed_key_address
    LD (p_fx_meta),HL
    XOR A
    LD (p_h_bit),A
    LD (p_fx_bank),A
.cell:
    LD A,(p_h_bit)
    LD L,A
    LD H,0
    LD DE,r_classes
    ADD HL,DE
    LD A,(HL)
    LD (rh_class),A
    RRCA
    RRCA
    LD C,A                 ;class*4 indexes the existing four-mask table
    LD A,(rh_top)
    AND 3
    LD B,A
    ADD A,C
    LD L,A
    LD H,0
    LD DE,p_fast_igloo_masks
    ADD HL,DE
    LD A,(HL)
    LD (pf_key),A
    LD A,(rh_bottom)
    AND 3
    LD E,A
    ADD A,A
    ADD A,A
    OR B
    LD (rh_pair),A
    LD A,E
    ADD A,C
    LD L,A
    LD H,0
    LD DE,p_fast_igloo_masks
    ADD HL,DE
    LD A,(HL)
    LD (pf_key+1),A
    LD B,A
    LD A,(pf_key)
    OR B
    JP Z,.next_cell
    LD HL,(p_w_name)
    LD A,(HL)
    SUB 128
    CP r_background_count
    JP NC,p_world_fail
    LD L,A
    LD H,0
    LD DE,r_background_map
    ADD HL,DE
    LD A,(HL)
    CP 255
    JP Z,p_world_fail
    LD C,A                 ;compact reachable background index
    LD HL,(p_w_name)
    LD A,(HL)
    LD (pf_key+2),A
    LD A,14
    LD (pf_key+3),A
    XOR A
    LD (pf_key+4),A
    LD A,5
    LD (pf_key+5),A
    LD HL,(p_fx_meta)
    LD DE,pf_key
    LD B,6
    PUSH BC
    CALL r_compare
    POP BC
    JR Z,.name
    LD L,C
    LD H,0
    LD D,H
    LD E,L
    ADD HL,HL
    ADD HL,DE
    DUP 4
    ADD HL,HL
    EDUP                    ;compact background*48
    LD A,(rh_class)
    LD B,A
    LD A,(rh_pair)
    OR B
    LD E,A
    LD D,0
    ADD HL,DE
    CALL r_record
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
    LD A,D
    ADD A,$20
    LD D,A
    LD HL,pt_tile+8
    LD B,8
    CALL vdp_write
    XOR A
    LD (pt_error),A
    LD HL,pf_key
    LD DE,(p_fx_meta)
    LD BC,6
    LDIR                    ;typed identity follows complete physical planes
.name:
    LD HL,(p_w_name)
    LD A,(p_w_tile)
    LD (HL),A
.next_cell:
    CALL r_advance
    LD A,(p_h_bit)
    LD B,1
    CP 2
    JR NZ,.shift
    INC B
.shift:
    LD HL,rh_top
    SRL (HL)
    INC L
    SRL (HL)
    DJNZ .shift
    LD A,(p_h_bit)
    INC A
    LD (p_h_bit),A
    CP 6
    JP NZ,.cell
.next_row:
    LD A,(p_h_level)
    INC A
    LD (p_h_level),A
    CP 3
    JP NZ,.row
    OR A
    RET

; HL=index of aligned16-byte record. Code remains mapped in RAM throughout.
r_record:
    LD A,H
    ADD A,A
    LD B,A
    LD A,L
    RLCA
    AND 1
    OR B
    ADD A,116
    LD ($7000),A
    LD A,L
    AND 127
    LD L,A
    LD H,0
    DUP 4
    ADD HL,HL
    EDUP
    LD DE,$B800
    ADD HL,DE
    LD DE,pt_tile
    LD BC,16
    LDIR
    RET

r_player_lookup:
    CALL p_player_variant_default
    RET C
    LD A,(PAGE)
    ADD A,rp_last&255
    LD L,A
    LD H,rp_last/256
    LD A,(HL)
    AND 3
    CALL p_player_variant_set
    LD A,(IX)
    CP 1
    JR NZ,.fallback
    LD HL,p_pc_key
    DUP 7,rp_n
    LD A,(HL)
    CP (IX+1+rp_n)
    JR NZ,.fallback
    INC L
    EDUP
    OR A                    ;retain the original last-key A/flag result
    RET
.fallback:
    CALL p_player_variant_default
    RET C
    CALL r_original_scan
    PUSH AF
    PUSH HL
    LD A,(PAGE)
    ADD A,rp_last&255
    LD L,A
    LD H,rp_last/256
    LD A,(p_pc_way)
    LD (HL),A
    POP HL
    POP AF
    RET

r_classes:
    DB 0,16,32,0,16,32
r_header_names:
    DUP 30,rh_name0
    DB 8+rh_name0
    EDUP
    DUP 30,rh_name1
    DB 72+rh_name1
    EDUP
r_background_map:
    INCBIN "igloo-map.bin"
r_end:
    ASSERT $ <= $F000
