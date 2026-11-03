; Resident typed tile constructors. Read-only six-byte key atCC90 and
; SCREEN2 bank A(0..2) -> complete16-byte tileC520, errorC53F.
; This component may change page2; it is not included in the game yet.
    INCLUDE "presentation_static.inc"
    INCLUDE "presentation_simple.inc"
pt_key EQU $CC90
pt_tile EQU $C520
pt_mask EQU $C530
pt_glyphs EQU $C538
pt_bank EQU $C53C
pt_kind EQU $C53D
pt_pair EQU $C53E
pt_error EQU $C53F

presentation_typed_construct:
    LD (pt_bank),A
    XOR A
    LD (pt_error),A
    LD A,(pt_bank)
    CP 3
    JP NC,pt_fail
    LD A,(pt_key+5)
    LD (pt_kind),A
    OR A
    JP Z,pt_mono
    CP 4
    JP C,pt_literal
    CP 5
    JP Z,pt_igloo
    CP 6
    JP Z,pt_footer
    CP 7
    JP Z,pt_union
    CP 8
    JP Z,pt_union
    IFDEF WITH_PRESENTATION_TEMPLATES
    CP 9
    JP Z,pt_template_floe
    ENDIF
    SUB 16
    CP 3
    IFDEF WITH_PRESENTATION_HEADER_FAST
    JP C,p_template_header_construct
    ELSE
    JP C,pt_header
    ENDIF
pt_fail:
    LD A,1
    LD (pt_error),A
    SCF
    RET

; Exact background identity is part of the key, not inferred from live RAM.
pt_background:
    CP 128
    JP C,pt_fail
    SUB 128
    LD L,A
    LD H,0
    ADD HL,HL
    ADD HL,HL
    ADD HL,HL
    EX DE,HL
    LD A,(pt_bank)
    ADD A,A
    ADD A,A
    LD L,A
    LD H,0
    LD BC,pt_background_roots
    ADD HL,BC
    PUSH HL
    POP IX
    LD L,(IX)
    LD H,(IX+1)
    ADD HL,DE
    PUSH HL
    LD L,(IX+2)
    LD H,(IX+3)
    ADD HL,DE
    PUSH HL
    LD A,1
    LD ($7000),A
    POP HL
    LD DE,pt_tile+8
    LD BC,8
    LDIR
    POP HL
    LD DE,pt_tile
    LD BC,8
    LDIR
    OR A
    RET
pt_background_roots:
    DW p_bg_patterns0_data,p_bg_colors0_data
    DW p_bg_patterns1_data,p_bg_colors1_data
    DW p_bg_patterns2_data,p_bg_colors2_data

pt_pattern:
    CALL presentation_geometry_pattern
    RET C
    LD HL,$CC80
    LD DE,pt_mask
    LD BC,8
    LDIR
    OR A
    RET
pt_mono:
    LD A,(pt_bank)
    LD L,A
    LD H,0
    LD DE,pt_water_ids
    ADD HL,DE
    LD A,(pt_key+2)
    CP (HL)
    JP Z,pt_water_mono
    LD DE,(pt_key)
    CALL pt_pattern
    RET C
    LD A,(pt_key+3)
    OR A
    CALL NZ,pt_clip
    LD A,(pt_key+2)
    CALL pt_background
    RET C
    LD A,(pt_key+4)
    JP pt_merge
pt_water_ids:
    DB pt_water_id0,pt_water_id1,pt_water_id2

    IFDEF WITH_PRESENTATION_TEMPLATES
pt_template_floe:
    LD A,(pt_bank)
    OR A
    JP Z,pt_fail            ;original floes belong only to SCREEN2 banks1/2
    LD L,A
    LD H,0
    LD DE,pt_water_ids
    ADD HL,DE
    LD A,(pt_key+2)
    CP (HL)
    JP NZ,pt_fail
    LD A,(pt_key+3)
    OR A
    JP NZ,pt_fail
    LD A,(pt_key+4)
    OR A
    JP Z,pt_fail
    CP 16
    JP NC,pt_fail
    LD DE,(pt_key)
    CALL p_template_floe_pattern
    JP C,pt_fail
    LD HL,$CC80
    LD DE,pt_tile
    LD BC,8
    LDIR
    LD A,(pt_key+4)
    DUP 4
    RLCA
    EDUP
    OR 4
    LD HL,pt_tile+8
    DUP 8
    LD (HL),A
    INC HL
    EDUP
    XOR A
    RET
    ENDIF

; Solid-water pixels have one exact constant colour pair. Retain the literal
; geometry mask even on empty rows; decoded pixels equal the general merge.
pt_water_mono:
    LD DE,(pt_key)
    CALL presentation_geometry_pattern
    RET C
    LD HL,$CC80
    LD DE,pt_tile
    LD BC,8
    LDIR
    LD A,(pt_key+3)
    OR A
    JR Z,.colors
    LD HL,pt_tile
    LD B,8
.clip:
    LD A,(HL)
    AND 15
    LD (HL),A
    INC HL
    DJNZ .clip
