; Byte-normalized rows trade 374 data bytes for bounded straight-line decoding.
; C7F0 phase, C7F1 owner; preserve IX/IY/SP/IFF. No scratch writes.
    IFNDEF CG_OUTPUT
CG_OUTPUT EQU $C200
    ENDIF
cg_build:
    LD A,($C7F1)
    LD L,A
    LD H,0
    LD DE,cg_bases
    ADD HL,DE
    LD C,(HL)
    LD L,A
    LD H,0
    LD DE,cg_waters
    ADD HL,DE
    LD B,(HL)
    LD A,($C7F0)
    LD L,A
    LD H,0
    LD DE,cg_directory
    ADD HL,DE
    LD L,(HL)
    LD H,0
    DUP 5
    ADD HL,HL
    EDUP
    LD DE,cg_rows
    ADD HL,DE
    LD DE,CG_OUTPUT
    DUP 30
    LD A,(HL)
    ADD A,C
    JR NC,$+3
    LD A,B
    LD (DE),A
    INC HL
    INC DE
    EDUP
    XOR A
    LD (DE),A
    INC DE
    LD (DE),A
    RET
cg_end:
