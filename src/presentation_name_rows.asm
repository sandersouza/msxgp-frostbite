; A=root0..159, HL=one30-byte row in this page's64-byte strip cache,
; DE=32-byte-aligned inactive CPU NAME row. All32 bytes are defined.
; Cache source is immutable; no VRAM or original/ABI/heap writes occur.
p_tn_error EQU $C2BC
p_template_name_row:
    CP 160
    JP NC,p_template_name_fail
    PUSH AF
    LD A,(PAGE)
    CP 2
    JR NC,.invalid
    LD B,A
    ADD A,$DE
    CP H
    JR NZ,.invalid
    LD A,L
    AND 63
    JR Z,.source
    CP 30
    JR NZ,.invalid
.source:
    LD A,E
    AND 31
    JR NZ,.invalid
    LD A,B
    OR A
    LD A,D
    JR Z,.page0
    SUB $CD
    JR .destination
.page0:
    SUB $C8
.destination:
    CP 3
    JR NC,.invalid
    POP AF
    DUP 4
    SRL A
    EDUP
    LD B,A
    ADD A,A
    ADD A,B
    LD C,A
    LD B,0
    PUSH DE
    LD A,128
    LD (DE),A               ;col0 is always black
    INC DE
    PUSH HL
    PUSH BC
    LD A,30
    SUB C
    LD C,A
    ADD HL,BC
    POP BC
    LD A,C
    OR A
    JR Z,.head
    LDIR                    ;wrapped suffix, never call LDIR with BC=0
.head:
    POP HL
    LD A,E
    AND 31
    LD C,A
    LD A,31
    SUB C
    LD C,A
    LD B,0
    LDIR                    ;remaining prefix, exactly30 cells in total
    LD A,128
    LD (DE),A               ;col31 is always black
    POP DE
    INC DE
    LD (DE),A               ;clip col1 AFTER world translation
    XOR A
    LD (p_tn_error),A
    RET
.invalid:
    POP AF
p_template_name_fail:
    LD A,1
    LD (p_tn_error),A
    SCF
    RET
