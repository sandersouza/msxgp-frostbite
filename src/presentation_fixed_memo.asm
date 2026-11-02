; Earlier-copy fast path; no source or tile mutation.
p_fast_try_memo:
    LD A,(p_w_top)
    CP 8
    JR NC,.position
    LD A,(p_w_col)
    CP 3
    RET C
.position:
    LD A,(p_w_index)
    ADD A,pfw_memo&255
    LD L,A
    LD H,pfw_memo/256
    LD A,(HL)
    CP 255
    JR Z,.miss
    LD HL,(p_w_name)
    LD (HL),A               ;earlier same primitive published this fixed role
    PUSH AF
    LD A,(p_w_family)
    OR A
    CALL Z,p_fixed_mark_object ;each copy has its own future fusion ordinal
    POP AF
    OR A
    RET
.miss:
    SCF
    RET
