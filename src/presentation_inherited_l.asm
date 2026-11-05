    ORG $B253
l_entry:
    LD A,($C066)
l_eligible:
    CP 84
    RET C
    PUSH HL
    LD A,($C064)
    SUB 19
    CP 115
    JR NC,.invalid
    LD L,A
    LD H,0
    LD DE,l_limits
    ADD HL,DE
    LD A,($C066)
    CP (HL)
    POP HL
    RET
.invalid:
    OR A
    POP HL
    RET
l_x:
    LD L,A
    LD H,0
    LD E,A
    LD D,H
    ADD HL,HL
    ADD HL,DE
    SRL H
    RR L
    LD A,L
    ADD A,8
    LD C,A
    RET
l_limits:
    INCBIN "limits.bin"
l_end:
    ASSERT l_end <= $B300
