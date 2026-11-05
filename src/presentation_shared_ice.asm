; Shared physical ice slots. Original logic and non-ice roles remain resident.
    INCLUDE "symbols.inc"
    ORG $4B6E
q_init:
    CALL $7F5F             ;K/I initialization, retained unchanged
    LD HL,$E800
    LD DE,$E801
    LD BC,$7FF
    LD (HL),255
    LDIR
    LD HL,$F000
    LD DE,$F001
    LD BC,$23F
    LD (HL),0
    LDIR
    LD A,64
    LD ($F201),A
    LD A,255
    LD ($F202),A           ;raw pattern0 is valid; its dedicated head
    LD HL,$C080            ;presentation_init continuation contract
    RET
q_entry:
    LD A,7
    LD ($7000),A
    JP q_strip
q_decode_entry:
    LD A,7
    LD ($7000),A
    JP q_decode
q_old_entry:
    LD A,7
    LD ($7000),A
    JP q_old_key
q_upload:
    CALL p_template_floe_upload_checked
    PUSH AF
    LD A,7
    LD ($7000),A
    POP AF
    RET
q_resident_end:
    ASSERT $ <= $4C00

    ORG $A10C
q_links EQU $F000
q_refs EQU $F080
q_colors EQU $F100
q_rows EQU $F180
q_cursors EQU $F200
q_rowptr EQU $F210
q_raw EQU $F212
q_index EQU $F214
q_slot EQU $F215
q_bankmask EQU $F216
q_savedgroup EQU $F217
q_codes EQU $E600

; Existing strip prologue validated PAGE/row/color/count and set common key.
q_strip:
    LD A,(p_w_cachegroup)
    LD (q_savedgroup),A
    LD A,(p_fx_bank)
    DEC A
    RRCA
    RRCA
    AND 64
    LD (q_bankmask),A
    LD A,(PAGE)
    DUP 6
    ADD A,A
    EDUP
    LD B,A
    LD A,(p_w_row)
    DUP 4
    ADD A,A
    EDUP
    ADD A,B
    ADD A,$80
    LD L,A
    LD H,$F1
    LD (q_rowptr),HL
    LD B,(HL)
    LD (HL),0              ;release only this inactive row, never its peers
    INC HL
    LD A,B
    OR A
    JR Z,.released
.release:
    LD E,(HL)
    LD D,$F0
    SET 7,E
    LD A,(DE)
    OR A
    JP Z,p_world_fail
    DEC A
    LD (DE),A
    INC HL
    DJNZ .release
.released:
    LD A,(p_tf_water)
    LD (q_codes),A
    XOR A
    LD (q_index),A
.key:
    LD A,(q_index)
    ADD A,A
    ADD A,p_tl_keys&255
    LD L,A
    LD H,p_tl_keys/256
    LD E,(HL)
    INC L
    LD D,(HL)
    LD (q_raw),DE
    LD (pf_key),DE
    CALL q_resolve
    JR NC,.acquire
    CALL q_metadata
    CALL q_upload
    JP C,p_world_fail
    LD A,(q_slot)
    LD L,A
    LD H,$F1
    LD A,(p_w_color)
    LD (HL),A              ;valid after physical pattern and color publication
.acquire:
    LD A,(q_slot)
    LD L,A
    LD H,$F0
    SET 7,L
    INC (HL)
    CALL q_physical_id
    LD B,A
    LD A,(q_index)
    INC A
    LD E,A
    ADD A,q_codes&255
    LD L,A
    LD H,q_codes/256
    LD (HL),B
    LD HL,(q_rowptr)
    LD D,0
    ADD HL,DE
    LD A,(q_slot)
    LD (HL),A
    LD HL,q_index
    INC (HL)
    LD A,(p_tl_count)
    CP (HL)
    JP NZ,.key
    LD HL,(q_rowptr)
    LD (HL),A              ;publish complete conservative owner list
    DEC A
    LD (p_ts_cursor),A
    LD A,(q_savedgroup)
    LD (p_w_cachegroup),A
    XOR A
    LD (pt_error),A
    LD (p_tr_error),A
    RET

; DE=rawID0..2048 -> direct head. Every linked index is physical, not a hash.
q_head:
    LD A,D
    OR E
    LD HL,$F202
    RET Z
    LD HL,$E7FF
    ADD HL,DE
    RET

q_resolve:
    CALL q_head
    LD A,(HL)
    LD B,128
.lookup:
    CP 255
    JR Z,.allocate
    CP 128
    JP NC,p_world_fail
    LD (q_slot),A
    LD L,A
    AND 64
    LD C,A
    LD A,(q_bankmask)
    CP C
    JR NZ,.next
    LD H,$F1
    LD A,(p_w_color)
    CP (HL)
    JR Z,.hit
.next:
    LD H,$F0
    LD A,(HL)
    DJNZ .lookup
    JP p_world_fail
.hit:
    OR A
    RET
.allocate:
    LD A,(p_fx_bank)
    DEC A
    ADD A,q_cursors&255
    LD L,A
    LD H,q_cursors/256
    LD A,(HL)
    LD B,64
.probe:
    LD (q_slot),A
    LD L,A
    LD H,$F0
    SET 7,L
    LD A,(HL)
    OR A
    JR Z,.chosen
    LD A,(q_slot)
    INC A
    AND 63
    LD C,A
    LD A,(q_bankmask)
    OR C
    DJNZ .probe
    JP p_world_fail
.chosen:
    LD A,(q_slot)
    INC A
    AND 63
    LD C,A
    LD A,(q_bankmask)
    OR C
    LD C,A
    LD A,(p_fx_bank)
    DEC A
    ADD A,q_cursors&255
    LD L,A
    LD H,q_cursors/256
    LD (HL),C
    LD A,(q_slot)
    LD L,A
    LD H,$F1
    LD A,(HL)
    OR A
    JR Z,.insert
    CALL q_metadata
    LD E,(HL)
    INC HL
    LD D,(HL)
    CALL q_head
    LD A,(q_slot)
    LD B,A
    LD C,128
.unlink:
    LD A,(HL)
    CP B
    JR Z,.remove
    CP 128
    JP NC,p_world_fail
    LD L,A
    LD H,$F0
    DEC C
    JR NZ,.unlink
    JP p_world_fail
.remove:
    LD E,B
    LD D,$F0
    LD A,(DE)
    LD (HL),A
.insert:
    LD DE,(q_raw)
    CALL q_head
    LD A,(HL)
    LD B,A
    LD A,(q_slot)
    LD (HL),A
    LD L,A
    LD H,$F0
    LD (HL),B
    SCF
    RET

q_physical_id:
    LD A,(q_slot)
    AND 32
    ADD A,A
    LD B,A
    LD A,(q_slot)
    AND 31
    ADD A,B
    LD B,A
    LD A,(p_fx_bank)
    CP 1
    LD A,19
    JR Z,.base
    LD A,9
.base:
    ADD A,B
    LD (p_w_tile),A
    RET

q_metadata:
    CALL q_physical_id
    LD A,(p_fx_bank)
    LD B,A
    LD A,(q_slot)
    AND 32
    LD A,B
    JR Z,.group
    ADD A,3
.group:
    LD (p_w_cachegroup),A
    CALL p_fixed_key_address
    LD (p_fx_meta),HL
    RET

; One physical mapping is rebuilt whenever the complete tuple changes.
; K's program-only cache cannot describe shared allocations.
q_decode:
    LD HL,p_tl_names
    LD B,q_codes/256
    DUP 30
    LD A,(HL)
    AND 15
    LD C,A
    LD A,(BC)
    LD (DE),A
    INC E
    LD A,(HL)
    DUP 4
    RRCA
    EDUP
    AND 15
    LD C,A
    LD A,(BC)
    LD (DE),A
    INC E
    INC L
    EDUP
    XOR A
    RET

; Only old ice ownership changes; the new fused cell still belongs to PAGE.
q_old_key:
    LD A,(p_w_cachegroup)
    PUSH AF
    CP 3
    JR C,.bank
    SUB 3
.bank:
    LD B,A
    LD HL,(p_w_name)
    BIT 6,(HL)
    LD A,B
    JR Z,.group
    ADD A,3
.group:
    LD (p_w_cachegroup),A
    CALL p_fast_old_key
    POP AF
    LD (p_w_cachegroup),A
    RET
q_end:
    ASSERT $ <= $AA68
