; Reclaimed obsolete header code. All foreign calls return through mapped RAM.
    INCLUDE "symbols.inc"
AN_RECORD EQU $C480
AN_TILE EQU $C500
AN_KEYS EQU $E8B9
    ORG w_header
an_early:
    LD A,($F04B)
    CP 3
    JP C,ai_entry
    RET
an_header:
    PUSH AF
    LD A,($F04B)
    CP 3
    JP C,an_original
    PUSH BC
    PUSH DE
    PUSH HL
    PUSH IX
    PUSH IY
    LD A,(p_w_coarse)
    PUSH AF
    LD A,(i_active)
    PUSH AF
    LD A,(t_bank)
    PUSH AF
    LD A,114
    CALL t_mapper
    JP an_body
an_return:
    POP AF
    CALL t_mapper
    POP AF
    LD (i_active),A
    POP AF
    LD (p_w_coarse),A
    POP IY
    POP IX
    POP HL
    POP DE
    POP BC
an_original:
    POP AF
    LD A,($F03F)
    JP AN_HUD_CONT
an_copy:
    CALL t_mapper
    LDIR
    LD A,114
    JP t_mapper
an_upload:
    CALL t_mapper
    CALL vdp_write
    LD A,114
    JP t_mapper
an_native:
    LD A,102
    CALL t_mapper
    CALL ai_body
    LD A,114
    JP t_mapper
an_ram_end:
    ASSERT $ <= w_selected
    DS w_selected-$,$FF
an_ram_padded_end:

    ORG $B800
an_body:
    LD A,($F03F)
    BIT 7,A
    JP NZ,an_return
    XOR A
    LD (i_active),A
    LD (pfw_geo_valid),A
    ; Recreate the original bear context from the coherent source snapshot.
    LD A,($F068)
    CP 150
    LD A,0
    ADC A,0
    XOR 1
    LD (p_w_coarse),A
    ADD A,51
    LD (p_w_y),A
    LD A,($F068)
    LD B,1
    CP 15
    JR NC,.x_offset
    LD B,6
.x_offset:
    ADD A,B
    CALL normalize_x
    LD (p_w_x),A
    LD C,A
    SRL A
    ADD A,C
    ADD A,8
    LD (p_w_base),A          ;target sprite X, not the source coordinate
    DUP 3
    SRL A
    EDUP
    LD (p_w_origin),A
    LD A,($F06F)
    ADD A,A
    LD B,A
    LD A,($F06C)
    AND 16
    DUP 4
    RRCA
    EDUP
    OR B
    LD (p_w_group),A
    LD A,(p_bg_theme)
    AND 1
    LD B,A
    LD A,($F04B)
    CP 3
    LD A,10
    JR C,.shore
    LD A,4
    DEC B
    JR NZ,.color
    LD A,12
    JR .color
.shore:
    DEC B
    JR NZ,.color
    LD A,2
.color:
    LD L,A
    LD H,$61                ;resident original world palette, no bank change
    LD A,(HL)
    LD (p_w_color),A
    LD A,2
    LD (p_w_family),A
    ; Original background has already filled all three original dirty rows.
    ; Missing rows require explicit restoration for a safe mode transition.
    CALL an_force_rows
    OR A
    JR Z,.restored
    LD A,6
    LD (p_w_top),A
.restore:
    CALL an_background
    PUSH BC
    PUSH DE
    CALL an_name
    POP DE
    POP BC
    LD (HL),128
    INC L
    LD (HL),E
    INC L
    LD (HL),D
    INC L
    LD A,C
    DUP 28
    LD (HL),A
    INC L
    EDUP
    LD (HL),128
    LD HL,p_w_top
    INC (HL)
    LD A,(HL)
    CP 9
    JR NZ,.restore
