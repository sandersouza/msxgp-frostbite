; Five-phase header fragments replace the prepared pair/single dictionary.
; C7B0..B2: glyph0..33, second glyph0..33, kind0..4. Inputs immutable.
; Return HL=CH_OUTPUT, eight output bytes; no other scratch writes.
; Preserve IX/IY/SP/IFF. No mapper or VDP access.
    IFNDEF CH_OUTPUT
CH_OUTPUT EQU $C480
    ENDIF
ch_build:
    LD A,($C7B2)
    ADD A,A
    LD L,A
    LD H,0
    LD DE,ch_phases
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD B,(HL)
    LD A,($C7B0)
    CALL ch_address
    LD DE,CH_OUTPUT
    LD C,8
    DUP 8
    LDI
    EDUP
    LD A,B
    CP 255
    JR Z,.done
    LD E,B
    LD A,($C7B1)
    CALL ch_address
    LD DE,CH_OUTPUT
    LD B,8
.combine:
    LD A,(DE)
    OR (HL)
    LD (DE),A
    INC DE
    INC HL
    DJNZ .combine
.done:
    LD HL,CH_OUTPUT
    RET
ch_address:
    LD L,A
    ADD A,A
    ADD A,A
    ADD A,L
    ADD A,E
    LD L,A
    LD H,0
    DUP 3
    ADD HL,HL
    EDUP
    LD DE,ch_fragments
    ADD HL,DE
    RET
ch_end:
