; Native movement diagnostic. Synthetic presentation and scripted contacts.
    ORG $4000
    DB "AB"
    DW start
    DS 12,0
    IFDEF WITH_FLOES
    DB "FBF0"
    ELSE
    DB "FBM0"
    ENDIF
start:
    DI
    IM 1
    LD SP,$F380
    CALL map_page2
    LD A,1
    LD ($7000),A
    LD A,2
    CALL $005F               ;BIOS SCREEN2 init, then own VDP polling
    DI
    LD A,$82                 ;16KiB VRAM, display/IRQ off,16x16sprites
    OUT ($99),A
    LD A,$81
    OUT ($99),A
    LD HL,$C000
    LD DE,$C001
    LD BC,$300
    LD (HL),0
    LDIR
    LD DE,$4000
    CALL set_address
    LD BC,16384
    XOR A
.clear_vram:
    OUT ($98),A
    LD D,A
    DEC BC
    LD A,B
    OR C
    LD A,D
    JR NZ,.clear_vram
    LD HL,font_patterns_data
    LD DE,$4000
    CALL copy_512
    LD HL,font_patterns_data
    LD DE,$4800
    CALL copy_512
    LD HL,font_patterns_data
    LD DE,$5000
    CALL copy_512
    LD HL,font_colors_data
    LD DE,$6000
    CALL copy_512
    LD HL,font_colors_data
    LD DE,$6800
    CALL copy_512
    LD HL,font_colors_data
    LD DE,$7000
    CALL copy_512
    LD HL,sprites_data
    LD DE,$7800
    LD A,8
    LD (ROWCOUNT),A
    CALL set_address
.sprites:
    LD B,0
    CALL vdp_stream
    LD A,(ROWCOUNT)
    DEC A
    LD (ROWCOUNT),A
    JR NZ,.sprites
    LD HL,names_data
    LD DE,NAMES
    LD BC,768
    LDIR
    LD HL,names_data
    LD DE,$5800
    CALL copy_768
    LD HL,names_data
    LD DE,$5C00
    CALL copy_768
    CALL load_atlas
    LD HL,initial_scene_data
    LD DE,INPUT
    LD BC,32
    LDIR
    IFDEF WITH_FLOES
    LD DE,$5B00              ; terminate SAT before enabling display/pacing
    CALL set_address
    LD A,208
    OUT ($98),A
    ENDIF
    LD HL,vdp_register_values
    LD B,8
    LD C,$80
.regs:
    LD A,(HL)
    OUT ($99),A
    LD A,C
    OUT ($99),A
    INC HL
    INC C
    DJNZ .regs
    CALL detect_period
    CALL cache_init
    CALL input_init
    XOR A
    LD ($C622),A
    CALL native_reset
native_reset_done:
    CALL adapt_scene
    CALL prepare
    CALL wait_vblank
    CALL commit
    LD HL,$3852
    LD (READY),HL
paced_frame_start:
    CALL diagnostic_selectors
    CALL scheduler
    CALL charge_steps
    CALL adapt_scene
    CALL prepare
paced_wait:
    CALL wait_vblank
paced_commit:
    CALL commit
    JP paced_frame_start

; RPC renderer tests use a fixed presentation with real native source steps.
rpc_start:
    CALL charge_steps
    CALL prepare
prepared_marker:
    CALL commit
rpc_done:
    JP rpc_done

map_page2:
    CALL $0138               ;RSLREG primary slot of cartridge page1
    RRCA
    RRCA
    AND 3
    LD C,A
    LD E,A
    LD D,0
    LD HL,$FCC1              ;EXPTBL
    ADD HL,DE
    BIT 7,(HL)
    JR Z,.slot
    LD HL,$FCC5              ;SLTTBL page1 secondary selection
    ADD HL,DE
    LD A,(HL)
    AND $0C
    OR C
    OR $80
    JR .enable
.slot:
    LD A,C
.enable:
    LD H,$80
    JP $0024                 ;ENASLT page2; page0 BIOS/page3 RAM retained

set_address:
    LD A,E
    OUT ($99),A
    LD A,D
    OUT ($99),A
    LD C,$98
    RET
copy_512:
    CALL set_address
    LD B,0
    CALL vdp_stream
    LD B,0
    JP vdp_stream
copy_768:
    CALL copy_512
    LD B,0
    JP vdp_stream

wait_vblank:
    IN A,($99)
status_sample:
    AND $80
    JR Z,wait_vblank
    RET

detect_period:
    CALL wait_vblank          ;discard an old pending flag after initialization
    CALL wait_vblank
    LD HL,0
.count:
    INC HL
    IN A,($99)
    RLCA
    JR NC,.count
    LD DE,1800
    OR A
    SBC HL,DE
    LD HL,0
    LD A,0
    JR C,.ntsc
    LD HL,11628
    LD A,1
.ntsc:
    LD (DELTA),HL
    LD (PALFLAG),A
    RET

scheduler:
    LD A,1
    LD (STEPS),A
    LD HL,(PHASE)
    LD DE,(DELTA)
    ADD HL,DE
    JR C,.overflow
    LD DE,59736
    OR A
    SBC HL,DE
    JR NC,.extra
    ADD HL,DE
    JR .save
.overflow:
    LD DE,5800               ;65536-59736
    ADD HL,DE
.extra:
    LD A,2
    LD (STEPS),A
.save:
    LD (PHASE),HL
    RET

charge_steps:
    LD A,(STEPS)
.step:
    PUSH AF
    CALL native_step
    LD HL,(TICKS)
    INC HL
    LD (TICKS),HL
    POP AF
    DEC A
    JR NZ,.step
    RET

native_reset:
    LD A,2
    LD ($7000),A
    XOR A
    LD (core_v),A
    LD ($C344),A
    LD A,$30
    LD (core_mode),A
    LD A,$80
    LD (core_stack_high),A
    LD IX,$C07F
    LD BC,0
    LD E,0
    XOR A
    CALL core_F000
    JP save_native_state
native_step:
    LD A,2
    LD ($7000),A
    LD A,(core_mode)
    BIT 3,A
    JP NZ,core_fault         ; whole-phase ABI requires source D clear
    LD A,(core_sp)
    CP 255
    JP NZ,core_fault         ; physical source return writes use proved call depth
    IFDEF WITH_FLOES
    CALL visible_step
    ELSE
    CALL scripted_contacts
    ENDIF
    LD A,(core_sp)
    AND 127
    LD L,A
    LD H,$C0
    PUSH HL
    POP IX
    LD A,(core_sp)
    AND 128
    LD (core_stack_high),A
    LD A,($C6F4)
    LD E,A
    LD BC,($C6F2)
    LD H,$C0
    LD L,B
    PUSH HL
    POP IY
    LD HL,($C6F0)
    PUSH HL
    POP AF
native_call:
    CALL core_F476
native_return:
native_state_boundary:
save_native_state:
    PUSH AF
    POP HL
    LD ($C6F0),HL
    LD ($C6F2),BC
    LD A,E
    LD ($C6F4),A
    PUSH IX
    POP HL
    LD A,(core_stack_high)
    OR L
    LD (core_sp),A
    RET

; These named stimuli intentionally replace collision acquisition until issue11.
; No X geometry or approximate collision engine is used.
scripted_contacts:
    LD HL,$C030
    LD DE,$C031
    LD BC,7
    LD (HL),0
    LDIR
    LD HL,$FFFF
    LD ($C038),HL
    XOR A
    LD ($C06D),A
    LD A,($C06A)
    OR A
    RET NZ
    LD A,($C064)
    LD HL,$C036
    CP 53
    JR Z,.set
    DEC L
    DEC L
    CP 79
    JR Z,.set
    DEC L
    DEC L
    CP 105
    JR Z,.set
    DEC L
    DEC L
    CP 131
    RET NZ
.set:
    LD (HL),128
    RET

; F3 toggles layout; F4 toggles width, once per press. F1/F2 belong to source.
diagnostic_selectors:
    IN A,($AA)
    LD D,A
    AND $F0
    OR 6
    OUT ($AA),A
    IN A,($A9)
    CPL
    AND 128
    RLCA
    LD B,A
    LD A,D
    AND $F0
    OR 7
    OUT ($AA),A
    IN A,($A9)
    CPL
    AND 1
    ADD A,A
    OR B
    LD B,A
    LD A,D
    OUT ($AA),A
    LD A,($C622)
    CPL
    AND B
    LD C,A
    LD A,B
    LD ($C622),A
    BIT 0,C
    JR Z,.width
    LD A,(INPUT+31)
    XOR 1
    LD (INPUT+31),A
.width:
    BIT 1,C
    RET Z
    LD A,(INPUT+30)
    XOR 1
    LD (INPUT+30),A
    RET

; Synthetic raster mapping only; canonical source coordinates stay read-only.
adapt_scene:
    LD A,($C022)
    CALL normalize_x
    LD (INPUT+0),A
    LD A,($C021)
    CALL normalize_x
    LD (INPUT+1),A
    LD A,($C020)
    CALL normalize_x
    LD (INPUT+2),A
    LD A,($C01F)
    CALL normalize_x
    LD (INPUT+3),A
    LD A,($C057)
    CALL normalize_x
    LD (INPUT+4),A
    LD A,($C056)
    CALL normalize_x
    LD (INPUT+5),A
    LD A,($C055)
    CALL normalize_x
    LD (INPUT+6),A
    LD A,($C054)
    CALL normalize_x
    LD (INPUT+7),A
    LD A,($C02E)
    CP 12
    LD A,0
    JR Z,$+3
    INC A
    LD (INPUT+8),A
    LD A,($C02D)
    CP 12
    LD A,0
    JR Z,$+3
    INC A
    LD (INPUT+9),A
    LD A,($C02C)
    CP 12
    LD A,0
    JR Z,$+3
    INC A
    LD (INPUT+10),A
    LD A,($C02B)
    CP 12
    LD A,0
    JR Z,$+3
    INC A
    LD (INPUT+11),A
    LD A,($C014)
    AND 3
    CP 3
    JR C,$+4
    LD A,2
    LD (INPUT+12),A
    LD A,($C013)
    AND 3
    CP 3
    JR C,$+4
    LD A,2
    LD (INPUT+13),A
    LD A,($C012)
    AND 3
    CP 3
    JR C,$+4
    LD A,2
    LD (INPUT+14),A
    LD A,($C011)
    AND 3
    CP 3
    JR C,$+4
    LD A,2
    LD (INPUT+15),A
    LD A,($C05B)
    IFDEF WITH_HAZARDS
    CP 2
    JR NC,$+3
    INC A
    ELSE
    CP 4
    JR C,$+4
    LD A,3
    ENDIF
    LD (INPUT+16),A
    LD A,($C05A)
    IFDEF WITH_HAZARDS
    CP 2
    JR NC,$+3
    INC A
    ELSE
    CP 4
    JR C,$+4
    LD A,3
    ENDIF
    LD (INPUT+17),A
    LD A,($C059)
    IFDEF WITH_HAZARDS
    CP 2
    JR NC,$+3
    INC A
    ELSE
    CP 4
    JR C,$+4
    LD A,3
    ENDIF
    LD (INPUT+18),A
    LD A,($C058)
    IFDEF WITH_HAZARDS
    CP 2
    JR NC,$+3
    INC A
    ELSE
    CP 4
    JR C,$+4
    LD A,3
    ENDIF
    LD (INPUT+19),A
    IFDEF WITH_HAZARDS
    LD A,($C05B)
    CP 2
    LD A,0
    JR NZ,$+3
    INC A
    ELSE
    LD A,($C014)
    AND 64
    RLCA
    RLCA
    ENDIF
    LD (INPUT+20),A
    IFDEF WITH_HAZARDS
    LD A,($C05A)
    CP 2
    LD A,0
    JR NZ,$+3
    INC A
    ELSE
    LD A,($C013)
    AND 64
    RLCA
    RLCA
    ENDIF
    LD (INPUT+21),A
    IFDEF WITH_HAZARDS
    LD A,($C059)
    CP 2
    LD A,0
    JR NZ,$+3
    INC A
    ELSE
    LD A,($C012)
    AND 64
    RLCA
    RLCA
    ENDIF
    LD (INPUT+22),A
    IFDEF WITH_HAZARDS
    LD A,($C058)
    CP 2
    LD A,0
    JR NZ,$+3
    INC A
    ELSE
    LD A,($C011)
    AND 64
    RLCA
    RLCA
    ENDIF
    LD (INPUT+23),A
    LD A,($C066)
    CALL normalize_x
    LD (INPUT+24),A
    LD A,($C064)
    ADD A,21
    JR C,.bottom
    CP 192
    JR C,.y
.bottom:
    LD A,191
.y:
    LD (INPUT+25),A
    LD A,($C068)
    CP 152
    JR C,.bear
    LD A,151
.bear:
    LD (INPUT+26),A
    LD A,51
    LD (INPUT+27),A
    LD A,($C04B)
    AND 4
    RRCA
    RRCA
    LD (INPUT+28),A
    LD A,($C04D)
    IFDEF WITH_FLOES
    CP 255
    LD A,0
    JR Z,.igloo
    LD A,($C04D)
    CP 15
    LD A,3
    JR Z,.igloo
    LD A,($C04D)
    CP 8
    LD A,1
    JR C,.igloo
    INC A
    ELSE
    SRL A
    SRL A
    CP 4
    JR C,.igloo
    LD A,3
    ENDIF
.igloo:
    LD (INPUT+29),A
adapt_done:
    RET
normalize_x:
    CP 160
    RET C
    SUB 160
    RET

    DEFINE WITH_NATIVE_INPUT
    DEFINE FAST_PHASE
    INCLUDE "native_input.asm"
    INCLUDE "movement_render.inc"
    INCLUDE "movement_rows.asm"
    INCLUDE "movement_cache.asm"
vdp_register_values:
    DB $02,$C2,$06,$FF,$03,$36,$07,$04
identity:
    IFDEF WITH_FLOES
    IFDEF WITH_HAZARDS
    IFDEF WITH_PROGRESSION
    DB "FROSTBITE PROGRESSION DIAGNOSTIC 0.0.6 REAL CONTACTS SYNTHETIC NO AUDIO",0
    ELSE
    DB "FROSTBITE HAZARD DIAGNOSTIC 0.0.5 REAL CONTACTS SYNTHETIC NO AUDIO",0
    ENDIF
    ELSE
    DB "FROSTBITE BUILD LOOP DIAGNOSTIC 0.0.4 REAL FLOES SYNTHETIC NO AUDIO",0
    ENDIF
    INCLUDE "floe_visible.asm"
    ELSE
    DB "FROSTBITE MOVEMENT DIAGNOSTIC 0.0.3 SCRIPTED CONTACTS SYNTHETIC NO AUDIO",0
    ENDIF
    INCLUDE "resident_tables.inc"
resident_end:
    ASSERT $ <= $8000
    DS $8000-$,$FF
    ORG $8000
    INCLUDE "boot_tables.inc"
assets_end:
    ASSERT $ <= $C000
    DS $C000-$,$FF
    ORG $8000
    INCLUDE "native_cpu.asm"
    INCLUDE "core.inc"
    ALIGN 1024
original_data:
    INCBIN "data.bin"
native_end:
    ASSERT $ <= $C000
    DS $C000-$,$FF
    INCLUDE "row_banks.inc"
    IFDEF WITH_FLOES
    INCLUDE "contact_banks.inc"
    INCLUDE "cartridge_padding.inc"
    ELSE
    ORG $8000
    DS $4000,$FF
    ORG $8000
    DS $4000,$FF
    ENDIF
