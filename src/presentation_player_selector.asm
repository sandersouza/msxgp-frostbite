    ORG $ADD9
    LD A,($C27B)
    LD E,A
    LD D,0
    LD HL,$C280
    ADD HL,DE
    LD A,(HL)
    LD ($C28E),A
    OR A
    RET Z
    LD A,($C27A)
    LD E,A
    ADD A,A
    ADD A,E
    ADD A,A
    ADD A,A
    ADD A,A
    ADD A,$80
    LD L,A
    LD H,$C4
    LD ($C28C),HL
    RET
    ASSERT $ <= $ADFC
    DS $ADFC-$,0
