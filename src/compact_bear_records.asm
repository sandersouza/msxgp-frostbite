; A=original record0..95. One persistent exact64-byte record atDFC0..DFFF.
; DFBE is ID+1, published last: zero/FF are invalid at both cold entry paths.
; DFBF remains owned initializer state.
; IX/IY/SP/IFF preserved. Only cache bytes and stack are written.
br_record:
    LD C,A
    LD A,($DFBE)
    DEC A
    CP C
    JR Z,.hit
    LD A,C
    PUSH IX
    PUSH IY
    PUSH AF
    LD L,A
    LD H,0
    LD D,H
    LD E,L
    DUP 5
    ADD HL,HL
    EDUP
    ADD HL,DE
    LD DE,br_records
    ADD HL,DE
    PUSH HL
    POP IX
    LD A,255
    LD ($DFBE),A
    LD IY,$DFC0
    LD B,6
.pair:
    LD E,(IX+0)
    LD A,(IX+1)
    AND 1
    LD D,A
    CALL br_emit
    LD A,(IX+1)
    SRL A
    LD E,A
    LD A,(IX+2)
    RRCA
    LD D,A
    AND 128
    OR E
    LD E,A
    LD A,D
    AND 1
    LD D,A
    CALL br_emit
    LD DE,3
    ADD IX,DE
    DJNZ .pair
    PUSH IX
    POP HL
    LD DE,$DFF0
    LD BC,15
    LDIR
    XOR A
    LD (DE),A
    LD A,($DFF0)
    CP 3
    JR NZ,.ready
    LD HL,$DFE4
    LD DE,$DFE5
    LD BC,11
    LD (HL),0
    LDIR
.ready:
    POP AF
    INC A
    LD ($DFBE),A
    POP IY
    POP IX
.hit:
    LD HL,$DFC0
    RET

; DE=dense mask0..469 -> original raw ID + dense/empty-left predicate.
; Retain the caller's pair loop B and input IX.
br_emit:
    PUSH DE
    EX DE,HL
    ADD HL,HL
    LD DE,br_raw
    ADD HL,DE
    LD A,(HL)
    LD (IY+0),A
    INC HL
    LD A,(HL)
    LD C,A
    AND 63
    LD (IY+1),A
    POP DE
    LD (IY+2),E
    LD A,C
    AND 128
    OR D
    LD (IY+3),A
    LD DE,4
    ADD IY,DE
    RET
br_end:
