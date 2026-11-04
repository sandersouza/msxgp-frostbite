; Direct ROM band transactions; no per-tile ice cache or metadata publication.
    INCLUDE "symbols.inc"
    ORG $7E5D              ;obsolete J strip, before preserved K initializer
pk_init:
    CALL $7F5F
    LD HL,$C1D1
    LD DE,$C1D2
    LD BC,31
    LD (HL),0
    LDIR
    LD HL,$C1F1
    LD DE,$C1F2
    LD BC,7
    LD (HL),255
    LDIR
    LD HL,$C080
    RET
pk_load_entry:
    PUSH AF
    LD A,7
    LD ($7000),A
    POP AF
    JP pk_load
pk_publish_entry:
    LD A,7
    LD ($7000),A
    JP pk_publish
pk_old_entry:
    LD A,7
    LD ($7000),A
    JP pk_old_key
pk_header:
    LD A,(pk_bank)
    LD ($7000),A
    LD BC,4
    LDIR                   ;raw-key far pointer and count, one owner
    LD A,(HL)
    LD (p_tl_program),A
    DEC DE
    LD A,(DE)
    LD (p_tl_count),A
    LD A,7
    LD ($7000),A
    RET
pk_names:
    CALL pk_names_tail
    PUSH AF
    LD A,7
    LD ($7000),A
    POP AF
    RET
pk_transfer:
    LD A,(pk_bank)
    LD ($7000),A
    CALL vdp_write
    LD A,7
    LD ($7000),A
    RET
pk_read_key:
    LD ($7000),A
    LD E,(HL)
    INC HL
    LD D,(HL)
    LD A,7
    LD ($7000),A
    RET
; A=complete CGT byte, B=count, DE=write address.33 MSX cycles between OUTs.
pk_fill:
    LD C,A
    LD A,E
    OUT ($99),A
    LD A,D
    OUT ($99),A
    LD A,C
.byte:
    OUT ($98),A
    NOP
    DEC B
    JP NZ,.byte
    RET
pk_resident_end:
    ASSERT $ <= $7F5F

    ORG $A10C
pk_records EQU $C1D1
pk_colors EQU $C1F1
pk_pointer EQU $C1F9
pk_bank EQU $C1FB
pk_ownerptr EQU $C1FC
pk_index EQU $C1FE
pk_pending EQU $C1C1       ;reclaims obsolete J strip scratch

; Preserve the original loader ABI but select one fixed, prepared packet.
pk_load:
    LD (p_tl_root),A
    LD A,B
    LD (p_tl_delta),A
    LD A,C
    LD (p_tl_y),A
    LD HL,p_template_deltas
    LD D,B
    LD B,10
    LD E,0
.delta:
    LD A,D
    CP (HL)
    JR Z,.found
    INC HL
    INC E
    DJNZ .delta
    JP p_world_fail
.found:
    LD A,E
    LD (p_tl_delta_index),A
    LD A,(p_tl_y)
    AND 7
    LD B,A
    ADD A,A
    ADD A,A
    ADD A,B
    ADD A,A                ;phase*10
    ADD A,E
    ADD A,35
    LD (pk_bank),A
    LD A,(p_tl_root)
    AND 15
    LD L,A
    LD H,0
    DUP 7
    ADD HL,HL
    EDUP
    LD DE,$B800
    ADD HL,DE
    LD (pk_pointer),HL
    LD A,(PAGE)
    DUP 4
    ADD A,A
    EDUP
    LD B,A
    LD A,(p_w_row)
    ADD A,A
    ADD A,A
    ADD A,B
    ADD A,pk_records&255
    LD E,A
    LD D,pk_records/256
    LD (pk_ownerptr),DE
    LD DE,pk_pending
    LD BC,112
    ADD HL,BC
    CALL pk_header
    CALL pk_names
    RET

; Original strip prologue selected physical row/base, color and water.
pk_publish:
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
    LD HL,(pk_pointer)
    LD A,(p_tl_count)
    DUP 3
    ADD A,A
    EDUP
    LD B,A
    CALL pk_transfer
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
    LD B,128               ;initialize all16 CGT slots, including future growth
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
    LDIR                   ;owner becomes valid after the complete band IO
    LD A,(p_tl_count)
    DEC A
    LD (p_ts_cursor),A
    XOR A
    LD (pt_error),A
    LD (p_tr_error),A
    RET

; Reconstruct exactly the rare old-ice key lazily, from its immutable record.
pk_old_key:
    LD HL,(p_w_name)
    LD A,(HL)
    LD D,A
    AND 63
    LD E,A
    LD A,(p_w_cachegroup)   ;context bank is valid before fixed-role resolution
    CP 3
    JR C,.target_bank
    SUB 3
.target_bank:
    CP 1
    JR NZ,.bank2
    LD A,E
    CP 35
    LD B,3
    LD C,19
    JR C,.row
    LD B,2
    LD C,35
    JR .row
.bank2:
    LD A,E
    CP 25
    LD B,1
    LD C,9
    JR C,.row
    LD B,0
    LD C,25
.row:
    LD A,E
    SUB C
    LD (pk_index),A
    LD A,D
    AND 64
    DUP 4
    SRL A
    EDUP
    ADD A,B
    ADD A,A
    ADD A,A
    ADD A,pk_records&255
    LD L,A
    LD H,pk_records/256
    LD (pk_ownerptr),HL
    PUSH HL
    INC L
    INC L
    INC L
    LD A,(pk_index)
    CP (HL)
    JP NC,p_world_fail
    POP HL
    LD E,(HL)
    INC L
    LD D,(HL)
    INC L
    LD A,(HL)
    PUSH AF
    EX DE,HL
    LD A,(pk_index)
    ADD A,A
    LD E,A
    LD D,0
    ADD HL,DE
    POP AF
    CALL pk_read_key
    LD (pfw_old),DE
    LD A,(p_w_cachegroup)
    CP 3
    JR C,.water_bank
    SUB 3
.water_bank:
    CP 1
    LD A,130
    JR Z,.water
    DEC A
.water:
    LD (pfw_old+2),A
    XOR A
    LD (pfw_old+3),A
    LD HL,(pk_ownerptr)
    LD A,L
    SUB pk_records&255
    ADD A,$C3
    LD L,A
    LD H,$E5
    LD A,(HL)              ;complete source row tuple's foreground
    LD (pfw_old+4),A
    LD A,9
    LD (pfw_old+5),A
    OR A
    RET
pk_end:
    ASSERT $ <= $AA68
