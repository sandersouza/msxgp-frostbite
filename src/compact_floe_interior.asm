; Interior-only original acquisition replacement; shared parameters once per tick.
cfi_acquire:
    LD A,(t_enabled)
    OR A
    JP Z,.legacy
    LD A,($C066)
    CP 9
    JP C,.legacy
    CP 154
    JP NC,.legacy
    LD A,($C01D)
    DUP 4
    RRCA
    EDUP
    LD L,A
    LD A,($C01C)
    OR L
    LD L,A
    LD H,HIGH floe_control_index
    LD A,(HL)
    CP 10
    JP NC,core_fault
    LD (cf_control),A
    LD A,($C06E)
    LD (cf_pose),A
    ADD A,A
    LD D,A
    DUP 4
    ADD A,A
    EDUP
    ADD A,D
    ADD A,D
    ADD A,D
    LD D,A
    LD A,($C06B)
    LD (cf_shift),A
    ADD A,A
    ADD A,D
    LD D,A
    LD A,($C06C)
    AND 8
    DUP 3
    RRCA
    EDUP
    LD (cf_reflection),A
    OR D
    LD C,A
    AND 7
    LD E,A
    LD D,0
    LD HL,floe_bit_masks
    ADD HL,DE
    LD A,(HL)
    LD (floe_viewmask),A
    LD A,C
    DUP 3
    RRCA
    EDUP
    AND 31
    LD (floe_viewbyte),A
    LD IX,$C01F
    LD IY,$C030
    LD B,123
    CALL cfi_row
    INC IX
    INC IY
    INC IY
    LD B,97
    CALL cfi_row
    INC IX
    INC IY
    INC IY
    LD B,71
    CALL cfi_row
    INC IX
    INC IY
    INC IY
    LD B,45
    JP cfi_row
.legacy:
    LD A,($C01D)
    JP floe_acquire+3

cfi_row:
    LD (IY+1),7
    LD A,(IX+0)
    CP 160
    JP NC,core_fault
    LD (cf_absolute_x),A
    LD A,($C064)
    SUB B
    JR C,.outside
    CP 33
    JR NC,.outside
    ADD A,45
    LD (cf_y),A
    LD A,($C066)
    LD C,A
    LD A,(cf_absolute_x)
    SUB C
    JR NC,.dx
    ADD A,160
.dx:
    LD (cf_dx),A
    JR .contact
.outside:
    XOR A
    LD (cf_y),A
.contact:
    CALL cf_contact
    LD (IY+0),A
    RET
cfi_end:
