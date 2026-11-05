    INCLUDE "symbols.inc"
    ORG p_fast_background_rows+3
ys_static:
    CALL p_static_lookup
    LD A,(p_s_upload)
    OR A
    RET NZ                  ; cold shapes keep the original producer
    POP HL                  ; replace the caller's remaining static tail
    LD DE,(p_s_sat)
    LD HL,ys_mask
    LD BC,28
    LDIR
    LD A,(PAGE)
    LD C,A
    ADD A,A
    ADD A,A
    ADD A,C
    ADD A,A
    ADD A,A
    ADD A,192
    LD C,A
    LD A,(p_s_door)
    OR A
    JR Z,.logo
    LD A,31
    LD (DE),A
    INC DE
    LD A,192
    LD (DE),A
    INC DE
    LD A,C
    LD (DE),A
    INC DE
    ADD A,4
    LD C,A
    LD A,(p_bg_theme)
    AND 1
    LD A,0
    JR Z,.door_color
    LD A,($F001)
    LD B,A
    LD A,($F002)
    XOR B
    AND 8
    LD A,0
    JR NZ,.door_color
    LD A,56
.door_color:
    CALL p_sprite_color
    LD (DE),A
    INC DE
.logo:
    LD A,12
    CALL p_sprite_color
    LD A,(p_s_logo_top)
    DEC A
    LD H,A
    LD L,53
    LD B,4
.part:
    LD A,H
    LD (DE),A
    INC DE
    LD A,L
    LD (DE),A
    INC DE
    LD A,C
    LD (DE),A
    INC DE
    LD A,(p_s_color)
    LD (DE),A
    INC DE
    LD A,L
    ADD A,16
    LD L,A
    LD A,C
    ADD A,4
    LD C,A
    DJNZ .part
    LD (p_s_sat),DE
    LD A,(p_s_door)
    ADD A,4
    LD B,A
    LD A,(p_s_static_start)
    ADD A,B
    LD (p_s_count),A
    CALL p_static_store
    JP p_s_finish
ys_mask:
    DUP 7,ys_mask_index
    DB 63+ys_mask_index*16,16,252,1
    EDUP
ys_end:
    ASSERT $ <= p_fast_upload_dirty
