; Standalone component, not yet linked into the accepted game.
; Inputs C780..C786: control0..9, relative sourceY(0 or45..77), relativeX0..159,
; pose0..5, shift0..18, reflection0/1, absolute floeX0..159.
; Bit7 geometry is proven only for playerX9..153; caller must enforce this.
; A returns the electrical byte. Clobbers AF/BC/DE/HL; preserves IX/IY/SP.
; No RAM writes except bounded stack; no mapper access. Tables supplied by build.
cf_control EQU $C780
cf_y EQU $C781
cf_dx EQU $C782
cf_pose EQU $C783
cf_shift EQU $C784
cf_reflection EQU $C785
cf_absolute_x EQU $C786

cf_contact:
    LD A,(cf_y)
    SUB 50
    JP C,.no_hit
    CP 25
    JP NC,.no_hit
    LD C,A                 ; bottom glyph row relative to the ice's first row
    LD A,(cf_control)
    LD L,A
    LD H,0
    ADD HL,HL
    ADD HL,HL
    ADD HL,HL
    ADD HL,HL
    ADD HL,HL              ; control*32
    LD D,H
    LD E,L
    ADD HL,HL
    ADD HL,HL
    ADD HL,DE              ; control*160
    LD A,(cf_dx)
    LD E,A
    LD D,0
    ADD HL,DE
    LD DE,cf_directory
    ADD HL,DE
    LD A,(HL)
    OR A
    JR Z,.no_hit
    LD L,A
    LD H,0
    LD E,A
    LD D,0
    ADD HL,HL
    ADD HL,HL
    ADD HL,HL
    OR A
    SBC HL,DE              ; footprint*7
    LD DE,cf_footprints
    ADD HL,DE
    EX DE,HL
    LD A,C
    LD B,7
    CP 19
    JR C,.bottom_clip
    SUB 18                 ; skip ice rows above the glyph's last stored row
    LD L,A
    LD H,0
    ADD HL,DE
    EX DE,HL
    NEG
    ADD A,7
    LD B,A
    LD A,18
    JR .glyph
.bottom_clip:
    CP 6
    JR NC,.glyph
    INC A
    LD B,A
    DEC A
.glyph:
    PUSH DE
    LD C,A
    LD A,(cf_pose)
    LD L,A
    LD H,0
    LD DE,cf_bases
    ADD HL,DE
    LD A,(HL)
    LD L,A
    LD A,(cf_shift)
    ADD A,L
    ADD A,C
    LD L,A
    LD A,(cf_reflection)
    AND 1
    ADD A,cf_glyphs/256     ; adjacent normal/reflected pages avoid loop overhead
    LD H,A
    POP DE
.rows:
    LD A,(DE)
    AND (HL)
    JR NZ,.hit
    INC DE
    DEC HL
    DJNZ .rows
.no_hit:
    LD C,7
    JR .shadow
.hit:
    LD C,135
.shadow:
    LD A,(cf_control)
    OR A
    JR Z,.shadow_on
    CP 4
    JR Z,.narrow_shadow
    CP 5
    JR NZ,.done
    LD B,31
    JR .exceptional_shadow
.narrow_shadow:
    LD B,30
.exceptional_shadow:
    LD A,(cf_y)
    SUB 50
    JR C,.outside_ice
    CP 19
    JR C,.done
.outside_ice:
    LD A,(cf_absolute_x)
    CP 94
    JR C,.done
    AND 31
    CP 30
    JR Z,.shadow_on
    CP B
    JR NZ,.done
.shadow_on:
    SET 6,C
.done:
    LD A,C
    RET
cf_end:

    ASSERT (cf_glyphs & 255) == 0
