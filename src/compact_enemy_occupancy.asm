; B group0..65, C variant (phaseX*8+phaseY). Return B exact legacy descriptor.
; No writes, IX/IY/SP/IFF preserved. All8448 combinations are represented.
co_lookup:
    LD L,B
    LD H,0
    ADD HL,HL
    ADD HL,HL
    ADD HL,HL
    LD A,C
    AND 7
    LD E,A
    LD D,0
    ADD HL,DE
    LD DE,co_directory
    ADD HL,DE
    LD L,(HL)
    LD H,0
    DUP 4
    ADD HL,HL
    EDUP
    LD A,C
    RRCA
    RRCA
    RRCA
    AND 15
    LD E,A
    LD D,0
    ADD HL,DE
    LD DE,co_rows
    ADD HL,DE
    LD B,(HL)
    RET
co_end:
