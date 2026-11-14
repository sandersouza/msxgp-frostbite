; A=packed temperature glyph indices. Exact 32-byte burst record at C480.
; Units are full32-byte records; tens contribute only nine variable bytes.
ct_build:
    PUSH AF
    AND 15
    LD L,A
    LD H,0
    DUP 5
    ADD HL,HL
    EDUP
    LD DE,ct_units
    ADD HL,DE
    LD DE,$C480
    LD BC,32
    DUP 32
    LDI
    EDUP
    POP AF
    AND $F0
    LD L,A
    LD H,HIGH ct_tens
    ASSERT LOW ct_tens = 0
    LD DE,$C480
    LD A,(DE)
    OR (HL)
    LD (DE),A
    INC HL
    LD E,$83
    DUP 7
    LD A,(DE)
    OR (HL)
    LD (DE),A
    INC DE
    INC HL
    EDUP
    LD E,$9B
    LD A,(DE)
    OR (HL)
    LD (DE),A
    LD HL,$C480
    RET
ct_end:
