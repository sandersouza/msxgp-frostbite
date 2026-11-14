; DE: low9 bits select470 immutable masks, next4 bits select9 contexts.
; Exact16-byte tile C520, mask scratch C530. Preserve IX/IY/SP/IFF.
cb_build:
    PUSH IX
    PUSH IY
    LD A,D
    SRL A
    AND 15
    PUSH AF
    LD A,D
    AND 1
    LD H,A
    LD L,E
    DUP 3
    ADD HL,HL
    EDUP
    LD DE,cb_patterns
    ADD HL,DE
    LD DE,$C530
    LD BC,8
    LDIR
    POP AF
    LD L,A
    LD H,0
    DUP 5
    ADD HL,HL
    EDUP
    LD DE,cb_contexts
    ADD HL,DE
    LD DE,$C520
    LD BC,16
    LDIR
    LD C,(HL)
    INC HL
    LD D,(HL)
    INC HL
    LD E,(HL)
    LD HL,$C530
    LD B,8
.clip:
    LD A,(HL)
    AND C
    LD (HL),A
    INC HL
    DJNZ .clip
    LD A,E
    OR A
    JR Z,.merge
    LD A,D
    DUP 4
    RLCA
    EDUP
    OR 4
    PUSH AF
    LD HL,$C530
    LD DE,$C520
    LD BC,8
    LDIR
    ; Water contexts use the original literal mask on every row, even empty.
    POP AF
    LD B,8
.water:
    LD (DE),A
    INC DE
    DJNZ .water
    JR .done
.merge:
    LD IX,$C530
    LD IY,$C520
    LD B,8
.row:
    LD A,(IX+0)
    INC IX
    OR A
    JR Z,.next
    LD E,A
    LD C,(IY+8)
    LD A,C
    DUP 4
    RRCA
    EDUP
    AND 15
    CP D
    JR Z,.foreground
    LD H,A
    LD A,C
    AND 15
    CP D
    JR Z,.background
    LD L,A
    CP H
    JR Z,.replace
    LD A,E
    CPL
    AND (IY+0)
    JR Z,.replace
    LD L,H
.replace:
    LD (IY+0),E
    LD A,D
    DUP 4
    RLCA
    EDUP
    OR L
    LD (IY+8),A
    JR .next
.foreground:
    LD A,(IY+0)
    OR E
    LD (IY+0),A
    JR .next
.background:
    LD A,E
    CPL
    AND (IY+0)
    LD (IY+0),A
.next:
    INC IY
    DJNZ .row
.done:
    POP IY
    POP IX
    RET
cb_end:
