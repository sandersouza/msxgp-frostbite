; Every original phase0 packet, exact live prefix atC480..BF. Two byte plane
; selectors replace the former word offset in each existing immutable entry.
nf_packet:
    PUSH IX
    PUSH IY
    LD HL,($C7B4)
    LD DE,nf_counts
    ADD HL,DE
    LD A,(HL)
    LD IYL,A
    LD HL,($C7B4)
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
    LD DE,$C480
.tile:
    LD A,(IX+0)
    LD C,(IX+1)
    INC IX
    INC IX
    CALL nf_tile
    DEC IYL
    JR NZ,.tile
    POP IY
    POP IX
    RET

; A,C=two plane indices, DE=8-byte destination; return DE+=8. IX/IY preserved.
nf_tile:
    PUSH IX
    PUSH DE
    LD L,A
    LD H,0
    DUP 3
    ADD HL,HL
    EDUP
    LD DE,nf_basis
    ADD HL,DE
    PUSH HL
    LD L,C
    LD H,0
    DUP 3
    ADD HL,HL
    EDUP
    ADD HL,DE
    EX DE,HL
    POP HL
    POP IX
    LD B,8
.row:
    LD A,(DE)
    OR (HL)
    LD (IX+0),A
    INC DE
    INC HL
    INC IX
    DJNZ .row
    PUSH IX
    POP DE
    POP IX
    RET
nf_end:
