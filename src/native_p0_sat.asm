; A=first pattern,B=1..6 entries,C=X,HL=signed dy/color pairs in a32-byte way.
; Metadata records and SAT entries cannot cross a256-byte page. IX is retained;
; final IY and p_s_sat are the same end pointer as the accepted indexed writer.
; AF/BC/DE/HL are scratch; return NC. No VDP, mapper, DI/EI or extra RAM.
ns_sat:
    LD IYL,A
    LD DE,SAT
.entry:
    LD A,(p_pc_cut)
    ADD A,(HL)
    INC L
    DEC A
    LD (DE),A
    INC E
    LD A,C
    LD (DE),A
    INC E
    LD A,IYL
    LD (DE),A
    INC E
    LD A,(HL)
    INC L
    LD (DE),A
    INC E
    LD A,IYL
    ADD A,4
    LD IYL,A
    DJNZ .entry
    LD (p_s_sat),DE
    PUSH DE
    POP IY
    OR A
    RET
ns_end:
