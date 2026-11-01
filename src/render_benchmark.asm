; Original-free renderer probe. No native Atari code/gameplay/assets.
    ORG $4000
    DB "AB"
    DW start
    DS 12,0
    DB "FBR8"
start:
    DI
    IM 1
    LD SP,$F380
    CALL map_page2
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
    LD HL,initial_scene_data
    LD DE,INPUT
    LD BC,32
    LDIR
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
    CALL prepare
    CALL wait_vblank
    CALL commit
    LD HL,$3852
    LD (READY),HL
paced_frame_start:
    CALL demo_update
    CALL scheduler
    CALL charge_steps
    CALL prepare
paced_wait:
    CALL wait_vblank
paced_commit:
    CALL commit
    JP paced_frame_start

; Direct-call harness entry; debugger sets STEPS and immutable scene.
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
    OR A
    RET Z
.step:
    PUSH AF
surrogate_call:
    CALL source_step_surrogate
surrogate_return:
    LD HL,(TICKS)
    INC HL
    LD (TICKS),HL
    POP AF
    DEC A
    JR NZ,charge_steps.step
    RET

source_step_surrogate:
    LD BC,332
.delay:
    DEC BC
    LD A,B
    OR C
    JR NZ,.delay
    LD A,0
    NOP
    NOP
    NOP
    RET                      ;10000 standard MSX cycles,10018 including CALL

demo_update:
    XOR A
    CALL $00D5               ;diagnostic keyboard, not native input adapter
    DI
    CP 3
    JR NZ,.left
    LD A,(INPUT+24)
    CP 159
    JR Z,.buttons
    INC A
    LD (INPUT+24),A
    JR .buttons
.left:
    CP 7
    JR NZ,.buttons
    LD A,(INPUT+24)
    OR A
    JR Z,.buttons
    DEC A
    LD (INPUT+24),A
.buttons:
    XOR A
    CALL $00D8
    DI
    LD C,A
    LD A,(PREVFIRE)
    OR A
    JR NZ,.fire_save
    LD A,C
    OR A
    JR Z,.fire_save
    LD A,(INPUT+31)
    XOR 1
    LD (INPUT+31),A
    LD A,(INPUT+30)
    XOR 1
    LD (INPUT+30),A
.fire_save:
    LD A,C
    LD (PREVFIRE),A
    LD HL,INPUT
    LD B,8
.positions:
    LD A,(HL)
    INC A
    CP 160
    JR C,.position_ok
    XOR A
.position_ok:
    LD (HL),A
    INC HL
    DJNZ .positions
    LD B,4
.colors:
    LD A,(HL)
    XOR 1
    LD (HL),A
    INC HL
    DJNZ .colors
    LD B,4
.kinds:
    LD A,(HL)
    INC A
    CP 3
    JR C,.kind_ok
    XOR A
.kind_ok:
    LD (HL),A
    INC HL
    DJNZ .kinds
    LD A,(INPUT+29)
    INC A
    AND 3
    LD (INPUT+29),A
    LD A,(TICKS)
    AND 32
    RRCA
    RRCA
    RRCA
    RRCA
    RRCA
    LD (INPUT+28),A
    RET

    INCLUDE "render.asm"
vdp_register_values:
    DB $02,$C2,$06,$FF,$03,$36,$07,$04
identity:
    DB "FROSTBITE MSX1 RENDER BENCH 0.0.2 - SYNTHETIC NO GAMEPLAY",0
    INCLUDE "render_tables.inc"
rom_end:
    ASSERT $ <= $C000
    DS $C000-$,$FF
