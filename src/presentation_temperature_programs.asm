; Exact lower-temperature three-column updates; all other header work falls back.
    INCLUDE "symbols.inc"
    ORG $EFE3
al_copy:
    CALL t_mapper
    LDIR
    LD A,131
    JP t_mapper
al_exit:
    CALL t_mapper
    JP (HL)
al_ram_end:
    ASSERT $ <= $F000

    ORG $69FC
al_gate:
    LD A,(hy_first)
    OR A
    JP NZ,al_original
    LD A,(hy_color)
    OR A
    JP NZ,al_original
    LD HL,(hy_up)
    LD A,H
    OR L
    JP NZ,al_original
    LD HL,(hy_lo)
    LD A,H
    OR A
    JP NZ,al_original
    LD A,L
    CP 14
    JP NZ,al_original
    LD A,(t_bank)
    PUSH AF
    LD A,131
    CALL t_mapper
    JP al_body
al_original:
    LD A,(hy_color)
    JP AL_RESUME
al_gate_end:
    ASSERT $ <= $6A46

    ORG $B800
al_body:
    LD A,(p_h_codes+6)
    DUP 3
    SRL A
    EDUP
    CP 16
    JP NC,.unsupported
    DUP 4
    RLCA
    EDUP
    LD B,A
    LD A,(p_h_codes+7)
    DUP 3
    SRL A
    EDUP
    CP 16
    JP NC,.unsupported
    OR B
    LD B,A
    DUP 6
    SRL A
    EDUP
    ADD A,127
    PUSH AF
    LD A,B
    DUP 3
    RRCA
    EDUP
    AND 7
    ADD A,$B8
    LD H,A
    LD A,B
    AND 7
    DUP 5
    RLCA
    EDUP
    LD L,A
    LD DE,$C480
    LD BC,32
    POP AF
    CALL al_copy
    LD HL,(hy_meta)
    LD DE,6
    ADD HL,DE
    PUSH HL
    POP IX
    LD IY,$C498
    LD HL,hy_tile
    INC (HL)
    LD A,1
    LD (hy_col),A
    LD HL,$C480
.column:
    CALL hy_address
    LD A,E
    ADD A,87
    LD E,A
    JR NC,.middle_address
    INC D
.middle_address:
    LD B,1
    CALL vdp_write
    CALL hy_address
    LD A,E
    ADD A,160
    LD E,A
    JR NC,.bottom_address
    INC D
.bottom_address:
    LD B,7
    CALL vdp_write
    PUSH HL
    LD B,(IY)
    LD A,(IX+61)
    AND 15
    OR B
    LD (IX+61),A
    LD (IX+121),B
    LD A,(IY+1)
    LD (IX+62),A
    LD (IX+122),A
    INC IY
    INC IY
    LD DE,6
    ADD IX,DE
    LD HL,hy_tile
    INC (HL)
    LD HL,hy_col
    INC (HL)
    LD A,(HL)
    CP 4
    POP HL
    JP NZ,.column
    POP AF
    LD A,118
    LD HL,w_save
    JP al_exit
.unsupported:
    POP AF
    LD HL,al_original
    JP al_exit
al_body_end:
    ASSERT $ <= $C000
