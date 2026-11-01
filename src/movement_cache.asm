; Inactive name-page layout and HUD/igloo metadata. Atlas tiles are immutable.
cache_init:
    LD HL,$CB00
    LD DE,$CB01
    LD BC,127
    LD (HL),255
    LDIR
    RET

handle_layout_change:
    LD A,(PAGE)
    LD E,A
    LD D,0
    LD HL,$CB70
    ADD HL,DE
    LD A,(INPUT+31)
    CP (HL)
    RET Z
    LD C,(HL)
    LD (HL),A
    LD A,C
    CP 2
    RET NC
    OR A
    LD E,14*32&255
    LD B,32
    JR Z,.erase
    LD E,15*32&255
    LD B,64
.erase:
    LD A,(PAGE)
    ADD A,A
    ADD A,A
    ADD A,$59
    LD D,A
    LD HL,zero_names
    JP vdp_write

upload_static_names:
    LD A,(PAGE)
    LD E,A
    LD D,0
    LD HL,$CB72
    ADD HL,DE
    LD A,(INPUT+24)
    CP (HL)
    JR Z,.palette
    LD (HL),A
    LD HL,NAMES+32+27
    LD E,32+27
    LD B,2
    CALL .header
.palette:
    LD A,(PAGE)
    LD E,A
    LD D,0
    LD HL,$CB74
    ADD HL,DE
    LD A,(INPUT+28)
    CP (HL)
    JR Z,.igloo
    LD (HL),A
    LD HL,NAMES+32+30
    LD E,32+30
    LD B,1
    CALL .header
.igloo:
    LD A,(PAGE)
    LD E,A
    LD D,0
    LD HL,$CB76
    ADD HL,DE
    LD A,(INPUT+29)
    CP (HL)
    RET Z
    LD (HL),A
    CALL stage_igloo
    LD A,(PAGE)
    ADD A,A
    ADD A,A
    ADD A,$58
    LD D,A
    LD E,3*32+22
    LD HL,NAMES+3*32+22
    LD A,4
    LD (ROWCOUNT),A
.row:
    LD B,8
    CALL vdp_write
    LD A,E
    ADD A,32
    LD E,A
    LD BC,24
    ADD HL,BC
    LD A,(ROWCOUNT)
    DEC A
    LD (ROWCOUNT),A
    JR NZ,.row
    RET
.header:
    LD A,(PAGE)
    ADD A,A
    ADD A,A
    ADD A,$58
    LD D,A
    JP vdp_write
