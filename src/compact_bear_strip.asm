; DE=prepared strip ID0..209. Four verified tile recipes -> exact64-byte strip.
; Output C480..C4BF (32 PGT then32 CGT); uses existing C520..537 scratch.
; cb_call takes the packed mask/context code in DE and preserves IX/IY.
bs_build:
    PUSH IX
    PUSH IY
    LD A,D
    OR E
    JR NZ,.decode
    ; Certified strip0 is64 literal FF bytes, independent of bear geometry.
    LD HL,$C480
    LD DE,$C481
    LD BC,63
    LD (HL),255
    LDIR
    JP .done
.decode:
    LD H,D
    LD L,E
    DUP 3
    ADD HL,HL
    EDUP
    LD DE,bs_codes
    ADD HL,DE
    PUSH HL
    POP IX
    DUP 4,column
    LD E,(IX+column*2)
    LD D,(IX+column*2+1)
    CALL cb_call
    LD HL,$C520
    LD DE,$C480+column*8
    LD BC,8
    DUP 8
    LDI
    EDUP
    LD HL,$C528
    LD DE,$C4A0+column*8
    LD BC,8
    DUP 8
    LDI
    EDUP
    EDUP
.done:
    POP IY
    POP IX
    RET
bs_end:
