; A=frozen footer tile0..187. Return original PGT address in DE. The nine
; monotonic run thresholds retain every original unused-VRAM allocation.
nr_address:
    LD C,A
    LD HL,nr_runs
.find:
    CP (HL)
    JR C,.found
    INC HL
    INC HL
    INC HL
    JR .find
.found:
    INC HL
    LD E,(HL)
    INC HL
    LD D,(HL)
    LD L,C
    LD H,0
    DUP 3
    ADD HL,HL
    EDUP
    ADD HL,DE
    EX DE,HL
    RET
nr_end:
