; Same AL eligibility and per-stream interrupt policy; four exact PGT streams.
    INCLUDE "symbols.inc"
    ORG $B800
burst_body:
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
    LD HL,hy_tile
    INC (HL)
    CALL hy_address
    LD HL,87
    ADD HL,DE
    EX DE,HL
    LD HL,$C480
    LD B,1
    CALL vdp_write
    EX DE,HL
    LD BC,8
    ADD HL,BC
    EX DE,HL
    LD B,1
    CALL vdp_write
    EX DE,HL
    LD BC,8
    ADD HL,BC
    EX DE,HL
    LD B,1
    CALL vdp_write
    EX DE,HL
    LD BC,57
    ADD HL,BC
    EX DE,HL
    LD B,24
    CALL vdp_write
    ; A valid kind18 bottom tile has row7=0; the existing gate is unchanged.
    LD HL,(hy_meta)
    LD DE,13
    ADD HL,DE
    PUSH HL
    POP IX
    LD A,($C49B)
    AND $F0
    LD B,A
    LD A,(IX+54)
    AND 15
    OR B
    LD (IX+54),A
    LD (IX+114),B
    LD A,($C49B)
    AND 15
    ADD A,A
    ADD A,A
    LD (IX+55),A
    LD (IX+115),A
    ADD A,A
    ADD A,A
    LD B,A
    LD (IX+120),A
    LD (IX+126),A
    LD A,(IX+60)
    AND 15
    OR B
    LD (IX+60),A
    LD A,(IX+66)
    AND 15
    OR B
    LD (IX+66),A
    XOR A
    LD (IX+61),A
    LD (IX+121),A
    LD A,128
    LD (IX+67),A
    LD (IX+127),A
    ; Retain the successful AL scratch/ABI endpoints used by the old body.
    LD DE,11
    ADD IX,DE
    LD IY,$C49E
    LD A,(hy_tile)
    ADD A,3
    LD (hy_tile),A
    LD A,4
    LD (hy_col),A
    POP AF
    LD A,118
    LD HL,w_save
    JP al_exit
.unsupported:
    POP AF
    LD HL,al_original
    JP al_exit
burst_body_end:
    ASSERT $ <= $C000
