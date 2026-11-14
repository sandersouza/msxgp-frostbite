; Exact phase0 dictionary stream. Called through resident mapped bridge.
; DE=VDP destination. Retain DE and IX/IY; reuse existing IRQ-safe port policy.
cs_stream:
    PUSH DE
    PUSH IX
    PUSH IY
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
    PUSH DE
    LD DE,cp_directory
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    LD HL,cp_indices
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
    LD DE,cp_patterns
    LD C,$98
.tile:
    LD L,(IX+0)
    LD H,(IX+1)
    INC IX
    INC IX
    ADD HL,DE
    LD B,8
.byte:
    OUTI
    JP NZ,.byte
    DEC IYL
    JR NZ,.tile
    POP IY
    POP IX
    POP DE
    RET
cs_stream_end:
