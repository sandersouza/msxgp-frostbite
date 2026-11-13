; Reconstruct all48 bytes of the inherited enemy buffer without packet banks.
; C7E0..E2: group0..65, horizontal phase0..15, vertical phase0..7.
; C7E5..E9 scratch. C180..C1AF output. Return A=third-column-empty flag.
; Reuse aligned ct_original(1KiB), ct_expansion(1KiB), ct_reverse(256B),
; plus ct_shapes(33B). Preserve IX/IY/SP/IFF. No mapper or VDP accesses.
ct_build:
    PUSH IX
    PUSH IY
    XOR A
    LD HL,$C180
    LD DE,$C181
    LD BC,47
    LD (HL),A
    LDIR
    LD ($C7E9),A
    LD A,($C7E0)
    LD E,A
    AND 1
    LD ($C7E6),A
    LD A,E
    SRL A
    LD L,A
    LD H,0
    LD DE,ct_shapes
    ADD HL,DE
    LD A,(HL)
    ADD A,7
    LD E,A
    LD D,0
    LD HL,ct_original+$100
    ADD HL,DE
    PUSH HL
    POP IY
    LD A,($C7E1)
    LD E,A
    AND 1
    ADD A,A
    ADD A,HIGH ct_expansion
    LD ($C7E8),A
    LD A,E
    SRL A
    ADD A,E
    AND 7
    LD ($C7E5),A
    LD A,($C7E2)
    ADD A,$80
    LD L,A
    LD H,$C1
    PUSH HL
    POP IX
    LD A,8
    LD ($C7E7),A
.row:
    LD A,(IY+0)
    DEC IY
    LD L,A
    LD A,($C7E6)
    OR A
    JR Z,.normal
    LD H,HIGH ct_reverse
    LD L,(HL)
.normal:
    LD H,0
    ADD HL,HL
    LD A,($C7E8)
    ADD A,H
    LD H,A
    LD D,(HL)
    INC HL
    LD E,(HL)
    LD C,0
    LD A,($C7E5)
    OR A
    JR Z,.shifted
.shift:
    SRL D
    RR E
    RR C
    DEC A
    JR NZ,.shift
.shifted:
    LD (IX+0),D
    LD (IX+8),E
    LD (IX+16),C
    LD A,($C7E9)
    OR C
    LD ($C7E9),A
    INC IX
    LD A,IXL
    AND 7
    JR NZ,.next
    LD DE,16
    ADD IX,DE
.next:
    LD A,($C7E7)
    DEC A
    LD ($C7E7),A
    JR NZ,.row
    LD A,($C7E9)
    OR A
    LD A,0
    JR NZ,.done
    INC A
.done:
    POP IY
    POP IX
    RET
ct_end:
