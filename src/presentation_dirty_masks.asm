; Private entries for p_dirty_describe's four-row loops and coarse0/1 state.
; Geometry is constant; OR complete24-bit spans without recomputing row bits.
; Resident helpers preserve IX/IY histories and never switch the mapper.
p_template_dirty_object:
    LD HL,p_template_object_spans
    JR p_template_dirty_span
p_template_dirty_floe:
    LD HL,p_template_floe_spans
p_template_dirty_span:
    LD A,(p_w_coarse)
    ADD A,A
    ADD A,A
    LD E,A
    LD A,(p_w_row)
    ADD A,E
    LD E,A
    ADD A,A
    ADD A,E
    LD E,A
    LD D,0
    ADD HL,DE
    LD DE,p_fd_rows
    DUP 3,i
    LD A,(DE)
    OR (HL)
    LD (DE),A
    IF i < 2
    INC HL
    INC E
    ENDIF
    EDUP
    RET
p_template_object_spans:
    DB $00,$00,$18, $00,$80,$01, $00,$30,$00, $00,$06,$00
    DB $00,$00,$18, $00,$00,$01, $00,$30,$00, $00,$06,$00
p_template_floe_spans:
    DB $00,$00,$30, $00,$00,$06, $00,$C0,$00, $00,$08,$00
    DB $00,$00,$20, $00,$00,$06, $00,$C0,$00, $00,$18,$00
