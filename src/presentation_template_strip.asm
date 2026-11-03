; PAGE/source row/foreground + loader count/IDs -> complete owned floe slots.
; Bounds and common grammar are checked ONCE. Every MISS still validates its
; raw ID and publishes the full six-byte key after the complete required IO.
p_ts_cursor EQU $C2E6
p_template_strip_publish:
    XOR A
    LD (pt_error),A
    LD A,(PAGE)
    CP 2
    JP NC,p_template_upload_fail
    LD A,(p_w_row)
    CP 4
    JP NC,p_template_upload_fail
    LD A,(p_w_color)
    OR A
    JP Z,p_template_upload_fail
    CP 16
    JP NC,p_template_upload_fail
    LD (pf_key+4),A
    LD A,(p_tl_count)
    OR A
    JP Z,p_template_upload_fail
    CP 15
    JP NC,p_template_upload_fail
    LD A,(p_w_row)
    LD E,A
    LD D,0
    LD HL,p_template_strip_bases
    ADD HL,DE
    LD B,(HL)
    LD A,(PAGE)
    DUP 6
    ADD A,A
    EDUP
    OR B
    LD (p_tf_namebase),A
    LD (p_w_tile),A
    LD A,(p_w_row)
    CP 2
    LD A,2
    JR C,.bank
    DEC A
.bank:
    LD (p_fx_bank),A
    LD B,A
    LD A,(PAGE)
    LD C,A
    ADD A,A
    ADD A,C
    ADD A,B
    LD (p_w_cachegroup),A
    LD A,B
    CP 1
    LD A,pt_water_id1
    JR Z,.water
    LD A,pt_water_id2
.water:
    LD (p_tf_water),A
    LD (pf_key+2),A
    XOR A
    LD (pf_key+3),A
    LD (p_ts_cursor),A
    LD A,9
    LD (pf_key+5),A
    CALL p_fixed_key_address
    LD (p_fx_meta),HL
.mask:
    LD A,(p_ts_cursor)
    ADD A,A
    ADD A,p_tl_keys&255
    LD L,A
    LD H,p_tl_keys/256
    LD E,(HL)
    INC L
    LD D,(HL)
    LD (pf_key),DE
    LD HL,(p_fx_meta)
    LD DE,pf_key
    DUP 6,i
    LD A,(DE)
    CP (HL)
    JR NZ,.miss
    IF i < 5
    INC DE
    INC HL
    ENDIF
    EDUP
    JR .next
.miss:
    CALL p_template_floe_upload_checked
    RET C
.next:
    LD HL,p_ts_cursor
    INC (HL)
    LD A,(p_tl_count)
    CP (HL)
    JR Z,.done
    LD HL,(p_fx_meta)
    LD DE,6
    ADD HL,DE
    LD (p_fx_meta),HL
    LD HL,p_w_tile
    INC (HL)
    JR .mask
.done:
    XOR A
    RET
p_template_strip_bases:
    DB 25,9,35,19
