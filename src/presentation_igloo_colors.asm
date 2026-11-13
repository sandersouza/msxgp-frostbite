; Scoped igloo publisher. Exact hit / certified CGT-only / original full path.
; No new RAM or VRAM; entry saves the original mapper on the existing stack.
    INCLUDE "symbols.inc"
    ORG $6212
ad_entry:
    LD A,(t_bank)
    PUSH AF
    LD A,119
    CALL t_mapper
    JP ad_main
ad_hit:
    POP AF
    CALL t_mapper
    JP ad_original_publish
ad_publish:
    POP AF
    LD A,1                    ;the original successful constructor leaves bank1
    CALL t_mapper
    JP ad_original_publish
ad_fallback:
    POP AF
    CALL t_mapper
    JP p_fast_put
ad_resident_end:
    ASSERT $ <= $6249

    ORG $B800
ad_main:
    LD A,(pf_key+5)
    CP 5
    JP NZ,ad_fallback
    LD A,(p_fx_force)
    CP 255
    JP NZ,ad_fallback
    LD A,(p_w_top)
    SUB 3
    CP 3
    JP NC,ad_fallback
    LD B,A
    ADD A,A
    ADD A,B
    ADD A,A
    LD B,A
    LD A,(p_w_col)
    SUB 22
    CP 6
    JP NC,ad_fallback
    ADD A,B
    ADD A,38
    LD B,A
    LD A,(PAGE)
    CP 2
    JP NC,ad_fallback
    LD C,A
    ADD A,A
    ADD A,C
    LD C,A
    LD A,(p_w_cachegroup)
    CP C
    JP NZ,ad_fallback
    LD A,(PAGE)
    RRCA
    RRCA
    OR B
    LD (p_w_tile),A
    XOR A
    LD (p_fx_bank),A
    CALL p_fixed_key_address
    LD (p_fx_meta),HL
    LD DE,pf_key
    LD B,6
.compare:
    LD A,(DE)
    CP (HL)
    JR NZ,.different
    INC DE
    INC HL
    DJNZ .compare
    JP ad_hit
.different:
    LD IX,(p_fx_meta)
    LD A,(IX+5)
    CP 5
    JP NZ,ad_fallback
    LD A,(pf_key)
    CP (IX)
    JP NZ,ad_fallback
    LD A,(pf_key+1)
    CP (IX+1)
    JP NZ,ad_fallback
    LD A,(pf_key+3)
    CP 14
    JP NZ,ad_fallback
    LD A,(IX+3)
    CP 14
    JP NZ,ad_fallback
    LD A,(pf_key+4)
    OR (IX+4)
    JP NZ,ad_fallback
    LD A,(IX+2)
    SUB 128
    CP 27
    JP NC,ad_fallback
    LD E,A
    LD D,0
    LD HL,ad_flags
    ADD HL,DE
    LD A,(HL)
    OR A
    JP Z,ad_fallback
    LD A,(pf_key+2)
    SUB 128
    CP 27
    JP NC,ad_fallback
    LD C,A
    LD E,A
    LD HL,ad_flags
    ADD HL,DE
    LD A,(HL)
    OR A
    JP Z,ad_fallback
    LD L,C
    LD H,0
    DUP 5
    ADD HL,HL
    EDUP
    LD DE,ad_colors
    ADD HL,DE
    LD A,(pf_key)
    OR A
    JR Z,.lower
    LD DE,8
    ADD HL,DE
.lower:
    LD A,(pf_key+1)
    OR A
    JR Z,.address
    LD DE,16
    ADD HL,DE
.address:
    PUSH HL
    LD A,(p_w_tile)
    LD L,A
    LD H,0
    DUP 3
    ADD HL,HL
    EDUP
    LD DE,$6000
    ADD HL,DE
    EX DE,HL
    POP HL
    LD (IX+5),255              ;new identity becomes valid after complete CGT
    LD B,8
    CALL vdp_write
    LD HL,pf_key
    LD DE,(p_fx_meta)
    LD BC,6
    LDIR
    XOR A
    LD (pt_error),A
    JP ad_publish
ad_code_end:
ad_flags:
    INCBIN "igloo-flags.bin"
ad_colors:
    INCBIN "igloo-colors.bin"
ad_end:
    ASSERT $ <= $C000
