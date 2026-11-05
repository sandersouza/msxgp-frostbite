; Guarded decoded FEB8 effect summary, only the rF850 context.
; Existing bank2 body 9709..978F; no new ROM/RAM allocation.
    ORG $9709
start:
    LD A,(IY+96)
    LD D,A
    LD C,8
    BIT 7,A
    JR Z,mask
    SUB 128
    RRCA
    RRCA
    RRCA
    RRCA
    AND 7
    LD C,A
mask:
    LD A,C
    ADD A,$D7
    LD L,A
    LD H,$A5
    LD A,(IY+92)
    AND (HL)
    LD C,A
    CP 56
    JP NC,$9834              ; Identical depth1 sibling, before any RAM/V write.
    BIT 7,D
    JR Z,table
    LD HL,$FEC4
    LD ($C07C),HL            ; Original nested JSR return bytes, high case only.
table:
    LD A,C
    ADD A,$C8
    LD L,A
    LD H,$A7
    LD A,(HL)
    LD H,A
    AND 15
    LD (IY+88),A
    LD A,C
    OR A
    JR Z,zero
    LD A,H
    AND 240
    ADD A,D
    PUSH AF
    POP HL
    LD D,H
    LD H,$82
    LD A,(HL)
    LD ($C600),A
    LD A,D
    CP 160
    LD E,0
    JR C,store
    INC E
    SUB 96
    PUSH AF
    POP HL
    LD D,H
    LD H,$82
    LD A,(HL)
    LD ($C600),A
    LD A,D
store:
    LD (IY+84),A
    RET
zero:
    LD E,0
    BIT 7,D
    JR Z,zero_store
    XOR A
    LD ($C600),A
    LD A,D
    RRCA
    RRCA
    RRCA
    AND 1
    LD E,A
zero_store:
    XOR A
    LD (IY+84),A
    RET
end:
    ASSERT $ <= $9790
    DS $9790-$,0