.colors:
    LD A,(pt_key+4)
    DUP 4
    RLCA
    EDUP
    OR 4
    JP pt_fill_colors
pt_clip:
    LD HL,pt_mask
    LD B,8
.row:
    LD A,(HL)
    AND 15
    LD (HL),A
    INC HL
    DJNZ .row
    RET
pt_union:
    LD DE,(pt_key)
    CALL pt_pattern
    RET C
    LD DE,(pt_key+2)
    CALL presentation_geometry_pattern
    RET C
    LD HL,$CC80
    LD DE,pt_mask
    LD B,8
.row:
    LD A,(DE)
    OR (HL)
    LD (DE),A
    INC HL
    INC DE
    DJNZ .row
    LD A,(pt_kind)
    CP 8
    CALL Z,pt_clip
    LD HL,pt_mask
    LD DE,pt_tile
    LD BC,8
    LDIR
    LD A,(pt_key+4)
    JP pt_fill_colors
pt_fill_colors:
    LD HL,pt_tile+8
    LD B,8
.row:
    LD (HL),A
    INC HL
    DJNZ .row
    OR A
    RET

pt_literal:
    LD HL,pt_tile
    LD DE,pt_tile+1
    LD BC,7
    LD (HL),0
    LDIR
    LD A,$44
    CALL pt_fill_colors
    LD A,(pt_key+3)
    AND $F0
    OR 4
    LD D,A
    LD A,(pt_key+3)
    DUP 4
    RRCA
    EDUP
    AND $F0
    OR 4
    LD E,A
    LD A,(pt_kind)
    CP 1
    JR NZ,.two
    LD A,(pt_key)
    LD (pt_tile),A
    LD A,(pt_key+1)
    LD (pt_tile+7),A
    LD A,D
    LD (pt_tile+8),A
    LD A,E
    LD (pt_tile+15),A
    OR A
    RET
.two:
    CP 2
    JR NZ,.three
    LD A,(pt_key)
    LD (pt_tile),A
    LD A,(pt_key+1)
    LD (pt_tile+1),A
    LD A,(pt_key+2)
    LD (pt_tile+7),A
    LD A,E
    LD (pt_tile+8),A
    LD (pt_tile+9),A
    LD A,D
    LD (pt_tile+15),A
    OR A
    RET
.three:
    LD A,(pt_key)
    LD (pt_tile),A
    LD A,(pt_key+1)
    LD (pt_tile+6),A
    LD A,(pt_key+2)
    LD (pt_tile+7),A
    LD A,E
    LD (pt_tile+8),A
    LD A,D
    LD (pt_tile+14),A
    LD (pt_tile+15),A
    OR A
    RET

pt_igloo:
    IFDEF WITH_PRESENTATION_IGLOO_FAST
    ; Generated flags certify every row: PGT=FF, identical color nibbles,
    ; neither nibble14. Other backgrounds use the original general merge.
    LD A,(pt_key+2)
    SUB 128
    JP C,pt_fail
    LD E,A
    LD D,0
    LD A,(pt_bank)
    LD H,A
    LD L,0
    SRL H
    RR L
    ADD HL,DE
    LD DE,p_bg_igloo_uniform_flags
    ADD HL,DE
    LD A,(HL)
    OR A
    JR Z,.general
    LD A,(pt_key+2)
    CALL pt_background
    RET C
    LD HL,pt_tile+8
    LD DE,pt_tile
    LD A,(pt_key)
    OR A
    JR Z,.lower
    LD C,A
    DUP 4
    LD A,(HL)
    AND 15
    OR $E0
    LD (HL),A
    INC L
    LD A,C
    LD (DE),A
    INC E
    EDUP
.lower:
    LD HL,pt_tile+12
    LD DE,pt_tile+4
    LD A,(pt_key+1)
    OR A
    RET Z
    LD C,A
    DUP 4
    LD A,(HL)
    AND 15
    OR $E0
    LD (HL),A
    INC L
    LD A,C
    LD (DE),A
    INC E
    EDUP
    OR A
    RET
.general:
    ENDIF
    LD A,(pt_key)
    LD HL,pt_mask
    DUP 4
    LD (HL),A
    INC HL
    EDUP
    LD A,(pt_key+1)
    DUP 4
    LD (HL),A
    INC HL
    EDUP
    LD A,(pt_key+2)
    CALL pt_background
    RET C
    LD A,14
pt_merge:
    LD D,A
    LD IX,pt_mask
    LD IY,pt_tile
    LD B,8
.row:
    LD A,(IX)
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
    AND (IY)
    JR Z,.replace
    LD A,(IY)
    OR E
    CP 255
    JP NZ,pt_fail
    LD L,H
.replace:
    LD A,E
    LD (IY),A
    LD A,D
    DUP 4
    RLCA
    EDUP
    OR L
    LD (IY+8),A
    JR .next
.foreground:
    LD A,(IY)
    OR E
    LD (IY),A
    JR .next
.background:
    LD A,E
    CPL
    AND (IY)
    LD (IY),A
