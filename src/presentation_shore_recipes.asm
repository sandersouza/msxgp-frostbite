; Standing left-shore P0 recipes. Normal/general preparation remains fallback.
    INCLUDE "symbols.inc"
    ORG $EFD1
ak_entry:
    LD A,2
    CALL t_mapper
    JP ak_try
ak_copy:
    CALL t_mapper
    LDIR
    LD A,2
    JP t_mapper
ak_ram_end:
    ASSERT $ <= $F000

    ORG $BA91
ak_try:
    LD A,($F06B)
    LD B,A
    LD A,($F070)
    OR B
    JP NZ,ak_fallback
    LD A,($F064)
    CP 27
    JP NZ,ak_fallback
    LD A,($F066)
    CP 24
    JR C,.recipe_x
    CP 84
    JP C,ak_fallback
    CP 153
    JP NC,ak_fallback
    AND 1
    ADD A,22
.recipe_x:
    LD (p_p_segment),A
    LD A,(p_w_coarse)
    CP 2
    JP NC,ak_fallback
    LD A,($F06E)
    CP 6
    JP NC,ak_fallback
    ; Directory: ((6*X+pose)*4+2*reflection+coarse)*2.
    LD C,A
    LD A,(p_p_segment)
    LD B,A
    ADD A,A
    ADD A,B
    ADD A,A
    ADD A,C
    LD L,A
    LD H,0
    DUP 3
    ADD HL,HL
    EDUP
    LD A,($F06C)
    AND 8
    RRCA
    LD B,A
    LD A,(p_w_coarse)
    ADD A,A
    OR B
    LD E,A
    LD D,0
    ADD HL,DE
    LD DE,$B800
    ADD HL,DE
    LD DE,p_p_planes
    LD BC,2
    LD A,AK_DIRECTORY_BANK
    CALL ak_copy
    LD A,(p_p_planes)
    LD B,A
    DUP 7
    SRL A
    EDUP
    ADD A,AK_RECORD_BANK
    PUSH AF
    LD A,B
    DUP 4
    RRCA
    EDUP
    AND 7
    ADD A,$B8
    LD H,A
    LD A,B
    AND 15
    DUP 4
    RLCA
    EDUP
    LD L,A
    LD DE,p_p_planes
    LD BC,16
    POP AF
    CALL ak_copy
    LD A,(p_p_planes)
    OR A
    JP Z,ak_fallback
    LD (p_p_count),A
    LD A,($F064)
    LD B,A
    LD A,(p_w_coarse)
    ADD A,B
    LD B,A
    LD A,(p_p_planes+1)
    ADD A,B
    LD (p_p_cut),A
    LD A,($F066)
    LD L,A
    LD H,0
    LD E,L
    LD D,H
    ADD HL,HL
    ADD HL,DE
    SRL H
    RR L
    LD DE,8
    ADD HL,DE
    LD (p_s_x),HL
    LD HL,p_p_planes+2
    LD (p_p_planeaddr),HL
    XOR A
    LD (p_p_plane),A
    LD A,1
    LD (p_s_upload),A
.entry:
    LD HL,(p_p_planeaddr)
    LD B,(HL)
    INC HL
    LD A,($F064)
    ADD A,B
    LD B,A
    LD A,(p_w_coarse)
    ADD A,B
    LD (p_s_y),A
    LD A,(HL)
    LD (p_s_color),A
    INC HL
    LD A,(HL)
    INC HL
    LD (p_p_planeaddr),HL
    LD B,A
    DUP 6
    SRL A
    EDUP
    ADD A,AK_PATTERN_BANK
    PUSH AF
    LD A,B
    DUP 3
    RRCA
    EDUP
    AND 7
    ADD A,$B8
    LD H,A
    LD A,B
    AND 7
    DUP 5
    RLCA
    EDUP
    LD L,A
    LD DE,p_s_pattern
    LD BC,32
    POP AF
    CALL ak_copy
    CALL p_sprite_emit
    LD HL,p_p_plane
    INC (HL)
    LD A,(p_p_count)
    CP (HL)
    JP NZ,.entry
    JP p_player_cache_store
ak_fallback:
    LD A,($F06B)
    JP x_try+3
ak_body_end:
    ASSERT $ <= $BC53
