; Static colored atlas plus complete inactive name rows. No per-frame tile
; uploads except page-specific crossing-band patches in the last eight tiles.
prepare:
    LD A,(PAGE)
    XOR 1
    LD (PAGE),A
    CALL handle_layout_change
    LD A,(INPUT+24)
    RRCA
    RRCA
    RRCA
    RRCA
    AND 15
    CALL digit_tile
    LD (NAMES+32+27),A
    LD A,(INPUT+24)
    AND 15
    CALL digit_tile
    LD (NAMES+32+28),A
    LD A,(INPUT+28)
    ADD A,42
    LD (NAMES+32+30),A
    CALL render_atlas_rows
    CALL upload_static_names
    JP stage_sprites

load_atlas:
    LD HL,atlas1_patterns_data
    LD DE,$4800
    CALL copy_2048
    LD HL,atlas1_colors_data
    LD DE,$6800
    CALL copy_2048
    LD HL,atlas2_patterns_data
    LD DE,$5000
    CALL copy_2048
    LD HL,atlas2_colors_data
    LD DE,$7000
    JP copy_2048
copy_2048:
    CALL set_address
    LD A,8
    LD (ROWCOUNT),A
.loop:
    LD B,0
    CALL vdp_stream
    LD A,(ROWCOUNT)
    DEC A
    LD (ROWCOUNT),A
    JR NZ,.loop
    RET

; A=variant0..33 (FF=blank), C=logical X0..159, DE=inactive name row.
upload_lookup_row:
    CP 255
    JR NZ,.lookup
    LD HL,zero_names
    LD B,32
    JP vdp_write
.lookup:
    PUSH DE
    LD L,A
    LD H,0
    DUP 5
    ADD HL,HL
    EDUP
    LD D,H
    LD E,L
    ADD HL,HL
    ADD HL,HL
    ADD HL,DE                ; variant*160
    LD E,C
    LD D,0
    ADD HL,DE
    LD A,H
    SRL A
    ADD A,3
    LD ($7000),A             ; rows512 per16KiB ROM bank
    LD A,H
    AND 1
    LD H,A
    DUP 5
    ADD HL,HL
    EDUP
    SET 7,H
    POP DE
    LD B,32
    JP vdp_write

patch_crossing:
    LD A,(INPUT+30)
    DUP 4
    RLCA
    EDUP
    LD B,A
    LD A,(INPUT+1)
    AND 15
    OR B
    LD B,A
    LD A,(INPUT+9)
    DUP 5
    RLCA
    EDUP
    OR B
    LD E,A
    LD D,0
    LD HL,patch_flags_data
    ADD HL,DE
    LD A,(HL)
    OR A
    RET Z
    LD A,E
    AND 31
    LD L,A
    LD H,0
    DUP 5
    ADD HL,HL
    EDUP
    LD DE,patch_patterns_data
    ADD HL,DE
    LD A,1
    LD ($7000),A
    LD A,(PAGE)
    DUP 5
    RLCA
    EDUP
    ADD A,$C0
    LD E,A
    LD D,$57
    LD B,32
    CALL vdp_write
    LD A,D
    ADD A,$20
    LD D,A
    LD HL,patch_white
    LD A,(INPUT+9)
    OR A
    JR Z,.color
    LD HL,patch_blue
.color:
    LD B,32
    JP vdp_write
zero_names: DS 64,0
patch_white: DS 32,$F0
patch_blue: DS 32,$50

render_atlas_rows:
    LD A,(INPUT+12)
    RLCA
    RLCA
    RLCA
    LD B,A
    LD A,(INPUT+20)
    RLCA
    RLCA
    OR B
    LD B,A
    LD A,(INPUT+16)
    OR B
    LD E,A
    LD D,0
    LD HL,object_variants_data
    ADD HL,DE
    LD A,(HL)
    CALL row_10
    LD A,(INPUT+30)
    ADD A,A
    LD B,A
    LD A,(INPUT+8)
    OR B
    CALL row_11
    LD A,(INPUT+13)
    RLCA
    RLCA
    RLCA
    LD B,A
    LD A,(INPUT+21)
    RLCA
    RLCA
    OR B
    LD B,A
    LD A,(INPUT+17)
    OR B
    LD E,A
    LD D,0
    LD HL,object_variants_data
    ADD HL,DE
    LD A,(HL)
    CALL row_13
    LD A,(INPUT+31)
    OR A
    JR Z,.aligned
    CALL patch_crossing
    LD A,(INPUT+30)
    ADD A,A
    LD B,A
    LD A,(INPUT+9)
    OR B
    ADD A,22
    CALL row_15
    LD A,(INPUT+30)
    ADD A,A
    LD B,A
    LD A,(INPUT+9)
    OR B
    LD B,A
    LD A,(PAGE)
    ADD A,A
    ADD A,A
    ADD A,B
    ADD A,26
    CALL row_16
    JR .after_crossing
.aligned:
    LD A,(INPUT+30)
    ADD A,A
    LD B,A
    LD A,(INPUT+9)
    OR B
    CALL row_14
.after_crossing:
    LD A,(INPUT+14)
    RLCA
    RLCA
    RLCA
    LD B,A
    LD A,(INPUT+22)
    RLCA
    RLCA
    OR B
    LD B,A
    LD A,(INPUT+18)
    OR B
    LD E,A
    LD D,0
    LD HL,object_variants_data
    ADD HL,DE
    LD A,(HL)
    CALL row_17
    LD A,(INPUT+30)
    ADD A,A
    LD B,A
    LD A,(INPUT+10)
    OR B
    CALL row_18
    LD A,(INPUT+15)
    RLCA
    RLCA
    RLCA
    LD B,A
    LD A,(INPUT+23)
    RLCA
    RLCA
    OR B
    LD B,A
    LD A,(INPUT+19)
    OR B
    LD E,A
    LD D,0
    LD HL,object_variants_data
    ADD HL,DE
    LD A,(HL)
    CALL row_20
    LD A,(INPUT+30)
    ADD A,A
    LD B,A
    LD A,(INPUT+11)
    OR B
    CALL row_21
    RET
row_10:
    LD B,A
    LD A,(INPUT+4)
    LD C,A
    LD A,(PAGE)
    ADD A,A
    ADD A,A
    ADD A,$59
    LD D,A
    LD E,$40
    LD A,B
    JP upload_lookup_row
row_11:
    LD B,A
    LD A,(INPUT+0)
    LD C,A
    LD A,(PAGE)
    ADD A,A
    ADD A,A
    ADD A,$59
    LD D,A
    LD E,$60
    LD A,B
    JP upload_lookup_row
row_13:
    LD B,A
    LD A,(INPUT+5)
    LD C,A
    LD A,(PAGE)
    ADD A,A
    ADD A,A
    ADD A,$59
    LD D,A
    LD E,$A0
    LD A,B
    JP upload_lookup_row
row_14:
    LD B,A
    LD A,(INPUT+1)
    LD C,A
    LD A,(PAGE)
    ADD A,A
    ADD A,A
    ADD A,$59
    LD D,A
    LD E,$C0
    LD A,B
    JP upload_lookup_row
row_15:
    LD B,A
    LD A,(INPUT+1)
    LD C,A
    LD A,(PAGE)
    ADD A,A
    ADD A,A
    ADD A,$59
    LD D,A
    LD E,$E0
    LD A,B
    JP upload_lookup_row
row_16:
    LD B,A
    LD A,(INPUT+1)
    LD C,A
    LD A,(PAGE)
    ADD A,A
    ADD A,A
    ADD A,$5A
    LD D,A
    LD E,$00
    LD A,B
    JP upload_lookup_row
row_17:
    LD B,A
    LD A,(INPUT+6)
    LD C,A
    LD A,(PAGE)
    ADD A,A
    ADD A,A
    ADD A,$5A
    LD D,A
    LD E,$20
    LD A,B
    JP upload_lookup_row
row_18:
    LD B,A
    LD A,(INPUT+2)
    LD C,A
    LD A,(PAGE)
    ADD A,A
    ADD A,A
    ADD A,$5A
    LD D,A
    LD E,$40
    LD A,B
    JP upload_lookup_row
row_20:
    LD B,A
    LD A,(INPUT+7)
    LD C,A
    LD A,(PAGE)
    ADD A,A
    ADD A,A
    ADD A,$5A
    LD D,A
    LD E,$80
    LD A,B
    JP upload_lookup_row
row_21:
    LD B,A
    LD A,(INPUT+3)
    LD C,A
    LD A,(PAGE)
    ADD A,A
    ADD A,A
    ADD A,$5A
    LD D,A
    LD E,$A0
    LD A,B
    JP upload_lookup_row