.next:
    INC IY
    DJNZ .row
    OR A
    RET

pt_footer:
    LD HL,(pt_key)
    LD DE,p_static_footer_tile_count
    OR A
    SBC HL,DE
    JP NC,pt_fail
    LD HL,(pt_key)
    DUP 4
    ADD HL,HL
    EDUP
    LD DE,p_static_footer_tiles_data
    ADD HL,DE
    LD A,p_static_footer_tiles_bank
    LD ($7000),A
    LD DE,pt_tile
    LD BC,16
    LDIR
    OR A
    RET

; Packed four6-bit glyph IDs. Static fragments hold only individual glyphs,
; five column phases and eight rows, rather than precomputed header frames.
pt_header:
    LD A,(pt_key)
    AND 63
    LD (pt_glyphs),A
    LD A,(pt_key)
    RLCA
    RLCA
    AND 3
    LD B,A
    LD A,(pt_key+1)
    ADD A,A
    ADD A,A
    AND 60
    OR B
    LD (pt_glyphs+1),A
    LD A,(pt_key+1)
    DUP 4
    RRCA
    EDUP
    AND 15
    LD B,A
    LD A,(pt_key+2)
    DUP 4
    RLCA
    EDUP
    AND 48
    OR B
    LD (pt_glyphs+2),A
    LD A,(pt_key+2)
    RRCA
    RRCA
    AND 63
    LD (pt_glyphs+3),A
    LD HL,pt_tile
    LD DE,pt_tile+1
    LD BC,7
    LD (HL),0
    LDIR
    LD A,(pt_key+4)
    AND 15
    LD B,A
    DUP 4
    RLCA
    EDUP
    OR B
    CALL pt_fill_colors
    LD A,p_static_header_bank
    LD ($7000),A
    LD A,(pt_kind)
    CP 18
    JR Z,.lower
    XOR A
    CALL pt_header_pair
    LD A,(pt_key+3)
    AND 15
    CALL pt_header_color
    LD A,(pt_kind)
    CP 16
    JR NZ,.shared_upper
    LD HL,pt_mask
    LD DE,pt_tile+3
    LD B,5
    JP pt_header_copy
.shared_upper:
    LD HL,pt_mask+5
    LD DE,pt_tile
    LD B,3
    CALL pt_header_copy
.lower:
    LD A,2
    CALL pt_header_pair
    LD A,(pt_key+3)
    DUP 4
    RRCA
    EDUP
    AND 15
    CALL pt_header_color
    LD A,(pt_kind)
    CP 18
    JR Z,.bottom
    LD HL,pt_mask
    LD DE,pt_tile+7
    LD B,1
    JP pt_header_copy
.bottom:
    LD HL,pt_mask+1
    LD DE,pt_tile
    LD B,7
    JP pt_header_copy
pt_header_color:
    DUP 4
    RLCA
    EDUP
    LD B,A
    LD A,(pt_key+4)
    AND 15
    OR B
    LD C,A
    RET
pt_header_copy:
    LD A,(HL)
    LD (DE),A
    INC HL
    LD A,E
    ADD A,8
    LD E,A
    LD A,C
    LD (DE),A
    LD A,E
    SUB 7
    LD E,A
    DJNZ pt_header_copy
    OR A
    RET
pt_header_pair:
    LD (pt_pair),A
    LD A,(pt_key+4)
    DUP 4
    RRCA
    EDUP
    AND 15
    CP 5
    JP NC,pt_fail
    ADD A,A
    LD E,A
    LD D,0
    LD HL,pt_header_parts
    ADD HL,DE
    LD A,(HL)
    INC HL
    LD C,(HL)
    PUSH BC
    CALL pt_header_fragment
    LD DE,pt_mask
    LD BC,8
    LDIR
    POP BC
    LD A,C
    CP 255
    RET Z
    LD HL,pt_pair
    INC (HL)
    CALL pt_header_fragment
    LD DE,pt_mask
    LD B,8
.row:
    LD A,(DE)
    OR (HL)
    LD (DE),A
    INC HL
    INC DE
    DJNZ .row
    RET
pt_header_fragment:
    ADD A,A
    ADD A,A
    ADD A,A
    LD C,A
    LD A,(pt_pair)
    ADD A,pt_glyphs&255
    LD L,A
    LD H,pt_glyphs/256
    LD A,(HL)
    CP 34
    JP NC,pt_fail
    LD L,A
    LD H,0
    LD E,L
    LD D,H
    ADD HL,HL
    ADD HL,HL
    ADD HL,DE
    DUP 3
    ADD HL,HL
    EDUP
    LD E,C
    ADD HL,DE
    LD DE,p_static_header_data
    ADD HL,DE
    RET
pt_header_parts:
    DB 0,255,1,2,3,255,4,0,4,255
    IFDEF WITH_PRESENTATION_HEADER_FAST
    INCLUDE "presentation_header.asm"
    IFDEF WITH_PRESENTATION_HEADER_BATCH
    INCLUDE "presentation_header_batch.asm"
    ENDIF
    ENDIF
