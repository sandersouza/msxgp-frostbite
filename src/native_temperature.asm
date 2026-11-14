; A=packed temperature glyph IDs. Original32-byte burst atC480. Units use
; sixteen absolute record pointers; tens store only nine consumed bytes each.
nt_build:
    PUSH AF
    AND 15
    LD L,A
    LD H,0
    ADD HL,HL
    LD DE,nt_units_directory
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    EX DE,HL
    LD DE,$C480
    LD BC,32
    DUP 32
    LDI
    EDUP
    POP AF
    DUP 4
    RRCA
    EDUP
    AND 15
    LD L,A
    LD H,0
    LD D,H
    LD E,L
    DUP 3
    ADD HL,HL
    EDUP
    ADD HL,DE
    LD DE,nt_tens
    ADD HL,DE
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
nt_build_end:
