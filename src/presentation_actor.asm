; Private mono-actor entry. The source primitive driver/p_fast_cell already
; selected PAGE/group and bounded bear/object grid row/column. All public
; resolver checks remain intact. Fixed IDs, complete tile IO and fusion marks
; are exactly those of the generic resolver.
p_fixed_put_actor:
    LD A,(p_w_top)
    CP 24
    JP NC,p_fixed_fail
    ADD A,A
    ADD A,A
    LD B,A
    LD A,(PAGE)
    OR A
    LD A,B
    JR Z,.context
    ADD A,96
.context:
    LD L,A
    LD H,p_actor_contexts/256
    LD A,(HL)
    CP 3
    JP NC,p_fixed_fail
    LD (p_fx_bank),A
    INC L
    LD A,(HL)
    LD B,A
    LD A,(p_w_line)
    LD C,A
    ADD A,B
    LD (p_w_tile),A
    INC L
    LD E,(HL)
    INC L
    LD D,(HL)
    LD A,C
    ADD A,A
    LD L,A
    ADD A,A
    ADD A,L
    LD L,A
    LD H,0
    ADD HL,DE
    CALL p_fixed_resolve_known
    RET C
    JP p_fixed_put.publish
    MACRO p_actor_context gen, bank, base
    DB bank,base+gen*64
    DW $D000+(gen*3+bank)*384+base*6
    ENDM
    ALIGN 256
p_actor_contexts:
    DUP 2,page
    DS 24,255
    p_actor_context page,0,0
    p_actor_context page,0,4
    p_actor_context page,1,0
    p_actor_context page,1,4
    p_actor_context page,1,7
    DS 4,255
    p_actor_context page,1,10
    p_actor_context page,1,13
    DS 4,255
    p_actor_context page,1,16
    p_actor_context page,2,0
    DS 8,255
    p_actor_context page,2,3
    p_actor_context page,2,6
    DS 12,255
    EDUP
