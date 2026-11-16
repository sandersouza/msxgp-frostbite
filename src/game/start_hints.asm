; Pre-game instructions. These three legacy bootstrap extents are not entered
; by native cartridge/DOS/BASIC loading: all formats enter nc_entry at C400h.
; The native clock ends at E99Dh and skips the former slot/mapper bootstrap.
; Reuse the offscreen igloo slots only while the source is waiting to start.
; Invalidate their keys after uploading so a later igloo always reconstructs.
    INCLUDE "symbols.inc"

    ORG $4014
sh_data:
sh_font:
    DB $7C,$40,$40,$78,$40,$40,$40,$00 ; F
    DB $10,$30,$10,$10,$10,$10,$38,$00 ; 1
    DB $00,$00,$18,$18,$00,$18,$18,$00 ; :
    DB $00,$00,$00,$00,$00,$00,$00,$00 ; space
    DB $3C,$40,$40,$38,$04,$04,$78,$00 ; S
    DB $7C,$10,$10,$10,$10,$10,$10,$00 ; T
    DB $38,$44,$44,$44,$7C,$44,$44,$00 ; A
    DB $78,$44,$44,$78,$50,$48,$44,$00 ; R
    DB $38,$44,$04,$08,$10,$20,$7C,$00 ; 2
    DB $7C,$40,$40,$78,$40,$40,$7C,$00 ; E
    DB $40,$40,$40,$40,$40,$40,$7C,$00 ; L
    DB $3C,$40,$40,$40,$40,$40,$3C,$00 ; C
sh_lines:
    ; Two rows per page, same column; padded START keeps both rows ten cells.
    DUP 2, page
    DB 38+page*64,39+page*64,40+page*64,41+page*64,42+page*64
    DB 43+page*64,44+page*64,45+page*64,43+page*64,41+page*64
    DB 38+page*64,46+page*64,40+page*64,41+page*64,42+page*64
    DB 47+page*64,48+page*64,47+page*64,49+page*64,43+page*64
    EDUP
sh_visible:
    DB 0,0
    ASSERT $ <= $40B1
    DS $40B1-$,0
sh_data_end:

    ORG $7C51
sh_prepare:
    CALL fb_p_fast_upload_dirty
    LD A,($F046)
    OR A
    JR NZ,.state
    LD HL,(sh_visible)
    LD A,H
    OR L
    RET Z                    ; steady active play: only the visibility guard
.state:
    LD A,(fb_PAGE)
    LD E,A
    LD D,0
    LD HL,sh_visible
    ADD HL,DE
    LD A,($F046)             ; coherent pre-game flag, never live source RAM
    OR A
    JR Z,.hide
    LD A,(HL)
    OR A
    JR NZ,.shown
    PUSH HL
    CALL sh_load_font
    POP HL
    LD (HL),1
.shown:
    LD A,(fb_PAGE)
    ADD A,A
    ADD A,A
    LD E,A
    ADD A,A
    ADD A,A
    ADD A,E                  ; twenty NAME bytes per page
    LD E,A
    LD D,0
    LD HL,sh_lines
    ADD HL,DE
    CALL sh_names_address
    XOR A                    ; consecutive source rows
    JR sh_rows
.hide:
    LD A,(HL)
    OR A
    RET Z                    ; active play: no VRAM work after both pages hide
    LD (HL),0
    LD A,(fb_PAGE)
    LD H,A
    ADD A,A
    ADD A,A
    ADD A,H
    ADD A,$C8                ; untouched renderer NAME buffers C800h / CD00h
    LD H,A
    LD L,53
    CALL sh_names_address
    LD A,22                  ; normal NAME rows have a 32-byte stride
sh_rows:
    PUSH AF
    PUSH DE
    LD B,10
    CALL fb_vdp_write
    POP DE
    POP AF
    LD C,A
    LD B,0
    ADD HL,BC
    LD A,E
    ADD A,32
    LD E,A
    LD B,10
    JP fb_vdp_write
sh_names_address:
    LD A,(fb_PAGE)
    ADD A,A
    ADD A,A
    ADD A,$58
    LD D,A
    LD E,53                  ; x=168, y=8/16; eight-pixel top/right margins
    RET
    ASSERT $ <= $7CF2
    DS $7CF2-$,0
sh_code_end:

    ORG $E99D
sh_load_font:
    LD A,(fb_PAGE)
    ADD A,A
    ADD A,$41
    LD D,A
    LD E,$30                 ; tiles 38..49 or 102..113 in PGT bank zero
    LD HL,sh_font
    LD B,96
    CALL fb_vdp_write
    SET 5,D                  ; same twelve tiles in CGT
    DI
    LD A,E
    OUT ($99),A
    LD A,D
    OUT ($99),A
    LD A,$F4                 ; white MSX-style glyphs on header blue
    LD B,96
.colors:
    OUT ($98),A
    NOP
    NOP
    DJNZ .colors
    CALL fb_t_restore_interrupts
    LD A,(fb_PAGE)
    LD HL,$D0E4              ; twelve six-byte igloo keys, page zero
    OR A
    JR Z,.keys
    LD HL,$D564              ; same keys, page one
.keys:
    LD D,H
    LD E,L
    INC DE
    LD BC,71
    LD (HL),255
    LDIR
    RET
    ASSERT $ <= $E9EE
    DS $E9EE-$,0
sh_helper_end:

    ; The former SCREEN 2/cache initializer is also bypassed by native cold
    ; loading, which supplies the complete static RAM/VRAM image directly.
    ; Clear its unreachable body to keep the cartridge within 32 KiB.
    ORG $4971
sh_retired_init:
    DS $49DB-$,0
sh_retired_init_end:
