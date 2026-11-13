; Certified immutable white/delta8 atlas; exact v19 dynamic fallback.
    INCLUDE "symbols.inc"
    ORG $F5B8
ah_boot_bridge:
    CALL $4A7B
    LD A,65
    CALL t_mapper
    CALL ah_boot
    LD A,1
    JP t_mapper
ah_runtime_bridge:
    LD A,65
    CALL t_mapper
    JP ah_floe
ah_bridges_end:
    ASSERT $ <= $F5D2
    DS $F5D2-$,0
ah_bridges_padded_end:

    ORG $B800
ah_boot:
    ; Original static initialization is complete; display/IRQ not started.
    LD HL,ah_patterns
    LD DE,$4000+1*$800+144*8
    LD B,128
    CALL vdp_write
    LD DE,$4000+1*$800+204*8
    LD B,0
    CALL vdp_write
    LD DE,$4000+1*$800+236*8
    LD B,112
    CALL vdp_write
    LD A,$F4
    LD DE,$6000+1*$800+144*8
    LD B,128
    CALL t_fill
    LD A,$F4
    LD DE,$6000+1*$800+204*8
    LD B,0
    CALL t_fill
    LD A,$F4
    LD DE,$6000+1*$800+236*8
    LD B,112
    CALL t_fill
    LD HL,ah_patterns
    LD DE,$4000+2*$800+144*8
    LD B,128
    CALL vdp_write
    LD DE,$4000+2*$800+204*8
    LD B,0
    CALL vdp_write
    LD DE,$4000+2*$800+236*8
    LD B,112
    CALL vdp_write
    LD A,$F4
    LD DE,$6000+2*$800+144*8
    LD B,128
    CALL t_fill
    LD A,$F4
    LD DE,$6000+2*$800+204*8
    LD B,0
    CALL t_fill
    LD A,$F4
    LD DE,$6000+2*$800+236*8
    LD B,112
    CALL t_fill
    RET
ah_floe:
    LD A,(p_w_row)
    ADD A,$2B
    LD L,A
    LD H,$F0
    LD L,(HL)
    LD H,$61
    LD A,(HL)
    CP 15
    JR NZ,.fallback
    LD A,(p_tl_delta_index)
    CP 1
    JR NZ,.fallback
    LD A,(p_w_row)
    LD L,A
    LD H,0
    LD DE,aa_y
    ADD HL,DE
    LD A,(HL)
    LD (p_w_y),A
    DUP 3
    SRL A
    EDUP
    LD (p_w_top),A
    LD L,A
    LD H,$FC
    LD A,(HL)
    OR A
    RET Z
    LD A,(p_w_row)
    ADD A,$1F
    LD L,A
    LD H,$F0
    LD A,(p_w_plane)
    LD B,A
    LD A,(HL)
    SUB B
    CP 160
    JR C,.root
    CP 248
    JR C,.above
    ADD A,160
    JR .root
.above:
    SUB 160
.root:
    LD (p_tl_root),A
    AND 15
    LD L,A
    LD H,0
    DUP 5
    ADD HL,HL
    EDUP
    LD DE,ah_programs
    ADD HL,DE
    PUSH HL
    LD A,(p_w_top)
    LD L,A
    LD H,0
    DUP 5
    ADD HL,HL
    EDUP
    LD A,(PAGE)
    OR A
    LD DE,$C800
    JR Z,.page
    LD D,$CD
.page:
    ADD HL,DE
    EX DE,HL
    POP HL
    JP x_name_row
.fallback:
    LD A,(p_w_row)
    JP $F440
ah_patterns:
    INCBIN "atlas-patterns.bin"
ah_programs:
    INCBIN "atlas-programs.bin"
ah_end:
    ASSERT $ <= $C000
    DS $C000-$,$FF
ah_padded_end:
