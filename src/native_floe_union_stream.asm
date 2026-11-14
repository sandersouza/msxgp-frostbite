; Exact phase0 PGT stream from two source-mask planes. Literal basis cells
; retain the original OUTI path; full interior ice is explicitly in the basis.
; Same DE/IX/IY and paced VDP/interrupt ABI as compact_floe_stream.asm.
nf_stream:
    PUSH DE
    PUSH IX
    PUSH IY
    PUSH DE
    LD A,(pk_bank)
    SUB 35
    DUP 4
    RLCA
    EDUP
    LD B,A
    LD HL,(pk_pointer)
    ADD HL,HL
    LD A,H
    AND 15
    OR B
    LD L,A
    LD H,0
    ADD HL,HL
    LD DE,nf_directory
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    LD HL,nf_indices
    ADD HL,DE
    PUSH HL
    POP IX
    POP DE
    LD A,(pk_pending+3)
    LD IYL,A
    DI
    LD A,E
    OUT ($99),A
    LD A,D
    OUT ($99),A
    CALL t_restore_interrupts
    LD C,$98
.tile:
    LD L,(IX+0)
    LD H,0
    DUP 3
    ADD HL,HL
    EDUP
    LD DE,nf_basis
    ADD HL,DE
    LD A,(IX+1)
    OR A
    JR Z,.literal
    PUSH HL
    LD L,A
    LD H,0
    DUP 3
    ADD HL,HL
    EDUP
    ADD HL,DE
    EX DE,HL
    POP HL
    LD B,8
.union:
    LD A,(DE)
    OR (HL)
    OUT (C),A
    INC DE
    INC HL
    DJNZ .union
    JR .next
.literal:
    LD B,8
.byte:
    OUTI
    JP NZ,.byte
.next:
    INC IX
    INC IX
    DEC IYL
    JR NZ,.tile
    POP IY
    POP IX
    POP DE
    RET
nf_stream_end:
