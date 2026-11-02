; Native background component. Foreground/HUD remain INCOMPLETE/private;
; full-source pixel acceptance must fail until their compositor is implemented.
    IFDEF WITH_PRESENTATION_FAST
INPUT       EQU $C2C0       ; only+30/+31 are live selector flags
    ELSE
INPUT       EQU $C100
    ENDIF
PAGE        EQU $C200
ROWCOUNT    EQU $C21F
PHASE       EQU $C212
DELTA       EQU $C214
STEPS       EQU $C216
TICKS       EQU $C218
PALFLAG     EQU $C21B
READY       EQU $C2FE
SAT         EQU $C400
NAMES       EQU $C800
p_bg_profile EQU $C2E0
p_bg_theme EQU $C2E1
p_bg_changed EQU $C2E9
p_sat_bytes EQU $C2EA
p_bg_previous EQU $CCE0
    INCLUDE "presentation_background.inc"

vdp_write:
    LD A,E
    OUT ($99),A
    LD A,D
    OUT ($99),A
    LD C,$98
vdp_stream:
.byte:
    OUTI
    JP NZ,.byte              ;29 standard MSX cycles/data write
    RET

presentation_init:
    IFDEF WITH_PRESENTATION_TEMPLATES
    LD HL,$C080
    LD DE,$C081
    LD BC,255
    LD (HL),0
    LDIR                    ;all eight player ways begin unpublished
    ENDIF
    LD HL,$C380
    LD DE,$C381
    LD BC,63
    LD (HL),0
    LDIR
    LD HL,$C400
    LD DE,$C401
    LD BC,$1FF
    LD (HL),0
    LDIR
    LD HL,$C800
    LD DE,$C801
    LD BC,$1FFF             ;ends E7FF; E800-F33F remains guarded
    LD (HL),0
    LDIR
    IFDEF WITH_PRESENTATION_FAST
    LD HL,$C800
    LD DE,$C801
    LD BC,767
    LD (HL),128
    LDIR
    LD HL,$CD00
    LD DE,$CD01
    LD BC,767
    LD (HL),128
    LDIR
    LD A,1
    LD ($7000),A
    LD HL,p_fast_crc_rom_data
    LD DE,p_fast_crc_data
    LD BC,256
    LDIR                    ;read-only CRC page replaces unused shadow storage
    ENDIF
    LD A,208
    LD (SAT),A
    LD HL,$FFFF
    LD (p_bg_previous),HL
    CALL p_bg_upload_static
    RET

cache_init:
    IFDEF WITH_PRESENTATION_FAST
    JP p_fast_init
    ELSE
    RET
    ENDIF

prepare:
presentation_prepare:
    LD A,1
    LD ($7000),A
    LD A,(PAGE)
    XOR 1
    LD (PAGE),A
    IFDEF WITH_PRESENTATION_FAST
    XOR A
    LD (p_w_fault),A
    CALL p_bg_describe
    LD A,2
    LD ($7000),A
    CALL p_dirty_describe
    CALL p_fast_release_dirty
    ELSE
    CALL presentation_cache_begin
    LD HL,$FFFF             ;private correctness candidate: reset both page rows
    LD (p_bg_previous),HL
    ENDIF
    CALL presentation_background_prepare
    CALL presentation_world_prepare
    CALL presentation_hud_prepare
    CALL presentation_footer_prepare
    LD A,2
    LD ($7000),A
    CALL presentation_sprites_prepare
    IFDEF WITH_PRESENTATION_FAST
    CALL p_fast_upload_dirty
    ELSE
    CALL p_bg_upload_names
    ENDIF
    RET

commit:
presentation_commit:
    LD HL,SAT
    LD DE,$5B00
    LD A,(p_sat_bytes)
    LD B,A
    CALL vdp_write
    LD A,(PAGE)
    ADD A,6
    OUT ($99),A
    LD A,$82
    OUT ($99),A
    RET

    IFNDEF WITH_PRESENTATION_FAST
presentation_black_sat:
    LD A,($C03F)
    BIT 7,A
    JR NZ,.blank
    LD HL,SAT
    LD D,63
    LD B,7
.row:
    LD A,D
    LD (HL),A
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
    DJNZ .row
    LD (HL),208
    LD A,29
    LD (p_sat_bytes),A
    RET
.blank:
    LD A,208
    LD (SAT),A
    LD A,1
    LD (p_sat_bytes),A
    RET
    ENDIF

presentation_background_prepare:
    IFDEF WITH_PRESENTATION_FAST
    JP p_fast_background_rows
    ELSE
    XOR A
    LD (p_bg_changed),A
    LD A,($C03F)
    BIT 7,A
    LD A,32
    JR NZ,.profile
    LD A,($C045)
    OR A
    JP M,.night
    LD A,($C04B)
    AND 4
    JR NZ,.night
    LD E,0
    JR .coarse
.night:
    LD E,1
.coarse:
    LD A,($C068)
    CP 150
    JR C,.small
    SET 1,E
.small:
    LD A,E
    LD (p_bg_theme),A
    LD A,($C002)
    LD L,A
    LD H,p_bg_rng_data/256
    LD A,(HL)
    ADD A,A
    ADD A,A
    OR E
.profile:
    LD (p_bg_profile),A
    LD B,A
    LD A,(PAGE)
    LD L,A
    LD H,0
    LD DE,p_bg_previous
    ADD HL,DE
    LD A,(HL)
    CP B
    RET Z
    LD (HL),B
    LD C,A
    LD A,B
    CP 32
    JP Z,.blank
    LD A,C
    CP 32
    JR NC,.full
    XOR B
    AND 3
    JR NZ,.full
    LD A,1
    LD (p_bg_changed),A
    CALL p_bg_gradient_ram
    CALL p_bg_buffer_hl
    LD BC,98
    ADD HL,BC
    LD DE,$5862
    LD A,(PAGE)
    OR A
    JR Z,.gradient_address
    LD D,$5C
.gradient_address:
    LD B,29
    IFDEF WITH_PRESENTATION_FAST
    RET
    ELSE
    JP vdp_write
    ENDIF
.full:
    LD A,2
    LD (p_bg_changed),A
    LD A,(p_bg_theme)
    ADD A,A
    LD L,A
    LD H,0
    LD DE,p_bg_roots
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    EX DE,HL
    CALL p_bg_buffer_de
    LD B,24
.row:
    PUSH BC
    LD A,128
    LD (DE),A
    INC DE
    LD A,(HL)
    INC HL
    LD (DE),A
    INC DE
    LD A,(HL)
    INC HL
    LD (DE),A
    INC DE
    LD A,(HL)
    INC HL
    DUP 28
    LD (DE),A
    INC DE
    EDUP
    LD A,128
    LD (DE),A
    INC DE
    POP BC
    DJNZ .row
    CALL p_bg_gradient_ram
    IFDEF WITH_PRESENTATION_FAST
    RET
    ELSE
    JP p_bg_upload_names
    ENDIF
.blank:
    LD A,2
    LD (p_bg_changed),A
    CALL p_bg_buffer_hl
    LD D,H
    LD E,L
    INC DE
    LD BC,767
    LD (HL),128
    LDIR
    IFDEF WITH_PRESENTATION_FAST
    RET
    ELSE
    JP p_bg_upload_names
    ENDIF

p_bg_gradient_ram:
    LD A,(p_bg_profile)
    AND 28
    LD C,A
    LD A,(p_bg_theme)
    AND 1
    ADD A,A
    OR C
    LD L,A
    LD H,0
    LD DE,p_bg_gradient_data
    ADD HL,DE
    CALL p_bg_buffer_de
    LD E,98
    LD A,(HL)
    INC HL
    LD (DE),A
    INC DE
    LD A,(HL)
    DUP 28
    LD (DE),A
    INC DE
    EDUP
    RET
p_bg_buffer_hl:
    LD HL,NAMES
    LD A,(PAGE)
    OR A
    RET Z
    LD H,$CD
    RET
p_bg_buffer_de:
    LD DE,NAMES
    LD A,(PAGE)
    OR A
    RET Z
    LD D,$CD
    RET
p_bg_upload_names:
    CALL p_bg_buffer_hl
    LD DE,$5800
    LD A,(PAGE)
    OR A
    JR Z,.address
    LD D,$5C
.address:
    LD B,0
    CALL vdp_write
    LD B,0
    CALL vdp_stream
    LD B,0
    JP vdp_stream
    ENDIF
    IFDEF WITH_PRESENTATION_FAST
p_bg_describe:
    LD A,($C068)
    CP 150
    LD A,0
    ADC A,0
    XOR 1
    LD (p_w_coarse),A
    LD A,($C03F)
    BIT 7,A
    LD A,32
    JR NZ,.profile
    LD A,($C045)
    OR A
    JP M,.night
    LD A,($C04B)
    AND 4
    JR NZ,.night
    LD E,0
    JR .coarse
.night:
    LD E,1
.coarse:
    LD A,(p_w_coarse)
    ADD A,A
    OR E
    LD E,A
    LD (p_bg_theme),A
    LD A,($C002)
    LD L,A
    LD H,p_bg_rng_data/256
    LD A,(HL)
    ADD A,A
    ADD A,A
    OR E
.profile:
    LD (p_bg_profile),A
    RET
    ENDIF
p_bg_roots:
    DW p_bg_rows_data,p_bg_rows_data+72,p_bg_rows_data+144,p_bg_rows_data+216

    INCLUDE "presentation_background_init.inc"

    IFDEF WITH_PRESENTATION_FAST
    IFDEF WITH_PRESENTATION_FIXED
    INCLUDE "presentation_fixed_runtime.asm"
    IFDEF WITH_PRESENTATION_TEMPLATES
    INCLUDE "presentation_template_reader.asm"
    INCLUDE "presentation_template_upload.asm"
    INCLUDE "presentation_template_strip.asm"
    INCLUDE "presentation_template_loader.asm"
    INCLUDE "presentation_name_rows.asm"
    INCLUDE "presentation_name_decode.asm"
    INCLUDE "presentation_background_cover.asm"
    INCLUDE "presentation_template_floe.asm"
    ELSE
    INCLUDE "presentation_fixed_pool.asm"
    INCLUDE "presentation_fixed_floe.asm"
    INCLUDE "presentation_fixed_emit.asm"
    ENDIF
    ELSE
    INCLUDE "presentation_fast_cache.asm"
    ENDIF
    INCLUDE "presentation_typed.asm"
    INCLUDE "presentation_fast_world.asm"
    INCLUDE "presentation_fast_hud.asm"
    INCLUDE "presentation_dirty_rows.asm"
    ELSE
    INCLUDE "presentation_cache.asm"
    ENDIF
    INCLUDE "presentation_geometry.asm"
    INCLUDE "presentation_world.asm"
    INCLUDE "presentation_hud.asm"
