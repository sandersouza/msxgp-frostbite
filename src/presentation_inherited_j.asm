    INCLUDE "symbols.inc"
    ORG $7E5D
j_flags EQU $C1C1
j_address EQU $C1C2
j_count EQU $C1C4
j_color EQU $C1C5

; Enter only after original strip publisher validates shared grammar and
; selects exclusive inactive-page roles. All prior fields remain authoritative.
j_strip:
    PUSH IX
    PUSH IY
    LD IX,(p_fx_meta)
    LD IY,p_tl_keys
    LD A,(p_tl_count)
    LD (j_count),A
    LD A,(pf_key+4)
    LD (j_color),A
    DUP 4
    RLCA
    EDUP
    OR 4
    LD HL,pt_tile+8
    DUP 8
    LD (HL),A
    INC L
    EDUP
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
    LD (j_address),HL
.slot:
    LD L,(IY+0)
    LD H,(IY+1)
    LD (pf_key),HL
    ; The slot is exclusive: tag9 proves the fixed water/zero grammar.
    LD A,(IX+5)
    CP 9
    LD A,3
    JR NZ,.flags
    XOR A
    LD B,A
    LD A,L
    CP (IX+0)
    JR NZ,.pattern_changed
    LD A,H
    CP (IX+1)
    JR Z,.color
.pattern_changed:
    INC B
.color:
    LD A,(j_color)
    CP (IX+4)
    LD A,B
    JR Z,.flags
    OR 2
.flags:
    LD (j_flags),A
    OR A
    JR Z,.next
    BIT 0,A
    JR Z,.color_write
    ; Raw IDs come from the compiled, bounded template loader. Same exact
    ; atlas mapping as p_template_floe_address, without per-tile revalidation.
    DUP 3
    ADD HL,HL
    EDUP
    LD DE,$8000+(p_template_floe_patterns_offset&$3FFF)
    ADD HL,DE
    LD A,13
    BIT 6,H
    JR Z,.mapped
    RES 6,H
    LD A,253
.mapped:
    LD ($7000),A
    LD DE,(j_address)
    LD B,8
    CALL vdp_write
.color_write:
    LD A,(j_flags)
    BIT 1,A
    JR Z,.publish
    LD DE,(j_address)
    LD A,D
    ADD A,$20
    LD D,A
    LD HL,pt_tile+8
    LD B,8
    CALL vdp_write
.publish:
    ; Full key becomes visible only after both required plane writes.
    LD HL,(pf_key)
    LD (IX+0),L
    LD (IX+1),H
    LD A,(pf_key+2)
    LD (IX+2),A
    LD (IX+3),0
    LD A,(j_color)
    LD (IX+4),A
    LD (IX+5),9
.next:
    LD HL,j_count
    DEC (HL)
    JR Z,.done
    INC IY
    INC IY
    LD DE,6
    ADD IX,DE
    LD HL,(j_address)
    LD DE,8
    ADD HL,DE
    LD (j_address),HL
    LD HL,p_w_tile
    INC (HL)
    JP .slot
.done:
    LD (p_fx_meta),IX
    LD A,(p_tl_count)
    DEC A
    LD (p_ts_cursor),A
    XOR A
    LD (p_tr_error),A
    POP IY
    POP IX
    RET
j_end:
    ASSERT $ <= $8000
