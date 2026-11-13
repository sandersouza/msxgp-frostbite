; Signed P0 cache displacements; no mapper or memory allocation changes.
    INCLUDE "symbols.inc"
    ORG AO_CACHE_ENTRY
ao_cache_entry:
    LD A,(p_pc_cut)
    ADD A,(HL)
    INC HL
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
    DJNZ ao_cache_entry
    LD (p_s_sat),IY
    OR A
    RET
    ASSERT $ <= AO_CACHE_MISS
    DS AO_CACHE_MISS-$,0
ao_cache_miss:
    LD (IX),0
    SCF
    RET
    ASSERT $ = p_player_cache_store
ao_cache_store:
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
    LD A,($F064)
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
    LD DE,0
    LD IY,SAT
.entry:
    LD A,(IY)
    INC A
    LD C,A
    LD A,(p_p_cut)
    CP C
    JR NZ,.upper
    INC E
    XOR A                    ;signed lower displacement0
    JR .record
.upper:
    CALL ao_upper
    RET C
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
    LD (IX),1                ;publish only after all P0 patterns exist
    RET
    ASSERT $ <= p_player_variant_default
    DS p_player_variant_default-$,$FF
ao_cache_end:

    ORG AO_UPPER
ao_upper:
    INC D
    LD A,(p_p_cut)
    SUB C
    RET C                    ;startY>cut is not a nonpositive displacement
    NEG
    RET P                    ;reject byte-wrap outside signed8-bit range
    BIT 2,(IX+8)             ;total count has already been bounded1..6
    JR Z,.small
    CP $F0                   ;4..6 entries retain exact original0/-16 bands
    RET Z
    SCF
    RET
.small:
    OR A
    RET
ao_upper_end:
    ASSERT $ <= p_player_variant_uncached
    DS p_player_variant_uncached-$,$FF
ao_upper_padded_end:
