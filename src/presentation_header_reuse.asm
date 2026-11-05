; Selective fixed header columns; the source clock and sprite geometry stay intact.
    INCLUDE "symbols.inc"
    ORG w_origin
w_cache EQU $E840             ;two17-byte identities, initialized FF by qe_init
w_changed EQU $E862
w_ownerptr EQU $E864
w_color_page EQU $E866

w_owner:
    LD A,(PAGE)
    LD B,A
    DUP 4
    ADD A,A
    EDUP
    ADD A,B
    ADD A,w_cache&255
    LD L,A
    LD H,w_cache/256
    LD (w_ownerptr),HL
    RET
w_level:
    LD A,($F04B)             ;coherent renderer snapshot, never live source RAM
    CP 20
    SBC A,A
    INC A
    RET
w_header:
    CALL w_owner
    LD DE,16
    ADD HL,DE
    LD A,(HL)
    CP $5A
    JR NZ,.all
    DEC HL
    CALL w_level
    CP (HL)
    JR NZ,.all
    LD HL,(w_ownerptr)
    LD DE,12
    ADD HL,DE
    LD DE,pfh_upper
    LD B,3
.colors:
    LD A,(DE)
    CP (HL)
    JR NZ,.all
    INC HL
    INC DE
    DJNZ .colors
    LD HL,0
    LD (w_changed),HL
    LD HL,(w_ownerptr)
    LD DE,p_h_codes
    LD IX,w_masks
    LD B,12
.glyph:
    LD A,(DE)
    CP (HL)
    JR Z,.next
    LD A,(w_changed)
    OR (IX)
    LD (w_changed),A
    LD A,(w_changed+1)
    OR (IX+1)
    LD (w_changed+1),A
.next:
    INC HL
    INC DE
    INC IX
    INC IX
    DJNZ .glyph
    JR .keys
.all:
    LD HL,1023
    LD (w_changed),HL
.keys:
    LD HL,(w_ownerptr)
    LD DE,16
    ADD HL,DE
    LD (HL),0
    CALL p_template_header_keys
    JP w_header_resume

w_selected:
    LD A,(p_h_index)
    LD B,A
    INC B
    LD HL,(w_changed)
.bit:
    SRL H
    RR L
    DJNZ .bit
    RET
w_pack_gate:
    CALL w_selected
    JP NC,w_pack_advance
    LD A,(IX)
    JP w_pack_resume
w_tile_gate:
    CALL w_selected
    JR NC,.keep
    CALL p_template_header_key
    JP w_tile_resume
.keep:
    LD HL,(p_w_name)
    LD A,(p_w_tile)
    LD (HL),A
    JP w_tile_advance
w_save:
    LD A,(p_w_fault)
    OR A
    JP NZ,p_fast_igloo_prepare
    CALL w_owner
    EX DE,HL
    LD HL,p_h_codes
    LD BC,12
    LDIR
    LD HL,pfh_upper
    LD BC,3
    LDIR
    CALL w_level
    LD (DE),A
    INC DE
    LD A,$5A
    LD (DE),A                ;valid only after all three bands complete
    JP p_fast_igloo_prepare
w_masks:
    DW 3,14,24,112,192,896,3,14,24,112,192,896

; Both player paths use the same adapter. Terminal animation retains old colors
; and its existing four-plane bound; normal player remains three planes.
w_player_color:
    LD A,(w_color_page)
    LD H,A
    LD A,(HL)
    RET
w_player_setup:
    LD A,($F06B)
    LD B,A
    LD A,($F070)
    OR B
    LD A,p_sprite_colors_data/256
    JR NZ,.selected
    LD A,w_palette/256
.selected:
    LD (w_color_page),A
    JP p_player_cache_lookup
    ALIGN 256
w_palette:
    INCBIN "normal-palette.bin"
w_end:
    ASSERT $ <= $F000
