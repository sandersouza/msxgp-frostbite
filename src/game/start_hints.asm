; Pre-game instructions. Existing native assets remain untouched.
; Only the unused cold initializer, bypassed clock/auxiliary bootstrap and
; unused RST vector area are replaced. IRQ vector 0038h remains intact.
    INCLUDE "symbols.inc"
    ORG $496E
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
sh_visible:
    DB 0,0
sh_invalidate:
    LD D,H
    LD E,L
    INC DE
    LD BC,71
    LD (HL),255
    LDIR
    RET
    ASSERT $ <= $49DE
    DS $49DE-$,0
sh_data_end:
    ORG $E99D
sh_prepare:
    CALL fb_p_fast_upload_dirty
    LD A,(fb_PAGE)
    LD E,A
    LD D,0
    LD HL,sh_visible
    ADD HL,DE
    CALL sh_waiting          ; do not borrow slots of an existing igloo
    JR Z,.hide
    LD A,(HL)
    OR A
    JR NZ,.shown
    INC (HL)
    CALL sh_load_font
.shown:
    LD A,(fb_PAGE)
    RRCA
    RRCA
    LD C,A
    LD HL,sh_lines
    LD DE,$C480
    LD B,20
.copy:
    LD A,(HL)
    OR C
    LD (DE),A
    INC HL
    INC DE
    DJNZ .copy
    LD HL,$C480
    CALL sh_names_address
    XOR A
    JP sh_rows
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
    JP sh_rows
    ASSERT $ <= $E9EE
    DS $E9EE-$,0
sh_code_end:
    ORG $7FBE
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
    LD A,22                  ; normal NAME source row gap (shown path clears A)
    RET
sh_lines:
    DB 38,39,40,41,42,43,44,45,43,41
    DB 38,46,40,41,42,47,48,47,49,43
sh_waiting:
    LD A,($F04D)
    INC A                    ; FF is the original empty-igloo sentinel
    JP Z,sh_waiting_empty
    XOR A
    RET
    ASSERT $ <= $8000
    DS $8000-$,0
sh_rows_end:
    ORG $0000
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
    LD HL,$D0E4
    BIT 1,D
    JR Z,.keys
    LD HL,$D564
.keys:
    JP sh_invalidate
    ASSERT $ <= $0038
    DS $0038-$,0
sh_helper_end:

    ORG $003B
sh_waiting_empty:
    LD A,($F046)
    OR A
    RET
    ASSERT $ = $0040
