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
    CALL p_player_prepare
    ; The shared HMOVE mask uses one immutable pattern at3C00.
    LD HL,(p_s_sat)
    LD D,63
    LD B,7
.black:
    LD (HL),D
    INC HL
    LD (HL),16
    INC HL
    LD (HL),128
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
p_s_finish:
    LD HL,(p_s_sat)
    LD (HL),208
    LD A,L
    INC A
    LD (p_sat_bytes),A
    RET

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
    LD A,B
    ADD A,A
    ADD A,A
    LD C,A
    LD A,(PAGE)
    DUP 6
    ADD A,A
    EDUP
    OR C
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
    LD HL,p_s_pattern
    LD B,32
    CALL vdp_write
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
p_p_planes EQU $C480
p_p_colors EQU $C4E0

p_player_prepare:
    LD HL,p_p_planes
    LD DE,p_p_planes+1
    LD BC,95
    LD (HL),0
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
    LD A,47
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
    JP NZ,.row
    LD A,(p_p_count)
    OR A
    RET Z
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
    CALL p_player_band_fits
    JR C,.advance
    LD A,1
    LD (p_p_side),A
    CALL p_player_bandtop
    CALL p_player_count_band
    CALL p_player_band_fits
    JP NC,p_player_emit_all
.advance:
    LD HL,p_p_cut
    INC (HL)
    LD A,(p_p_limit)
    CP (HL)
    JR NC,.candidate
    JP p_world_fail

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
    LD A,(p_p_oldpattern)
    OR B
    RET Z
    XOR A
    LD (p_p_dx),A
.point:
    LD A,(p_p_dx)
    LD E,A
    LD D,0
    LD HL,p_player_bits
    ADD HL,DE
    LD A,(HL)
    LD (p_p_bit),A
    LD A,($C066)
    ADD A,E
    CALL normalize_x
    LD (p_p_x),A
    CP 8
    JR NC,.pattern
    LD A,(p_p_unblank)
    OR A
    JP Z,.next
.pattern:
    LD A,(p_p_pattern)
    LD B,A
    LD A,(p_p_index)
    CP 19
    JR NC,.selected
    LD A,(p_p_virtual)
    CP 55
    JR NC,.selected
    LD A,(p_p_prefix)
    LD C,A
    LD A,(p_p_x)
    CP C
    JR NC,.selected
    LD A,(p_p_oldpattern)
    LD B,A
.selected:
    LD A,(p_p_bit)
    AND B
    JP Z,.next
    LD A,(p_p_color)
    LD C,A
    LD A,(p_p_virtual)
    CP 57
    JR NZ,.tail
    LD A,(p_p_index)
    CP 19
    JR NC,.tail
    LD A,(p_p_prefix)
    LD B,A
    LD A,(p_p_x)
    CP B
    JR NC,.tail
    LD A,(p_p_oldcolor)
    LD C,A
.tail:
    LD A,(p_p_tail)
    LD B,A
    LD A,(p_p_x)
    CP B
    JR C,.color
    LD A,(p_p_nextcolor)
    LD C,A
.color:
    LD L,C
    LD H,p_sprite_colors_data/256
    LD A,(HL)
    LD (p_p_pointcolor),A
    CALL p_player_store
.next:
    LD HL,p_p_dx
    INC (HL)
    LD A,(HL)
    CP 8
    JP NZ,.point
    RET

p_player_store:
    LD C,A
    LD A,(p_p_count)
    LD B,A
    LD E,0
    LD HL,p_p_colors
    OR A
    JR Z,.new
.find:
    LD A,(HL)
    CP C
    JR Z,.plane
    INC HL
    INC E
    DJNZ .find
.new:
    LD A,E
    CP 4
    JP NC,p_world_fail
    LD (HL),C
    LD HL,p_p_count
    INC (HL)
.plane:
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
    JP NC,p_world_fail
    PUSH AF
    LD L,E
    LD H,0
    LD D,H
    ADD HL,HL
    ADD HL,DE
    DUP 3
    ADD HL,HL
    EDUP
    LD DE,p_p_planes
    ADD HL,DE
    POP AF
    LD E,A
    LD D,0
    ADD HL,DE
    LD A,(p_p_bit)
    OR (HL)
    LD (HL),A
    RET

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
    RET C
    RET Z
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
    RET

p_player_sprite_pattern:
    CALL p_sprite_clear
    XOR A
    LD (p_p_row),A
.row:
    LD A,(p_p_top)
    LD B,A
    LD A,(p_p_row)
    LD C,A
    LD A,(p_p_bandtop)
    ADD A,C
    SUB B
    JR C,.zero
    CP 24
    JR NC,.zero
    LD E,A
    LD D,0
    LD HL,(p_p_planeaddr)
    ADD HL,DE
    LD A,(p_p_segmask)
    AND (HL)
    JR .expand
.zero:
    XOR A
.expand:
    LD L,A
    LD H,0
    ADD HL,HL
    LD A,($C066)
    AND 1
    ADD A,A
    ADD A,p_sprite_expansion_data/256
    ADD A,H
    LD H,A
    LD A,(p_p_row)
    LD E,A
    LD D,p_s_pattern/256
    LD A,(HL)
    LD (DE),A
    INC HL
    LD A,E
    ADD A,16
    LD E,A
    LD A,(HL)
    LD (DE),A
    LD HL,p_p_row
    INC (HL)
    LD A,(HL)
    CP 16
    JR NZ,.row
    RET
p_player_bits:
    DB $80,$40,$20,$10,$08,$04,$02,$01

    INCLUDE "presentation_sprite_data.inc"
