; Preserve the header's upper/lower and special-column dictionary semantics.
hc_lookup:
    LD A,(hy_half)
    LD E,A
    LD D,0
    LD HL,pt_glyphs
    ADD HL,DE
    LD C,(HL)
    INC HL
    LD B,(HL)
    LD A,(IY+2)
    CP 5
    JR C,.valid_kind
    LD A,4
.valid_kind:
    LD ($C7B2),A
    LD A,(hy_half)
    OR A
    JR Z,.regular
    LD A,(hy_col)
    CP 3
    JR Z,.temperature
    CP 4
    JR Z,.icon
    CP 6
    JR Z,.level
    CP 7
    JR Z,.lives
.regular:
    LD A,C
    LD ($C7B0),A
    LD A,B
    LD ($C7B1),A
    LD A,52
    CALL t_mapper
    JP $B800
.temperature:
    LD B,32
    LD A,3
    JR .kind
.icon:
    LD A,B
    CP 33
    LD B,10
    JR NZ,.icon_ready
    LD B,33
.icon_ready:
    LD C,32
    LD A,1
    JR .kind
.level:
    LD A,C
    CP 33
    LD C,10
    JR NZ,.level_ready
    LD C,33
.level_ready:
    LD B,10
    LD A,3
    JR .kind
.lives:
    LD C,10
    LD A,1
.kind:
    LD ($C7B2),A
    JR .regular
hc_end:
