; A=one of239 exact prepared left-shore P0 sprite patterns.
; Output C500..C51F; two immutable16-byte halves. Preserve IX/IY/SP/IFF.
sp_build:
    PUSH IX
    LD L,A
    LD H,0
    ADD HL,HL
    ADD HL,HL
    LD DE,sp_directory
    ADD HL,DE
    PUSH HL
    POP IX
    LD DE,$C500
    DUP 2,half
    LD L,(IX+half*2)
    LD H,(IX+half*2+1)
    PUSH DE
    LD DE,sp_halves
    ADD HL,DE
    POP DE
    LD BC,16
    DUP 16
    LDI
    EDUP
    EDUP
    POP IX
    RET
sp_end:
