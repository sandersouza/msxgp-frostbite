; Sparse exact-key P1 cells. No source state is written. First integration
; rebuilds the inactive page; dirty ownership comes after whole-pixel proof.
pfw_id EQU $C298
pfw_old EQU $E500
pfw_mask EQU $E510
pfw_kind EQU $C29A
pfw_memo EQU $E5A0
pfw_geo_valid EQU $C2C4
pfw_geo_family EQU $C2C5
pfw_geo_group EQU $C2C6
pfw_geo_variant EQU $C2C7

; Copies are separated by16/32source pixels: phase and descriptor IDs are
; identical even across the160pixel wrap. Pattern reads never modify IDs.
p_fast_geometry_lookup:
    LD D,A
    LD A,(pfw_geo_valid)
    OR A
    JR Z,.miss
    LD A,(pfw_geo_family)
    CP D
    JR NZ,.miss
    LD A,(pfw_geo_group)
    CP B
    JR NZ,.miss
    LD A,(pfw_geo_variant)
    CP C
    JR NZ,.miss
    XOR A
    RET
.miss:
    LD A,D
    LD (pfw_geo_family),A
    LD A,B
    LD (pfw_geo_group),A
    LD A,C
    LD (pfw_geo_variant),A
    XOR A
    LD (pfw_geo_valid),A
    LD A,D
    CALL presentation_geometry_lookup
    RET C
    LD A,1
    LD (pfw_geo_valid),A
    OR A
    RET

p_fast_clear_memo:
    LD HL,pfw_memo
    LD DE,pfw_memo+1
    LD BC,11
    LD (HL),255
    LDIR
    RET

p_fast_begin_page:
    LD HL,pf_refs
    LD A,(PAGE)
    OR A
    JR Z,.refs
    LD HL,pf_refs+192
.refs:
    LD D,H
    LD E,L
    INC DE
    LD BC,191
    LD (HL),0
    LDIR
    LD HL,pf_used
    LD A,(PAGE)
    OR A
    JR Z,.bitmap
    LD HL,pf_used+24
.bitmap:
    LD D,H
    LD E,L
    INC DE
    LD BC,23
    LD (HL),0
    LDIR
    RET

; Derive the cell and cache group from the target row/column, never source
; coordinates. The group's generation owns every dynamic name reference.
p_fast_cell:
    LD A,(p_w_top)
    LD L,A
    LD H,0
    DUP 5
    ADD HL,HL
    EDUP
    LD A,(p_w_col)
    LD E,A
    LD D,0
    ADD HL,DE
    LD A,(PAGE)
    OR A
    LD DE,$C800
    JR Z,.names
    LD D,$CD
.names:
    ADD HL,DE
    LD (p_w_name),HL
    LD A,(p_w_top)
    DUP 3
    SRL A
    EDUP
    LD B,A
    LD A,(PAGE)
    LD C,A
    ADD A,A
    ADD A,C
    ADD A,B
    LD (p_w_cachegroup),A
    RET

; All six bytes are retained before releasing the old cell owner.
p_fast_old_key:
    LD HL,(p_w_name)
    LD A,(HL)
    AND 63
    LD L,A
    LD H,0
    LD E,L
    LD D,H
    ADD HL,HL
    ADD HL,DE
    ADD HL,HL
    PUSH HL
    LD A,(p_w_cachegroup)
    ADD A,A
    LD E,A
    LD D,0
    LD HL,p_fast_key_roots
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    POP HL
    ADD HL,DE
    LD DE,pfw_old
    LD BC,6
    LDIR
    RET

; Construct/upload only on an exact-key MISS. Every intermediate fused cell
; drops its old owner before resolving, so an obsolete tile is safe to evict.
p_fast_put:
    LD HL,(p_w_name)
    LD A,(HL)
    CP 128
    JR NC,.resolve
    LD C,A
    LD A,(p_w_cachegroup)
    CALL p_fast_ref_drop
    JP C,p_world_fail
.resolve:
    LD A,(p_w_cachegroup)
    CALL p_fast_resolve
    JP C,p_world_fail
    LD (p_w_tile),A
    LD A,(pf_miss)
    CP 1
    JR NZ,.acquire
    LD A,(p_w_cachegroup)
    CP 3
    JR C,.bank
    SUB 3
.bank:
    CALL presentation_typed_construct
    JP C,p_world_fail
    LD A,(pt_error)
    OR A
    JP NZ,p_world_fail
    LD A,(p_w_tile)
    LD L,A
    LD H,0
    DUP 3
    ADD HL,HL
    EDUP
    LD A,(p_w_cachegroup)
    CP 3
    JR C,.vram_bank
    SUB 3
.vram_bank:
    DUP 3
    ADD A,A
    EDUP
    ADD A,$40
    ADD A,H
    LD H,A
    EX DE,HL
    PUSH DE
    LD HL,pt_tile
    LD B,8
    CALL vdp_write
    POP DE
    LD A,D
    ADD A,$20
    LD D,A
    LD HL,pt_tile+8
    LD B,8
    CALL vdp_write
.acquire:
    LD A,(p_w_tile)
    LD C,A
    LD A,(p_w_cachegroup)
    CALL p_fast_ref_add
    JP C,p_world_fail
    LD HL,(p_w_name)
    LD A,(p_w_tile)
    LD (HL),A
    RET

; Input DE=PGT ID. The source grammar guarantees a zero atlas ID is empty.
; Nonshared interior cells need no PGT read on an exact cache hit.
p_fast_world_tile:
    LD (pfw_id),DE
    LD A,D
    OR E
    RET Z
    CALL p_fast_cell
    LD A,(p_w_col)
    CP 2
    JR NZ,.old
    CALL p_fast_read_mask
    LD HL,pfw_mask
    LD B,8
    XOR A
.visible:
    OR (HL)
    INC HL
    DJNZ .visible
    RET Z
.old:
    LD HL,(p_w_name)
    LD A,(HL)
    CP 128
    JP NC,.mono_lookup
    CALL p_fast_old_key
    LD A,(p_w_family)
    CP 1
    JP NZ,p_world_fail
    CALL p_fast_read_mask
    LD A,(pfw_old+5)
    OR A
    JR Z,.old_mono
    CP 4
    JP C,p_fast_extend_literal
    CP 7
    JR Z,.already_union
    CP 8
    JP NZ,p_world_fail
.already_union:
    LD HL,(pfw_id)
    LD DE,(pfw_old)
    OR A
    SBC HL,DE
    RET Z
    LD HL,(pfw_id)
    LD DE,(pfw_old+2)
    OR A
    SBC HL,DE
    RET Z
    JP p_world_fail         ; no three distinct floe planes share a source cell
.old_mono:
    CALL p_fast_shared_kind
    LD (pfw_kind),A
    OR A
    JP Z,p_fast_union
    LD DE,(pfw_old)
    CALL presentation_geometry_pattern
    JP C,p_world_fail
    LD A,(p_w_col)
    CP 2
    JR NZ,.object_rows
    LD HL,$CC80
    LD B,8
.clip:
    LD A,(HL)
    AND 15
    LD (HL),A
    INC HL
    DJNZ .clip
.object_rows:
    LD A,(pfw_kind)
    DEC A
    LD A,($CC80)
    JR Z,.has_object
    LD A,(pfw_kind)
    CP 2
    LD A,($CC87)
    JR Z,.has_object
    LD A,($CC86)
    LD B,A
    LD A,($CC87)
    OR B
.has_object:
    OR A
    JP Z,p_fast_union
    LD A,(pfw_old+4)
    DUP 4
    RLCA
    EDUP
    LD B,A
    LD A,(p_w_color)
    OR B
    LD (pf_key+3),A
    XOR A
    LD (pf_key+4),A
    LD A,(pfw_kind)
    LD (pf_key+5),A
    CP 1
    JR NZ,.fused23
    LD A,($CC80)
    LD (pf_key),A
    LD A,(pfw_mask+7)
    LD (pf_key+1),A
    XOR A
    LD (pf_key+2),A
    JP p_fast_put
.fused23:
    CP 2
    JR NZ,.fused3
    LD A,(pfw_mask)
    LD (pf_key),A
    LD A,(pfw_mask+1)
    LD (pf_key+1),A
    LD A,($CC87)
    LD (pf_key+2),A
    JP p_fast_put
.fused3:
    LD A,(pfw_mask)
    LD (pf_key),A
    LD A,($CC86)
    LD (pf_key+1),A
    LD A,($CC87)
    LD (pf_key+2),A
    JP p_fast_put
.mono_lookup:
    LD B,A                  ;current static background identity
    LD A,(p_w_col)
    CP 3
    JR C,.not_retained       ;source left-edge mask has a separate constructor
    LD A,(p_w_index)
    ADD A,pfw_memo&255
    LD L,A
    LD H,pfw_memo/256
    LD A,(HL)
    CP 255
    JR Z,.not_retained
    LD (p_w_tile),A
    JP p_fast_put.acquire   ;already pinned by a nonoverlapping earlier copy
.not_retained:
    LD A,B
.mono:
    LD (pf_key+2),A
    LD DE,(pfw_id)
    LD (pf_key),DE
    XOR A
    LD (pf_key+5),A
    LD A,(p_w_col)
    CP 2
    LD A,0
    JR NZ,.clip_flag
    INC A
.clip_flag:
    LD (pf_key+3),A
    LD A,(p_w_color)
    LD (pf_key+4),A
    CALL p_fast_put
    LD A,(p_w_col)
    CP 3
    RET C
    LD A,(p_w_index)
    ADD A,pfw_memo&255
    LD L,A
    LD H,pfw_memo/256
    LD A,(p_w_tile)
    LD (HL),A
    RET

p_fast_read_mask:
    LD DE,(pfw_id)
    CALL presentation_geometry_pattern
    JP C,p_world_fail
    LD HL,$CC80
    LD DE,pfw_mask
    LD BC,8
    LDIR
    LD A,(p_w_col)
    CP 2
    RET NZ
    LD HL,pfw_mask
    LD B,8
.row:
    LD A,(HL)
    AND 15
    LD (HL),A
    INC HL
    DJNZ .row
    RET

p_fast_shared_kind:
    LD A,(p_w_coarse)
    OR A
    JR NZ,.coarse
    LD A,(p_w_top)
    CP 20
    LD A,1
    RET Z
    LD A,(p_w_top)
    CP 15
    LD A,2
    RET Z
    XOR A
    RET
.coarse:
    LD A,(p_w_top)
    CP 12
    LD A,3
    RET Z
    XOR A
    RET

p_fast_union:
    LD A,(pfw_old+4)
    LD B,A
    LD A,(p_w_color)
    CP B
    JP NZ,p_world_fail
    LD HL,(pfw_id)
    LD DE,(pfw_old)
    OR A
    SBC HL,DE
    RET Z
    LD HL,(pfw_id)
    JR NC,.ordered
    EX DE,HL
.ordered:
    LD (pf_key),DE
    LD (pf_key+2),HL
    LD A,B
    DUP 4
    RLCA
    EDUP
    OR 4
    LD (pf_key+4),A
    LD A,(p_w_col)
    CP 2
    LD A,7
    JR NZ,.kind
    INC A
.kind:
    LD (pf_key+5),A
    JP p_fast_put

p_fast_extend_literal:
    LD HL,pfw_old
    LD DE,pf_key
    LD BC,6
    LDIR
    LD A,(pf_key+3)
    AND 15
    LD B,A
    LD A,(p_w_color)
    CP B
    JP NZ,p_world_fail
    LD A,(pf_key+5)
    CP 1
    JR NZ,.other
    LD A,(pfw_mask+7)
    LD HL,pf_key+1
    OR (HL)
    LD (HL),A
    JP p_fast_put
.other:
    LD A,(pfw_mask)
    LD HL,pf_key
    OR (HL)
    LD (HL),A
    LD A,(pf_key+5)
    CP 2
    JP NZ,p_fast_put
    LD A,(pfw_mask+1)
    LD HL,pf_key+1
    OR (HL)
    LD (HL),A
    JP p_fast_put
