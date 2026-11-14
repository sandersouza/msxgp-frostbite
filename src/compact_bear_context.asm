; HL=original10-bit certified-context address. A=exact old byte or FF.
; Nine sparse (word index, byte value) entries, preserving IX/IY/SP/IFF.
cx_find_context:
    EX DE,HL
    LD HL,cx_entries
    LD B,9
.entry:
    LD A,(HL)
    INC HL
    CP E
    JR NZ,.skip_high
    LD A,(HL)
    INC HL
    CP D
    JR NZ,.skip_value
    LD A,(HL)
    RET
.skip_high:
    INC HL
.skip_value:
    INC HL
    DJNZ .entry
    LD A,255
    RET
cx_end:
