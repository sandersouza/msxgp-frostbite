; Per-generation ordinary-player templates. Firstn SPT slots remain owned
; byP0 until that generation is rebuilt. Every miss invalidates ownership;
; static door/logo patterns are appended after the retained P0 slots.
p_pc_eligible EQU $C293
p_pc_pointer EQU $C294
p_pc_cut EQU $C296
p_pc_key EQU $C4E4

p_player_cache_lookup:
    CALL p_player_init_masks
    LD A,(PAGE)
    DUP 5
    ADD A,A
    EDUP
    ADD A,$80
    LD L,A
    LD H,$C3
    LD (p_pc_pointer),HL
    PUSH HL
    POP IX
    XOR A
    LD (p_pc_eligible),A
    LD A,($C066)
    CP 84
    JP NC,.miss
    LD A,($C064)
    IFDEF WITH_PRESENTATION_FAST
    CP 19
    ELSE
    CP 30
    ENDIF
    JP C,.miss
    CP 134
    JP NC,.miss
    LD A,1
    LD (p_pc_eligible),A
    LD A,($C06E)
    LD (p_pc_key),A
    LD A,($C06B)
    LD (p_pc_key+1),A
    LD A,($C070)
    LD (p_pc_key+2),A
    LD A,($C06C)
    AND 8
    LD (p_pc_key+3),A
    LD A,($C066)
    AND 1
    IFDEF WITH_PRESENTATION_FAST
    LD B,A
    LD A,($C064)
    CP 30
    JR NC,.ordinary_key
    LD C,A
    LD A,30
    SUB C
    ADD A,A
    OR B
    LD B,A
    LD A,(p_w_coarse)
    DUP 6
    RLCA
    EDUP
    OR B
    LD (p_pc_key+4),A
    LD A,($C066)             ;absolute X retains source prefix/colour races
    JR .horizontal_key
.ordinary_key:
    LD A,B
    ENDIF
    LD (p_pc_key+4),A
    LD A,(p_p_clip)
.horizontal_key:
    LD (p_pc_key+5),A
    LD A,($C064)
    LD E,A
    LD D,0
    LD HL,p_sprite_holds_data
    ADD HL,DE
    LD A,135
    SUB E
    LD B,A
    LD C,0
.hold:
    LD A,(HL)
    OR A
    JR Z,.tail_ready
    INC C
    INC HL
    DJNZ .hold
.tail_ready:
    LD A,C
    LD (p_pc_key+6),A
    LD A,(IX)
    CP 1
    JP NZ,.miss
    LD HL,p_pc_key
    DUP 7,i
    LD A,(HL)
    CP (IX+1+i)
    JP NZ,.miss
    INC HL
    EDUP
    LD A,($C064)
    LD B,A
    LD A,(p_w_coarse)
    ADD A,B
    ADD A,(IX+9)
    LD (p_pc_cut),A
    ADD A,15
    LD B,A
    LD A,(p_s_logo_top)
    CP B
    JR C,.miss
    JR Z,.miss
    LD A,(IX+8)
    LD (p_s_count),A
    OR A
    JR Z,.miss
    CP 7
    JR NC,.miss
    LD B,A
    LD A,($C066)
    LD E,A
    ADD A,A
    ADD A,E
    SRL A
    ADD A,8
    LD C,A
    LD A,(PAGE)
    DUP 6
    ADD A,A
    EDUP
    LD D,A
    LD HL,(p_pc_pointer)
    LD DE,10
    ADD HL,DE
    LD A,(PAGE)
    DUP 6
    ADD A,A
    EDUP
    LD D,A
    LD IY,SAT
.entry:
    LD A,(HL)
    INC HL
    OR A
    LD A,(p_pc_cut)
    JR NZ,.lower
    SUB 16
.lower:
    DEC A
    LD (IY),A
    LD (IY+1),C
    LD (IY+2),D
    LD A,(HL)
    INC HL
    LD (IY+3),A
    INC IY
    INC IY
    INC IY
    INC IY
    LD A,D
    ADD A,4
    LD D,A
    DJNZ .entry
    LD (p_s_sat),IY
    OR A
    RET
.miss:
    LD (IX),0
    SCF
    RET

p_player_cache_store:
    LD A,(p_pc_eligible)
    OR A
    RET Z
    LD A,(p_s_count)
    OR A
    RET Z
    CP 7
    RET NC
    LD B,A
    LD IX,(p_pc_pointer)
    LD (IX+8),A
    LD A,($C064)
    LD C,A
    LD A,(p_w_coarse)
    ADD A,C
    LD C,A
    LD A,(p_p_cut)
    SUB C
    LD (IX+9),A
    LD HL,(p_pc_pointer)
    LD DE,10
    ADD HL,DE
    LD D,0
    LD E,0
    LD IY,SAT
.entry:
    LD A,(IY)
    INC A
    LD C,A
    LD A,(p_p_cut)
    CP C
    JR NZ,.upper
    INC E
    LD A,1
    JR .record
.upper:
    INC D
    XOR A
.record:
    LD (HL),A
    INC HL
    LD A,(IY+3)
    LD (HL),A
    INC HL
    INC IY
    INC IY
    INC IY
    INC IY
    DJNZ .entry
    ; A16-row P0band may encounter at most one door/HMOVE rectangle.
    ; Retain only templates with<=3dynamic entries on EACHband, ensuring
    ; every accepted translation remains within four FULL rectangles/line.
    LD A,D
    CP 4
    RET NC
    LD A,E
    CP 4
    RET NC
    LD HL,(p_pc_pointer)
    INC HL
    EX DE,HL
    LD HL,p_pc_key
    LD BC,7
    LDIR
    LD (IX),1              ; publish metadata only after all P0patterns exist
    RET
