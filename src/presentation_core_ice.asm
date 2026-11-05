    ORG $8FD9
ice_entry:
    LD HL,$FA19
    LD ($C07E),HL
    LD HL,$FCF9
    LD ($C07C),HL
    LD A,($C016)
    LD ($C079),A
    JP ice_loop
ice_finish:
    LD IY,$C0FF
    PUSH AF
    LD A,H
    CP 160
    LD A,0
    JR NC,.store_v
    BIT 2,L
    JR Z,.store_v
    LD A,$40
.store_v:
    LD ($C600),A
    POP AF
    JP $9007
ice_entry_end:
    ASSERT $ <= $9007
    DS $9007-$,0

    ORG $9A24
ice_loop:
    LD A,($C016)
    LD H,A
    LD A,(IY+31)
    LD ($C078),A
    BIT 6,(IY+17)
    JR NZ,.subtract
    ADD A,H
    JR .arithmetic_done
.subtract:
    SUB H
.arithmetic_done:
    PUSH AF
    LD E,0
    CP $F0
    JR C,.below_f0
    SUB $60
    JR .normalized
.below_f0:
    CP $A0
    JR C,.normalized
    SUB $A0
    LD E,1
.normalized:
    LD (IY+31),A
    POP HL
    DEC B
    DEC IY
    JP P,ice_loop
    JP ice_finish
ice_loop_end:
    ASSERT $ <= $9A61
    DS $9A61-$,0
