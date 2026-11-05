    INCLUDE "symbols.inc"
    ORG core_F875
az_start:
    LD A,($C001)
    SRL A
    SRL A
    SRL A
    CP 16
    JR C,.triangle
    XOR 31
.triangle:
    LD (core_lhs),A
    ADD A,$C2
    LD L,A
    LD H,(original_data+$100)/256
    LD A,(HL)
    LD (core_rhs),A
    LD B,3
    LD IY,$C003
    LD E,0
.lane:
    LD A,(IY+17)
    AND 3
    LD C,A
    LD L,A
    LD H,(original_data+$100)/256
    LD A,(HL)
    LD (IY+39),A
    LD A,C
    ADD A,A
    LD C,A
    CP 6
    LD A,8
    JR NZ,.mask
    ADD A,A
.mask:
    LD HL,$C001
    AND (HL)
    JR NZ,.shape
    INC C
.shape:
    LD A,C
    ADD A,10
    LD L,A
    LD H,(original_data+$100)/256
    LD A,(HL)
    LD (IY+35),A
    LD H,A
    LD A,C
    CP 2
    LD A,H
    JR C,.next
    LD H,A
    LD A,(core_lhs)
    LD C,A
    LD A,(core_rhs)
    ADD A,H
    CALL core_capture_v
    LD (IY+35),A
.next:
    DEC B
    DEC IY
    JP P,.lane
    LD IY,$C0FF
    JP core_F8B2
az_end:
    ASSERT $ <= core_F8B2
    DS core_F8B2-$,0