.restored:
    LD A,($F046)
    LD B,A
    LD A,($F067)
    OR B
    LD B,A
    LD A,($F071)
    OR B
    JP NZ,.native
    LD A,(p_bg_profile)
    CP 32
    JP Z,.native
    LD A,(p_w_group)
    CP 16
    JP NC,.native
    LD A,(p_w_x)
    CP 11
    JP C,.native
    CP 145
    JP NC,.native
    LD A,(p_w_color)
    CP 1
    JR Z,.palette_ok
    CP 15
    JP NZ,.native
.palette_ok:
    LD A,(p_sat_bytes)
    CP 1
    JP C,.native
    CP 118                  ;retain at most31 sprites plus the terminator
    JP NC,.native
    CALL an_admit
    JP NC,.native
    ; Original512-entry directory, copied at132:B800, still identifies96 grids.
    LD A,(p_w_group)
    LD L,A
    LD H,0
    DUP 6
    ADD HL,HL
    EDUP
    LD A,(p_w_x)
    AND 15
    ADD A,A
    LD B,A
    LD A,(p_w_coarse)
    OR B
    ADD A,A
    LD E,A
    LD D,0
    ADD HL,DE
    LD DE,$B800
    ADD HL,DE
    LD DE,AN_RECORD
    LD BC,2
    LD A,132
    CALL an_copy
    LD A,(AN_RECORD)
    CP 96
    JP NC,.native
    CP 93
    JR C,.normal_record
    SUB 93
    LD L,A
    LD H,0
    CALL an_record_offset
    LD DE,an_extra_records
    ADD HL,DE
    LD DE,AN_RECORD
    LD BC,22
    LDIR
    JR .record_ready
.normal_record:
    LD L,A
    LD H,0
    CALL an_record_offset
    LD DE,$B800
    ADD HL,DE
    LD DE,AN_RECORD
    LD BC,22
    LD A,133
    CALL an_copy
.record_ready:
    LD A,(p_w_base)
    AND 7
    LD B,A
    LD A,(AN_RECORD+19)
    CP B
    JP NZ,.native
    LD A,(p_w_coarse)
    LD B,A
    LD A,(AN_RECORD+20)
    CP B
    JP NZ,.native
    LD A,(p_bg_theme)
    RRCA
    AND 1
    CP B
    JP NZ,.native
    ; Only the two palette choices selected by the original >=3 source path.
    LD A,(p_bg_theme)
    AND 1
    LD B,A
    LD A,(p_w_color)
    CP 15
    JR Z,.white
    LD A,B
    OR A
    JP NZ,.native
    JR .combo
.white:
    LD A,B
    CP 1
    JP NZ,.native
.combo:
    LD (p_w_copy),A
    CALL an_sprite_patterns
    CALL an_draw
    CALL an_append
    JP an_return
.native:
    CALL an_native
    JP an_return

an_record_offset:
    LD D,H
    LD E,L
    ADD HL,HL
    ADD HL,HL
    ADD HL,DE
    ADD HL,HL
    ADD HL,DE
    ADD HL,HL               ;22-byte far-pointer record
    RET

an_force_rows:
    LD A,(p_fd_rows)
    AND $C0
    CP $C0
    JR NZ,.collect
    LD A,(p_fd_rows+1)
    BIT 0,A
    JR Z,.collect
    XOR A                   ;background already filled all three rows
    RET
.collect:
    LD A,(p_fd_rows)
    OR $C0
    LD (p_fd_rows),A
    LD A,(p_fd_rows+1)
    OR 1
    LD (p_fd_rows+1),A
    CALL p_fast_collect_rows
    LD A,1
    RET

an_background:
    LD A,(p_bg_profile)
    CP 32
    LD DE,$8080
    LD C,128
    RET Z
    LD A,(p_bg_theme)
    LD B,A
    DUP 3
    ADD A,A
    EDUP
    ADD A,B
    LD B,A
    LD A,(p_w_top)
    SUB 6
    LD C,A
    ADD A,A
    ADD A,C
    ADD A,B
    LD L,A
    LD H,0
    LD DE,an_background_rows
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    INC HL
    LD C,(HL)
    RET
an_name:
    LD A,(p_w_top)
    LD L,A
    LD H,0
    DUP 5
    ADD HL,HL
    EDUP
    LD DE,$C800
    LD A,(PAGE)
    OR A
    JR Z,.page
    LD D,$CD
.page:
    ADD HL,DE
    RET

; Existing count plus one is bounded at the start of the bear span and every
; sprite start inside it. Counts can increase only at those critical scanlines.
an_admit:
    LD A,(p_w_y)
    SUB 23                  ;bearStart-15: full16px rectangles intersect32px span
    LD C,A
    LD A,(p_sat_bytes)
    DEC A
    DUP 2
    SRL A
    EDUP
    LD B,A
    OR A
    JR Z,.empty
    LD HL,SAT
    LD DE,$C500
.filter:
    LD A,(HL)
    INC A
    SUB C
    CP 47
    JR NC,.filter_next
    ADD A,C
    LD (DE),A
    INC E
.filter_next:
    INC L
    INC L
    INC L
    INC L
    DJNZ .filter
    LD A,E
.empty:
    LD (p_w_line),A
    CP 4                    ;global overlap<=3 proves every scanline safe
    JR C,.yes
    JR NZ,.full
    ; Four intervals are never all active if their starts span>=16.
    ; Use relative filtered coordinates so unsigned Y wrap stays sound.
    LD A,(p_w_y)
    SUB 23
    LD E,A
    LD B,4
    LD C,255
    LD D,0
    LD HL,$C500
.extrema:
    LD A,(HL)
    SUB E
    CP C
    JR NC,.minimum
    LD C,A
.minimum:
    CP D
    JR C,.maximum
    LD D,A
.maximum:
    INC L
    DJNZ .extrema
    LD A,D
    SUB C
    CP 16
    JR NC,.yes
.full:
    LD A,(p_w_y)
    SUB 8
    LD (p_w_index),A         ;initial critical line is already tested
    CALL an_line
    RET NC
    LD A,(p_w_line)
    LD B,A
    LD HL,$C500
.outer:
    LD A,(HL)
    LD C,A
    LD A,(p_w_y)
    SUB 8
    LD E,A
    LD A,C
    SUB E
    CP 32
    JR NC,.next
    LD A,(p_w_index)
    CP C
    JR Z,.next
    LD A,C
    LD (p_w_index),A
    PUSH BC
    PUSH HL
    CALL an_line
    POP HL
    POP BC
    RET NC
.next:
    INC L
    DJNZ .outer
.yes:
    SCF
    RET
an_line:
    LD (p_w_top),A
    LD A,(p_w_line)
    LD B,A
    LD C,0
    OR A
    JR Z,.yes
    LD HL,$C500
.scan:
    LD E,(HL)
    LD A,(p_w_top)
    SUB E
    CP 16
    JR NC,.next
    INC C
    LD A,C
    CP 4
    RET NC
.next:
    INC L
    DJNZ .scan
.yes:
    SCF
    RET

an_sprite_patterns:
    LD A,(PAGE)
    ADD A,AN_KEYS&255
    LD L,A
    LD H,AN_KEYS/256
    LD A,(p_w_group)
    INC A
    CP (HL)
    RET Z
    PUSH HL
    LD A,(p_w_group)
    LD L,A
    LD H,0
    DUP 6
    ADD HL,HL
    EDUP
    LD DE,$BC00
    ADD HL,DE
    LD DE,$7AC0             ;page0 slots22/23, page1 slots46/47
    LD A,(PAGE)
    OR A
    JR Z,.page
    LD D,$7D
.page:
    LD A,132
    LD B,64
    CALL an_upload
    POP HL
    LD A,(p_w_group)
    INC A
    LD (HL),A
    RET

an_draw:
    LD A,6
    LD (p_w_top),A
    XOR A
    LD (p_w_index),A
.row:
    LD A,(PAGE)
    LD B,A
    ADD A,A
    ADD A,B
    LD B,A
    LD A,(p_w_top)
    SUB 6
    ADD A,B
    LD L,A
    LD H,0
    ADD HL,HL
    ADD HL,HL
    LD DE,an_roles
    ADD HL,DE
    LD A,(HL)
    LD (p_fx_bank),A
    INC HL
    LD A,(HL)
    LD (p_w_tile),A
    INC HL
    LD E,(HL)
    INC HL
    LD D,(HL)
    LD (p_fx_meta),DE
    CALL an_name
    LD A,(p_w_origin)
    ADD A,2
    LD E,A
    LD D,0
    ADD HL,DE
    LD (p_w_name),HL
    LD A,(p_w_copy)
    LD B,A
    ADD A,A
    ADD A,B
    LD B,A
    LD A,(p_w_index)
    ADD A,B
    LD B,A
    ADD A,A
    ADD A,B                 ;three-byte far pointer
    LD L,A
    LD H,0
    LD DE,AN_RECORD
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    INC HL
    LD A,(HL)
    LD (p_tf_column),A
    EX DE,HL
    PUSH HL
    LD A,(p_w_tile)
    LD L,A
    LD H,0
    DUP 3
    ADD HL,HL
    EDUP
    LD A,(p_fx_bank)
    DUP 3
    ADD A,A
    EDUP
    ADD A,$40
    ADD A,H
    LD H,A
    EX DE,HL
    POP HL
    PUSH DE
    LD A,(p_tf_column)
    LD B,16
    CALL an_upload
    POP DE
    LD A,D
    ADD A,$20
    LD D,A
    LD A,(p_tf_column)
    LD B,16
    CALL an_upload
    LD DE,(p_fx_meta)
    LD BC,12
    LD A,(p_tf_column)
    CALL an_copy            ;publish both keys only after completePGT/CGT
    LD IX,(p_fx_meta)
    LD HL,(p_w_name)
    LD A,(p_w_tile)
    LD B,A
    LD C,2
.cell:
    LD A,(IX+5)
    OR A
    JR NZ,.skip
    LD (HL),B
.skip:
    INC HL
    INC B
    LD DE,6
    ADD IX,DE
    DEC C
    JR NZ,.cell
    LD HL,p_w_index
    INC (HL)
    LD HL,p_w_top
    INC (HL)
    LD A,(HL)
    CP 9
    JP NZ,.row
    RET

an_append:
    LD A,(p_sat_bytes)
    DEC A
    LD L,A
    LD H,SAT/256
    LD A,(p_w_y)
    SUB 9
    LD (HL),A
    INC L
    LD A,(p_w_base)
    LD (HL),A
    INC L
    LD A,(PAGE)
    OR A
    LD A,88
    JR Z,.top
    LD A,184
.top:
    LD (HL),A
    LD B,A
    INC L
    LD A,(p_w_color)
    LD (HL),A
    INC L
    LD A,(p_w_y)
    ADD A,7
    LD (HL),A
    INC L
    LD A,(p_w_base)
    LD (HL),A
    INC L
    LD A,B
    ADD A,4
    LD (HL),A
    INC L
    LD A,(p_w_color)
    LD (HL),A
    INC L
    LD (p_s_sat),HL
    LD (HL),208
    LD A,L
    INC A
    LD (p_sat_bytes),A
    RET
an_roles:
    DB 0,2
    DW $D00C
    DB 0,6
    DW $D024
    DB 1,2
    DW $D18C
    DB 0,66
    DW $D48C
    DB 0,70
    DW $D4A4
    DB 1,66
    DW $D60C
an_background_rows:
    INCBIN "bear-background-rows.bin"
an_registry:
    INCBIN "bear-registry.bin"
an_extra_records:
    INCBIN "bear-extra-records.bin"
an_body_end:
    ASSERT $ <= $C000
    DS $C000-$,$FF
an_body_padded_end:
