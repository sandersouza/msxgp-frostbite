; Bank2 presentation shader. Only resident RAM/VDP helpers may be called;
; changing the page2 mapper before return would unmap the active instructions.
p_s_count EQU $C250
p_s_sat EQU $C251
p_s_logo_top EQU $C253
p_s_phase EQU $C254
p_s_x EQU $C255
p_s_color EQU $C257
p_s_y EQU $C258
p_s_column EQU $C259
p_s_pattern EQU $C500
    IFDEF WITH_PRESENTATION_FAST
p_s_upload EQU $C29B
p_s_static_start EQU $C29C
p_s_door EQU $C29D
p_s_reflect EQU $C29E
    IFDEF WITH_PRESENTATION_TEMPLATES
p_s_pattern_id EQU $C29F
    ENDIF
    ENDIF

presentation_sprites_prepare:
    XOR A
    LD (p_s_count),A
    LD HL,SAT
    LD (p_s_sat),HL
    LD A,($C03F)
    BIT 7,A
    JP NZ,p_s_finish
    LD A,(p_h_footer_phase)
    LD (p_s_phase),A
    LD B,A
    LD A,(p_w_coarse)
    ADD A,B
    ADD A,181
    LD (p_s_logo_top),A
    IFDEF WITH_PRESENTATION_FAST
    LD A,1
    LD (p_s_upload),A         ;P0 always owns its own pattern upload decision
    IFDEF WITH_PRESENTATION_TEMPLATES
    LD A,255
    LD (p_s_static_start),A   ;P0 pattern IDs come from the selected cache way
    ENDIF
    ENDIF
    CALL p_player_prepare
    IFDEF WITH_PRESENTATION_FAST
    CALL p_static_lookup
    ENDIF
    ; The shared HMOVE mask uses one immutable pattern at3C00.
    LD HL,(p_s_sat)
    LD D,63
    LD B,7
.black:
    LD (HL),D
    INC HL
    LD (HL),16
    INC HL
    IFDEF WITH_PRESENTATION_TEMPLATES
    LD (HL),252              ;immutable mask at3FE0, outside every cache way
    ELSE
    LD (HL),128
    ENDIF
    INC HL
    LD (HL),1
    INC HL
    LD A,D
    ADD A,16
    LD D,A
    DJNZ .black
    LD (p_s_sat),HL
    LD A,($C04D)
    CP 15
    JR NZ,.logo
    IFDEF WITH_PRESENTATION_FAST
    LD A,(p_s_upload)
    OR A
    JR Z,.door_ready
    ENDIF
    LD A,($C06C)
    AND 16
    ADD A,A
    LD E,A
    LD D,0
    LD HL,p_sprite_door_data
    ADD HL,DE
    LD DE,p_s_pattern
    LD BC,32
    LDIR
.door_ready:
    LD HL,192
    LD (p_s_x),HL
    LD A,32
    LD (p_s_y),A
    LD A,(p_bg_theme)
    AND 1
    LD A,0
    JR Z,.door_color
    LD A,($C001)
    LD B,A
    LD A,($C002)
    XOR B
    AND 8
    LD A,0
    JR NZ,.door_color
    LD A,56
.door_color:
    CALL p_sprite_color
    CALL p_sprite_emit
.logo:
    XOR A
    LD (p_s_column),A
.part:
    IFDEF WITH_PRESENTATION_FAST
    LD A,(p_s_upload)
    OR A
    JR Z,.part_ready
    ENDIF
    CALL p_sprite_clear
    LD A,(p_s_column)
    LD L,A
    LD H,0
    DUP 4
    ADD HL,HL
    EDUP
    LD DE,p_sprite_logo_data
    ADD HL,DE
    LD IX,p_s_pattern
    LD A,(p_s_phase)
    LD B,A
    LD A,8
    SUB B
    LD B,A
.row:
    LD A,(HL)
    LD (IX),A
    INC HL
    LD A,(HL)
    LD (IX+16),A
    INC HL
    INC IX
    DJNZ .row
.part_ready:
    LD A,(p_s_column)
    DUP 4
    ADD A,A
    EDUP
    ADD A,53
    LD L,A
    LD H,0
    LD (p_s_x),HL
    LD A,(p_s_logo_top)
    LD (p_s_y),A
    LD A,12
    CALL p_sprite_color
    CALL p_sprite_emit
    LD HL,p_s_column
    INC (HL)
    LD A,(HL)
    CP 4
    JR NZ,.part
    IFDEF WITH_PRESENTATION_FAST
    CALL p_static_store
    ENDIF
p_s_finish:
    LD HL,(p_s_sat)
    LD (HL),208
    LD A,L
    INC A
    LD (p_sat_bytes),A
    RET

    IFDEF WITH_PRESENTATION_FAST
; The same page retains door/logo patterns iff P0's slot count and these
; exact shape selectors are unchanged. Positions/colours remain live SAT data.
; Bytes22..26 are independent of the P0 cache's valid byte and key.
p_static_lookup:
    LD A,(p_s_count)
    LD (p_s_static_start),A
    XOR A
    LD (p_s_reflect),A
    LD B,A
    LD A,($C04D)
    CP 15
    JR NZ,.door
    INC B
    LD A,($C06C)
    AND 16
    LD (p_s_reflect),A
.door:
    LD A,B
    LD (p_s_door),A
    IFDEF WITH_PRESENTATION_TEMPLATES
    LD IX,$C380
    LD A,(PAGE)
    OR A
    JR Z,.metadata
    LD IX,$C3A0
.metadata:
    ELSE
    LD IX,(p_pc_pointer)
    ENDIF
    LD A,(IX+22)
    CP 1
    JR NZ,.miss
    IFNDEF WITH_PRESENTATION_TEMPLATES
    LD A,(p_s_static_start)
    CP (IX+23)
    JR NZ,.miss
    ENDIF                   ;template static slots are independent of P0 count
    LD A,(p_s_door)
    CP (IX+24)
    JR NZ,.miss
    LD A,(p_s_reflect)
    CP (IX+25)
    JR NZ,.miss
    LD A,(p_s_phase)
    CP (IX+26)
    JR NZ,.miss
    XOR A
    LD (p_s_upload),A
    RET
.miss:
    LD (IX+22),0
    RET

p_static_store:
    LD A,(p_w_fault)
    OR A
    RET NZ
    IFDEF WITH_PRESENTATION_TEMPLATES
    LD IX,$C380
    LD A,(PAGE)
    OR A
    JR Z,.metadata
    LD IX,$C3A0
.metadata:
    ELSE
    LD IX,(p_pc_pointer)
    ENDIF
    LD A,(p_s_static_start)
    LD (IX+23),A
    LD A,(p_s_door)
    LD (IX+24),A
    LD A,(p_s_reflect)
    LD (IX+25),A
    LD A,(p_s_phase)
    LD (IX+26),A
    LD (IX+22),1             ;publish only after every pattern was uploaded
    RET
    ENDIF

p_sprite_color:
    LD L,A
    LD H,p_sprite_colors_data/256
    LD A,(HL)
    LD (p_s_color),A
    RET
p_sprite_clear:
    LD HL,p_s_pattern
    LD DE,p_s_pattern+1
    LD BC,31
    LD (HL),0
    LDIR
    RET
p_sprite_emit:
    LD A,(p_s_count)
    CP 16
    JP NC,p_world_fail
    LD B,A
    LD HL,(p_s_sat)
    LD A,(p_s_y)
    DEC A
    LD (HL),A
    INC HL
    LD A,(p_s_x+1)
    OR A
    LD A,(p_s_x)
    JR Z,.positive
    ADD A,32
.positive:
    LD (HL),A
    INC HL
    IFDEF WITH_PRESENTATION_TEMPLATES
    LD A,(p_s_static_start)
    CP 255
    JR NZ,.static_id
    LD A,B
    ADD A,A
    ADD A,A
    LD C,A
    LD A,(p_pc_patternbase)
    ADD A,C
    JR .pattern_id
.static_id:
    LD C,A
    LD A,B
    SUB C
    ADD A,48
    LD C,A
    LD A,(PAGE)
    LD D,A
    ADD A,A
    ADD A,A
    ADD A,D
    ADD A,C
    ADD A,A
    ADD A,A
.pattern_id:
    LD (p_s_pattern_id),A
    ELSE
    LD A,B
    ADD A,A
    ADD A,A
    LD C,A
    LD A,(PAGE)
    DUP 6
    ADD A,A
    EDUP
    OR C
    ENDIF
    LD (HL),A
    INC HL
    LD A,(p_s_x+1)
    OR A
    LD A,(p_s_color)
    JR Z,.color
    OR 128
.color:
    LD (HL),A
    INC HL
    LD (p_s_sat),HL
    IFDEF WITH_PRESENTATION_FAST
    LD A,(p_s_upload)
    OR A
    JR Z,.uploaded
    ENDIF
    IFDEF WITH_PRESENTATION_TEMPLATES
    LD A,(p_s_pattern_id)
    LD L,A
    LD H,0
    DUP 3
    ADD HL,HL
    EDUP
    LD DE,$7800
    ADD HL,DE
    EX DE,HL
    ELSE
    LD L,B
    LD H,0
    DUP 5
    ADD HL,HL
    EDUP
    LD A,(PAGE)
    ADD A,A
    ADD A,$78
    ADD A,H
    LD H,A
    EX DE,HL
    ENDIF
    LD HL,p_s_pattern
    LD B,32
    CALL vdp_write
.uploaded:
    LD HL,p_s_count
    INC (HL)
    RET

p_p_count EQU $C260
p_p_top EQU $C261
p_p_bottom EQU $C262
p_p_virtual EQU $C263
p_p_index EQU $C264
p_p_pattern EQU $C265
p_p_oldpattern EQU $C266
p_p_color EQU $C267
p_p_oldcolor EQU $C268
p_p_patternbase EQU $C269
p_p_colorbase EQU $C26B
p_p_cross EQU $C26D
p_p_nextcolor EQU $C26E
p_p_tail EQU $C26F
p_p_prefix EQU $C270
p_p_target EQU $C271
p_p_unblank EQU $C272
p_p_dx EQU $C273
p_p_bit EQU $C274
p_p_x EQU $C275
p_p_pointcolor EQU $C276
p_p_cut EQU $C277
p_p_limit EQU $C278
p_p_side EQU $C279
p_p_plane EQU $C27A
p_p_segment EQU $C27B
p_p_bandtop EQU $C27C
p_p_row EQU $C27D
p_p_masks EQU $C280
p_p_bandcount EQU $C282
p_p_planeaddr EQU $C28C
p_p_segmask EQU $C28E
p_p_last EQU $C291
p_p_expansion_page EQU $C292
p_p_planes EQU $C480
p_p_colors EQU $C4E0
p_p_color_planes EQU $C4F0 ;16 exact palette-index -> plane-byte-offset entries

p_player_prepare:
    CALL p_player_cache_lookup
    RET NC
    LD HL,p_p_planes
    LD DE,p_p_planes+1
    LD BC,95
    LD (HL),0
    LDIR
    LD HL,p_p_color_planes
    LD DE,p_p_color_planes+1
    LD BC,15
    LD (HL),255
    LDIR
    XOR A
    LD (p_p_count),A
    LD (p_p_pattern),A
    LD (p_p_color),A
    LD (p_p_unblank),A
    DEC A
    LD (p_p_top),A
    LD A,($C06E)
    CP 6
    JP NC,p_world_fail
    LD E,A
    LD D,0
    LD HL,original_data+$AA
    ADD HL,DE
    LD B,(HL)
    LD A,($C06B)
    ADD A,B
    LD L,A
    LD H,original_data/256
    LD (p_p_patternbase),HL
    LD HL,original_data+$B0
    ADD HL,DE
    LD B,(HL)
    LD A,($C06B)
    ADD A,B
    LD B,A
    LD A,($C070)
    ADC A,B
    LD L,A
    LD H,original_data/256
    LD (p_p_colorbase),HL
    ; Fully visible body, left of every source colour-race threshold.
    ; The original19 table rows can be streamed directly; rare shoreline,
    ; tail-colour, wrapped and clipped vertical cases retain the general path.
    LD A,($C066)
    CP 84
    JR NC,.general
    LD A,($C064)
    CP 30
    IFDEF WITH_PRESENTATION_TEMPLATES
    JR NC,.ordinary
    CP 19
    JR C,.general
    LD A,($C066)
    CP 24
    JR C,.general
    CALL p_player_shore_stream
    JP .rows_done
    ELSE
    JR C,.general
    ENDIF
.ordinary:
    CP 134
    JR NC,.general
    CALL p_player_body_stream
    JP .rows_done
.general:
    ; The visible active interval is E4+28..E4+46. E4=0 or>=154
    ; cannot intersect virtual47..181, including modulo256 wrap. After the
    ; last active row, only consecutive original GPR-hold rows can survive.
    LD A,($C064)
    OR A
    RET Z
    CP 154
    RET NC
    ADD A,46
    CP 182
    JR C,.last
    LD A,181
.last:
    LD (p_p_last),A
    LD A,($C064)
    ADD A,28
    CP 47
    JR NC,.first
    LD A,47
.first:
    LD (p_p_virtual),A
.row:
    LD A,(p_p_pattern)
    LD (p_p_oldpattern),A
    LD A,(p_p_color)
    LD (p_p_oldcolor),A
    LD A,160
    LD (p_p_tail),A
    XOR A
    LD (p_p_cross),A
    LD A,(p_p_virtual)
    LD B,A
    LD A,($C064)
    ADD A,46
    SUB B
    LD (p_p_index),A
    CP 19
    JR NC,.inactive
    LD E,A
    LD HL,(p_p_patternbase)
    CALL p_player_read
    LD B,A
    LD A,($C06C)
    AND 8
    LD A,B
    JR Z,.pattern
    LD L,A
    LD H,p_sprite_reverse_data/256
    LD A,(HL)
.pattern:
    LD (p_p_pattern),A
    LD A,(p_p_index)
    LD E,A
    LD HL,(p_p_colorbase)
    CALL p_player_read
    LD (p_p_color),A
    LD A,(p_p_cross)
    ADD A,16
    LD (p_p_prefix),A
    LD A,(p_p_index)
    OR A
    JR Z,.points
    DEC A
    LD E,A
    LD HL,(p_p_colorbase)
    CALL p_player_read
    LD (p_p_nextcolor),A
    LD A,(p_p_virtual)
    SUB 47
    LD E,A
    LD D,0
    LD HL,p_sprite_tails_data
    ADD HL,DE
    LD A,(p_p_cross)
    ADD A,(HL)
    LD (p_p_tail),A
    JR .points
.inactive:
    LD A,(p_p_virtual)
    SUB 47
    LD E,A
    LD D,0
    LD HL,p_sprite_holds_data
    ADD HL,DE
    LD A,(HL)
    OR A
    JR NZ,.hold
    LD (p_p_pattern),A
.hold:
    LD A,(p_p_virtual)
    CP 56
    JR NZ,.points
    XOR A
    LD (p_p_color),A
.points:
    LD A,(p_p_virtual)
    SUB 7
    LD B,A
    LD A,(p_p_virtual)
    CP 57
    LD A,B
    JR C,.target
    LD B,A
    LD A,(p_w_coarse)
    ADD A,B
.target:
    LD (p_p_target),A
    CALL p_player_points
    LD A,(p_p_virtual)
    CP 56
    JR NZ,.next
    LD A,(p_w_coarse)
    OR A
    JR Z,.next
    LD (p_p_unblank),A
    LD A,50
    LD (p_p_target),A
    CALL p_player_points
    XOR A
    LD (p_p_unblank),A
.next:
    LD HL,p_p_virtual
    INC (HL)
    LD A,(HL)
    CP 182
    JR Z,.rows_done
    LD B,A
    LD A,(p_p_last)
    CP B
    JP NC,.row
    LD A,B
    SUB 47
    LD E,A
    LD D,0
    LD HL,p_sprite_holds_data
    ADD HL,DE
    LD A,(HL)
    OR A
    JP NZ,.row
.rows_done:
    LD A,(p_p_count)
    OR A
    RET Z
    LD A,(p_p_top)
    ADD A,16
    LD (p_p_limit),A
    LD A,(p_p_bottom)
    SUB 15
    LD (p_p_cut),A
.candidate:
    XOR A
    LD (p_p_side),A
    CALL p_player_bandtop
    CALL p_player_count_band
    IFDEF WITH_PRESENTATION_TEMPLATES
    LD (p_pc_total),A
    ENDIF
    CALL p_player_band_fits
    JR C,.advance
    LD A,1
    LD (p_p_side),A
    CALL p_player_bandtop
    CALL p_player_count_band
    IFDEF WITH_PRESENTATION_TEMPLATES
    LD B,A
    LD A,(p_pc_total)
    ADD A,B
    LD (p_pc_total),A
    LD A,B
    ENDIF
    CALL p_player_band_fits
    JP NC,p_player_emit_all
.advance:
    LD HL,p_p_cut
    INC (HL)
    LD A,(p_p_limit)
    CP (HL)
    JR NC,.candidate
    JP p_world_fail

; Exact ordinary body path. Reflection and source palette mapping remain
; live; post-body rows follow the original hold table until its first clear.
p_player_body_stream:
    LD DE,18
    LD HL,(p_p_patternbase)
    ADD HL,DE
    PUSH HL
    POP IX
    LD HL,(p_p_colorbase)
    ADD HL,DE
    PUSH HL
    POP IY
    LD A,($C064)
    ADD A,21
    LD B,A
    LD A,(p_w_coarse)
    ADD A,B
    LD (p_p_target),A
    LD B,19
.row:
    LD A,(IX)
    DEC IX
    LD C,A
    LD A,($C06C)
    AND 8
    LD A,C
    JR Z,.pattern
    LD L,A
    LD H,p_sprite_reverse_data/256
    LD A,(HL)
.pattern:
    LD C,A
    LD A,(p_p_clip)
    AND C
    LD (p_p_bit),A
    LD A,(IY)
    DEC IY
    LD (p_p_color),A
    PUSH BC
    CALL p_player_store_mapped
    POP BC
    LD HL,p_p_target
    INC (HL)
    DJNZ .row
    LD A,($C064)
    ADD A,47
    LD (p_p_virtual),A
.tail:
    LD A,(p_p_virtual)
    CP 182
    RET NC
    SUB 47
    LD E,A
    LD D,0
    LD HL,p_sprite_holds_data
    ADD HL,DE
    LD A,(HL)
    OR A
    RET Z
    LD A,(p_p_color)
    CALL p_player_store_mapped
    LD HL,p_p_target
    INC (HL)
    LD HL,p_p_virtual
    INC (HL)
    JR .tail

p_p_wholemask EQU $C273
p_p_clip EQU $C28F
p_p_zone EQU $C290
p_player_init_masks:
    ; Split only the wrap at source160; parity is unchanged by240targetpx.
    LD A,($C066)
    CP 153
    LD A,255
    JR C,.masks
    LD A,($C066)
    LD B,A
    LD A,160
    SUB B
    LD B,A
    XOR A
.main_mask:
    SCF
    RRA
    DJNZ .main_mask
.masks:
    LD (p_p_masks),A
    CPL
    LD (p_p_masks+1),A
    LD A,8
    CALL p_player_zone
    CPL
    LD (p_p_clip),A
    RET

; SourceX<cut as an exact8-bit mask. All source raster cutoffs are>=8;
; wrapping bits near160 are therefore always in the low-X zone.
p_player_zone:
    PUSH BC
    PUSH DE
    PUSH HL
    LD B,A
    LD A,($C066)
    CP 153
    JR NC,.wrap
    LD C,A
    LD A,B
    SUB C
    JR C,.zero
    CP 8
    JR NC,.full
    LD L,A
    LD H,0
    LD DE,p_player_zones
    ADD HL,DE
    LD A,(HL)
    JR .done
.wrap:
    LD A,(p_p_masks+1)
    JR .done
.zero:
    XOR A
    JR .done
.full:
    LD A,255
.done:
    POP HL
    POP DE
    POP BC
    RET

; Read source table at baseHL+indexE, retaining6502 page-cross color races.
p_player_read:
    LD A,L
    ADD A,E
    LD L,A
    JR NC,.read
    INC H
    LD A,(p_p_cross)
    ADD A,3
    LD (p_p_cross),A
.read:
    LD A,(HL)
    RET

p_player_points:
    LD A,(p_p_pattern)
    LD B,A
    LD A,(p_p_index)
    CP 19
    JR NC,.clip
    LD A,(p_p_virtual)
    CP 55
    JR NC,.clip
    LD A,(p_p_prefix)
    CALL p_player_zone
    LD C,A
    CPL
    AND B
    LD B,A
    LD A,(p_p_oldpattern)
    AND C
    OR B
    LD B,A
.clip:
    LD A,(p_p_unblank)
    OR A
    LD A,B
    JR NZ,.whole
    LD C,A
    LD A,(p_p_clip)
    AND C
.whole:
    OR A
    RET Z
    LD (p_p_wholemask),A
    LD A,(p_p_virtual)
    CP 57
    JR NZ,.tail
    LD A,(p_p_index)
    CP 19
    JR NC,.tail
    LD A,(p_p_prefix)
    CALL p_player_zone
    LD (p_p_zone),A
    LD B,A
    LD A,(p_p_wholemask)
    AND B
    LD (p_p_bit),A
    LD A,(p_p_oldcolor)
    CALL p_player_store_mapped
    LD A,(p_p_zone)
    CPL
    LD B,A
    LD A,(p_p_wholemask)
    AND B
    LD (p_p_bit),A
    LD A,(p_p_color)
    JP p_player_store_mapped
.tail:
    LD A,(p_p_tail)
    CP 160
    JR NC,.single
    CALL p_player_zone
    LD (p_p_zone),A
    LD B,A
    LD A,(p_p_wholemask)
    AND B
    LD (p_p_bit),A
    LD A,(p_p_color)
    CALL p_player_store_mapped
    LD A,(p_p_zone)
    CPL
    LD B,A
    LD A,(p_p_wholemask)
    AND B
    LD (p_p_bit),A
    LD A,(p_p_nextcolor)
    JP p_player_store_mapped
.single:
    LD A,(p_p_wholemask)
    LD (p_p_bit),A
    LD A,(p_p_color)
p_player_store_mapped:
    LD C,A
    LD A,(p_p_bit)
    OR A
    RET Z
    LD L,C
    LD H,p_sprite_colors_data/256
    LD A,(HL)
    JP p_player_store

p_player_store:
    LD C,A
    OR p_p_color_planes&255
    LD L,A
    LD H,p_p_color_planes/256
    LD A,(HL)
    CP 255
    JR NZ,.plane
    LD A,(p_p_count)
    CP 4
    JP NC,p_world_fail
    LD E,A
    LD D,0
    PUSH HL
    LD HL,p_p_colors
    ADD HL,DE
    LD (HL),C
    LD HL,p_p_count
    INC (HL)
    LD A,E
    ADD A,A
    ADD A,E
    DUP 3
    ADD A,A
    EDUP
    POP HL
    LD (HL),A
.plane:
    IFDEF WITH_PRESENTATION_TEMPLATES
    ; Four24-byte planes fit wholly within C480..C4DF. Keep the original
    ; byte offset; form its row address only after validating the row delta.
    ASSERT (p_p_planes&255)+4*24 <= 256
    LD E,A
    LD A,(p_p_top)
    CP 255
    JR NZ,.byte_origin
    LD A,(p_p_target)
    LD (p_p_top),A
.byte_origin:
    LD B,A
    LD A,(p_p_target)
    LD (p_p_bottom),A
    SUB B
    CP 24
    JP NC,p_world_fail
    ADD A,E
    ADD A,p_p_planes&255
    LD L,A
    LD H,p_p_planes/256
    LD A,(p_p_bit)
    OR (HL)
    LD (HL),A
    RET
    ELSE
    LD E,A
    LD D,0
    LD HL,p_p_planes
    ADD HL,DE
    PUSH HL
    LD A,(p_p_top)
    CP 255
    JR NZ,.origin
    LD A,(p_p_target)
    LD (p_p_top),A
.origin:
    LD A,(p_p_top)
    LD B,A
    LD A,(p_p_target)
    LD (p_p_bottom),A
    SUB B
    CP 24
    JR C,.valid_row
    POP HL
    JP p_world_fail
.valid_row:
    POP HL
    LD E,A
    LD D,0
    ADD HL,DE
    LD A,(p_p_bit)
    OR (HL)
    LD (HL),A
    RET
    ENDIF

p_player_bandtop:
    LD A,(p_p_side)
    OR A
    LD A,(p_p_cut)
    JR NZ,.ready
    SUB 16
.ready:
    LD (p_p_bandtop),A
    RET
p_player_select:
    LD A,(p_p_plane)
    LD E,A
    LD D,0
    LD L,E
    LD H,D
    ADD HL,HL
    ADD HL,DE
    DUP 3
    ADD HL,HL
    EDUP
    LD DE,p_p_planes
    ADD HL,DE
    LD (p_p_planeaddr),HL
    LD A,(p_p_segment)
    LD E,A
    LD D,0
    LD HL,p_p_masks
    ADD HL,DE
    LD A,(HL)
    LD (p_p_segmask),A
    RET

p_player_nonempty:
    LD A,(p_p_segmask)
    OR A
    RET Z
    LD E,A
    LD A,(p_p_top)
    LD D,A
    LD A,(p_p_bandtop)
    ADD A,16
    SUB D
    JR C,.empty
    JR Z,.empty
    CP 25
    JR C,.end
    LD A,24
.end:
    LD B,A
    LD A,(p_p_bandtop)
    SUB D
    JR NC,.start
    XOR A
.start:
    CP 24
    JR NC,.empty
    LD C,A
    LD A,B
    SUB C
    LD B,A
    JR Z,.empty
    LD HL,(p_p_planeaddr)
    LD D,0
    PUSH DE
    LD E,C
    ADD HL,DE
    POP DE
.row:
    LD A,(HL)
    AND E
    RET NZ
    INC HL
    DJNZ .row
.empty:
    XOR A
    RET

p_player_count_band:
    XOR A
    LD (p_p_bandcount),A
    LD (p_p_plane),A
.plane:
    XOR A
    LD (p_p_segment),A
.segment:
    CALL p_player_select
    CALL p_player_nonempty
    JR Z,.next_segment
    LD HL,p_p_bandcount
    INC (HL)
.next_segment:
    LD HL,p_p_segment
    INC (HL)
    LD A,(HL)
    CP 2
    JR NZ,.segment
    LD HL,p_p_plane
    INC (HL)
    LD A,(p_p_count)
    CP (HL)
    JR NZ,.plane
    LD A,(p_p_bandcount)
    RET
p_player_band_fits:
    OR A
    RET Z
    LD B,A
    LD A,(p_p_bandtop)
    ADD A,15
    LD C,A
    LD A,(p_s_logo_top)
    CP C
    JR C,.bad
    JR Z,.bad
    LD A,(p_p_bandtop)
    CP 176
    JR NC,.door
    LD A,C
    CP 64
    JR NC,.static
.door:
    LD A,($C04D)
    CP 15
    JR NZ,.count
    LD A,(p_p_bandtop)
    CP 48
    JR NC,.count
    LD A,C
    CP 32
    JR C,.count
.static:
    INC B
.count:
    LD A,4
    CP B
    RET
.bad:
    SCF
    RET

p_player_emit_all:
    IFDEF WITH_PRESENTATION_TEMPLATES
    LD A,(p_pc_total)
    CP 7
    JR C,.cached
    CALL p_player_variant_uncached
    JP C,p_world_fail
    XOR A
    LD (p_pc_eligible),A     ;a large uncached frame cannot publish a six-slot way
.cached:
    ENDIF
    XOR A
    LD (p_p_side),A
.band:
    CALL p_player_bandtop
    XOR A
    LD (p_p_plane),A
.plane:
    XOR A
    LD (p_p_segment),A
.segment:
    CALL p_player_select
    CALL p_player_nonempty
    JR Z,.next_segment
    CALL p_player_sprite_pattern
    LD A,($C066)
    LD L,A
    LD H,0
    LD D,H
    LD E,L
    ADD HL,HL
    ADD HL,DE
    SRL H
    RR L
    LD DE,8
    ADD HL,DE
    LD A,(p_p_segment)
    OR A
    JR Z,.x
    LD DE,240
    OR A
    SBC HL,DE
.x:
    LD (p_s_x),HL
    LD A,(p_p_bandtop)
    LD (p_s_y),A
    LD A,(p_p_plane)
    LD E,A
    LD D,0
    LD HL,p_p_colors
    ADD HL,DE
    LD A,(HL)
    LD (p_s_color),A
    CALL p_sprite_emit
.next_segment:
    LD HL,p_p_segment
    INC (HL)
    LD A,(HL)
    CP 2
    JR NZ,.segment
    LD HL,p_p_plane
    INC (HL)
    LD A,(p_p_count)
    CP (HL)
    JP NZ,.plane
    LD HL,p_p_side
    INC (HL)
    LD A,(HL)
    CP 2
    JP NZ,.band
    JP p_player_cache_store

p_player_sprite_pattern:
    CALL p_sprite_clear
    ; Intersect the 16-row output band with the 24-row source plane once.
    ; The old inner loop recomputed this same intersection for every row.
    LD A,($C066)
    AND 1
    ADD A,A
    ADD A,p_sprite_expansion_data/256
    LD (p_p_expansion_page),A
    LD A,(p_p_top)
    LD B,A
    LD A,(p_p_bandtop)
    SUB B
    JR C,.leading
    CP 24
    RET NC
    LD E,A
    LD D,0
    LD HL,(p_p_planeaddr)
    ADD HL,DE
    PUSH HL
    POP IX
    LD B,A
    LD A,24
    SUB B
    CP 16
    JR C,.count
    LD A,16
.count:
    LD B,A
    LD DE,p_s_pattern
    JR .mask
.leading:
    NEG
    CP 16
    RET NC
    LD E,A
    LD D,p_s_pattern/256
    LD B,A
    LD A,16
    SUB B
    LD B,A
    LD IX,(p_p_planeaddr)
.mask:
    LD A,(p_p_segmask)
    LD C,A
.row:
    LD A,(IX)
    INC IX
    AND C
    JR Z,.next
    LD L,A
    LD H,0
    ADD HL,HL
    LD A,(p_p_expansion_page)
    ADD A,H
    LD H,A
    LD A,(HL)
    LD (DE),A
    INC HL
    LD A,E
    ADD A,16
    LD E,A
    LD A,(HL)
    LD (DE),A
    LD A,E
    SUB 16
    LD E,A
.next:
    INC E
    DJNZ .row
    RET
p_player_zones:
    DB $00,$80,$C0,$E0,$F0,$F8,$FC,$FE,$FF

    IFDEF WITH_PRESENTATION_TEMPLATES
    INCLUDE "presentation_player_shore.asm"
    ENDIF
    INCLUDE "presentation_player_cache.asm"
    INCLUDE "presentation_sprite_data.inc"
