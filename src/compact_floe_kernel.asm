; Standalone component, not yet linked into the accepted game.
; Inputs C780..C786: control0..9, relative sourceY(0 or45..77), relativeX0..159,
; pose0..5, shift0..18, reflection0/1, absolute floeX0..159.
; Bit7 geometry is proven only for playerX9..153; caller must enforce this.
; A returns the electrical byte. Clobbers AF/BC/DE/HL; preserves IX/IY/SP.
; No RAM writes except bounded stack; no mapper access. Tables supplied by build.
    IFNDEF CF_INPUT_ORIGIN
CF_INPUT_ORIGIN EQU $C780
    ENDIF
cf_control EQU CF_INPUT_ORIGIN
cf_y EQU CF_INPUT_ORIGIN+1
cf_dx EQU CF_INPUT_ORIGIN+2
cf_pose EQU CF_INPUT_ORIGIN+3
cf_shift EQU CF_INPUT_ORIGIN+4
cf_reflection EQU CF_INPUT_ORIGIN+5
cf_absolute_x EQU CF_INPUT_ORIGIN+6

    IFNDEF CF_ENEMY_ONLY
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
    ENDIF

    ASSERT (cf_glyphs & 255) == 0

    IFDEF CF_WITH_ENEMY
; Ordinary common-profile component, playerX25..151, one original copy.
; Same seven-byte input ABI, interpreted as: shape index0..32, Y(0 or36..61),
; signed-distance index(distance+7), P0 pose/shift/reflection, P1 reflection.
; Seven collision rows retain the source's early latch read; visual height is8.
cf_enemy_contact:
    LD A,(cf_y)
    SUB 36
    JP C,.direct_miss
    CP 25
    JP NC,.direct_miss
    PUSH IX
    PUSH AF
    LD A,(cf_dx)
    CP 7
    JR C,.right_shift
    SUB 7
    LD E,A
    LD D,0
    LD HL,cf_enemy_left_end
    JR .rotation_address
.right_shift:
    NEG
    ADD A,7
    LD E,A
    LD D,0
    LD HL,cf_enemy_right_end
.rotation_address:
    OR A
    SBC HL,DE              ; one-byte rotations; enter at the required count
    PUSH HL
    POP IX
    LD A,(cf_control)
    LD L,A
    LD H,0
    LD DE,cf_enemy_shapes
    ADD HL,DE
    LD A,(HL)
    ADD A,7
    LD L,A
    LD A,(cf_absolute_x)    ; P1 reflection in this entrypoint
    AND 1
    ADD A,cf_enemy_glyphs/256
    LD H,A
    EX DE,HL
    POP AF
    LD B,7
    CP 19
    JR C,.bottom_clip
    SUB 18
    EX DE,HL
    LD E,A
    LD D,0
    OR A
    SBC HL,DE              ; enemy source bytes run backwards through the rows
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
    ADD A,cf_glyphs/256
    LD H,A
    POP DE
    PUSH DE
    PUSH HL
    LD A,(cf_dx)
    LD E,A
    LD D,0
    LD HL,cf_enemy_clip_masks
    ADD HL,DE
    LD C,(HL)
    POP HL
    POP DE
.rows:
    LD A,(DE)
    CALL cf_enemy_rotate
    AND C                  ; remove rotated pixels that crossed the clip edge
    AND (HL)
    JR NZ,.hit
    DEC DE
    DEC HL
    DJNZ .rows
    LD A,7
    POP IX
    RET
.hit:
    LD A,135
    POP IX
    RET
.direct_miss:
    LD A,7
    RET

cf_enemy_rotate:
    JP (IX)
    DUP 7
    RLCA
    EDUP
cf_enemy_left_end:
    RET
    DUP 7
    RRCA
    EDUP
cf_enemy_right_end:
    RET
cf_enemy_end:
    ASSERT (cf_enemy_glyphs & 255) == 0
    ENDIF

    IFDEF CF_WITH_BEAR
; Shore common-X profile, playerX25..151. Inputs: mode0..5, Y(0 or12..46),
; signed-distance index(distance+7, range0..22), P0 pose/shift/reflection, zero.
; Footprints contain doubled/reflected source pixels; last two rows are blank.
cf_bear_contact:
    LD A,(cf_y)
    SUB 12
    JP C,.no_hit
    CP 35
    JP NC,.no_hit
    LD C,A
    LD A,(cf_control)
    LD L,A
    LD H,0
    LD E,A
    LD D,0
    ADD HL,HL
    ADD HL,HL
    ADD HL,HL              ; mode*8
    PUSH HL
    ADD HL,HL
    OR A
    SBC HL,DE              ; mode*15
    POP DE
    ADD HL,DE              ; mode*23
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
    ADD HL,HL
    ADD HL,DE              ; footprint*17
    LD DE,cf_footprints
    ADD HL,DE
    EX DE,HL
    LD A,C
    LD B,17
    CP 19
    JR C,.bottom_clip
    SUB 18
    LD L,A
    LD H,0
    ADD HL,DE
    EX DE,HL
    NEG
    ADD A,17
    LD B,A
    LD A,18
    JR .glyph
.bottom_clip:
    CP 16
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
    ADD A,cf_glyphs/256
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
    LD A,7
    RET
.hit:
    LD A,135
    RET
cf_bear_end:
    ENDIF
