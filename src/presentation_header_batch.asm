; Private live-header work: upper/lower eight-row masks for ten columns.
; Keys remain authoritative for residency; complete tiles/IO remain unchanged.
p_th_masks EQU $E650

; pt_glyphs[4], IX=current three-byte column command, p_h_index0..9.
; Preserve IX/IY and all four glyph selectors for the existing key packer.
p_template_header_mask_column:
    LD A,(p_h_index)
    CP 10
    JP NC,pt_fail
    LD L,A
    LD H,0
    DUP 4
    ADD HL,HL
    EDUP
    LD DE,p_th_masks
    ADD HL,DE
    PUSH HL
    LD A,p_static_header_bank
    LD ($7000),A
    XOR A
    LD (pt_pair),A
    POP DE
    CALL p_template_header_mask_pair
    RET C
    LD A,2
    LD (pt_pair),A
    JP p_template_header_mask_pair

; DE=destination eight bytes, pt_pair=0/2, IX+2=fragment combination0..4.
; Return DE advanced8. Every first fragment and optional second is complete.
p_template_header_mask_pair:
    LD A,(IX+2)
    CP 5
    JP NC,pt_fail
    ADD A,A
    LD L,A
    LD H,0
    PUSH DE
    LD DE,pt_header_parts
    ADD HL,DE
    LD A,(HL)
    INC HL
    LD B,(HL)
    PUSH BC
    CALL pt_header_fragment
    POP BC
    POP DE
    RET C
    PUSH BC
    DUP 8
    LDI
    EDUP
    POP BC
    LD A,B
    CP 255
    JR Z,.done
    LD HL,pt_pair
    INC (HL)
    PUSH DE
    CALL pt_header_fragment
    POP DE
    RET C
    LD A,E
    SUB 8
    LD E,A
    JR NC,.or_rows
    DEC D
.or_rows:
    DUP 8
    LD A,(DE)
    OR (HL)
    LD (DE),A
    INC DE
    INC HL
    EDUP
.done:
    OR A
    RET

; Bounded live-header caller only: source-derived cached masks and current key
; have just been prepared together. Generic typed constructors stay independent.
p_template_header_live_construct:
    XOR A
    LD (pt_error),A
    LD (pt_bank),A
    LD A,(p_h_y)
    CP 3
    JP NC,pt_fail
    ADD A,16
    LD B,A
    LD A,(pt_key+5)
    CP B
    JP NZ,pt_fail
    LD (pt_kind),A
    LD A,(p_h_index)
    CP 10
    JP NC,pt_fail
    LD L,A
    LD H,0
    DUP 4
    ADD HL,HL
    EDUP
    LD DE,p_th_masks
    ADD HL,DE
    PUSH HL
    XOR A
    LD HL,pt_tile
    DUP 8
    LD (HL),A
    INC L
    EDUP
    POP HL
    LD A,(pt_kind)
    CP 16
    JR Z,.upper
    CP 18
    JR Z,.lower
    LD DE,5
    ADD HL,DE
    LD DE,pt_tile
    DUP 3
    LDI
    EDUP
    LD DE,pt_tile+7
    LDI
    JP p_template_header_construct.colours
.upper:
    LD DE,pt_tile+3
    DUP 5
    LDI
    EDUP
    JP p_template_header_construct.colours
.lower:
    LD DE,9
    ADD HL,DE
    LD DE,pt_tile
    DUP 7
    LDI
    EDUP
    JP p_template_header_construct.colours
