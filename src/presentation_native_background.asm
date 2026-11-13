    INCLUDE "symbols.inc"
    ORG $F900
xh_collect:
    LD DE,p_fd_list
    CALL xh_collect_resume
    PUSH AF
    PUSH BC
    PUSH DE
    PUSH HL
    LD DE,$FC00
    DUP 3,group
    LD A,(p_fd_rows+group)
    LD C,A
    DUP 8
    SRL C
    SBC A,A
    AND 1
    LD (DE),A
    INC E
    EDUP
    EDUP
    POP HL
    POP DE
    POP BC
    POP AF
    RET
xh_dirty:
    CP 24
    JR NC,.fallback
    PUSH HL
    LD L,A
    LD H,$FC
    LD A,(HL)
    OR A
    POP HL
    RET
.fallback:
    PUSH BC
    PUSH DE
    PUSH HL
    JP xh_dirty_resume

xh_bg:
    LD A,(p_fd_count)
    OR A
    RET Z
    LD A,1
    CALL t_mapper
    LD A,(PAGE)
    OR A
    LD A,$C8
    JR Z,.page
    LD A,$CD
.page:
    LD (xh_page),A
    LD A,(p_bg_theme)
    ADD A,A
    LD L,A
    LD H,0
    LD DE,p_bg_roots
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    LD (p_fd_program),DE
    LD A,(p_bg_profile)
    AND 28
    LD B,A
    LD A,(p_bg_theme)
    AND 1
    ADD A,A
    OR B
    LD L,A
    LD H,0
    LD DE,p_bg_gradient_data
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    LD (xh_gradient),DE
    LD IY,p_fd_list
    LD A,(p_fd_count)
    LD B,A
.row:
    PUSH BC
    LD A,(IY)
    INC IY
    LD (p_fd_loop),A
    CALL p_template_background_covered
    JR C,.next
    LD A,(p_bg_profile)
    CP 32
    LD DE,$8080
    LD C,128
    JR Z,.fill
    LD A,(p_fd_loop)
    LD E,A
    ADD A,A
    ADD A,E
    LD E,A
    LD D,0
    LD HL,(p_fd_program)
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    INC HL
    LD C,(HL)
    LD A,(p_fd_loop)
    CP 3
    JR NZ,.fill
    LD A,(xh_gradient)
    LD D,A
    LD A,(xh_gradient+1)
    LD C,A
.fill:
    LD A,(p_fd_loop)
    LD L,A
    LD H,0
    DUP 5
    ADD HL,HL
    EDUP
    LD A,(xh_page)
    ADD A,H
    LD H,A
    LD (HL),128
    INC L
    LD (HL),E
    INC L
    LD (HL),D
    INC L
    LD A,C
    DUP 28
    LD (HL),A
    INC L
    EDUP
    LD (HL),128
.next:
    POP BC
    DEC B
    JP NZ,.row
    RET
xh_page EQU $E86C
xh_gradient EQU $E86D
xh_igloo_bottom:
    LD (pfh_bottom),A
    LD B,A
    LD A,(p_h_bits)
    OR B
    JP Z,xh_igloo_next
    JP xh_igloo_continue
xh_igloo_end:
    ASSERT $ <= $FB60
