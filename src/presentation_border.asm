; Additive item3 view. Only retired/declared ranges are emitted.
    INCLUDE "symbols.inc"
    ORG ag_floe_end
ac_names:
    LD A,(PAGE)
    OR A
    LD HL,$C902             ;row8/column2, inactive CPU NAME buffer
    JR Z,.page
    LD H,$CE
.page:
    LD DE,32
    DUP 13
    LD (HL),128
    ADD HL,DE
    EDUP
    LD (HL),128             ;row21/column2
    JP p_template_upload_names_known
ac_names_code_end:
    ASSERT $ <= $F5D2
    DS $F5D2-$,0
ac_names_end:

    ORG x_eligible
ac_eligible:
    LD A,(p_w_mode)
    LD E,A
    LD D,0
    LD HL,x_counts
    ADD HL,DE
    LD A,(HL)
    LD (x_n),A
    LD B,A
    LD A,(p_sat_bytes)
    DEC A
    SRL A
    SRL A
    ADD A,B
    CP 32
    RET NC
    XOR A
    LD (x_clip),A
    LD A,(p_w_mode)
    ADD A,A
    ADD A,A
    LD E,A
    LD D,0
    LD HL,p_world_copies
    ADD HL,DE
    LD (x_offsets),HL
    ; B still contains the copy count; no need to reload disposable scratch.
.edges:
    LD A,(p_w_base)
    ADD A,(HL)
    CALL normalize_x
    OR A
    JR Z,.reject            ;raw160 must never become unclipped sentinel0
    CP 11
    JR C,.edge
    CP 153
    JR C,.edge_ready
.edge:
    LD C,A
    LD A,(p_w_mode)
    OR A
    JR NZ,.reject
    LD A,C
    LD (x_clip),A
.edge_ready:
    INC HL
    DJNZ .edges
    LD A,(x_n)              ;actual copies only; no obsolete mask rectangle
    LD C,A
    LD A,(p_s_static_start)
    LD B,A
    OR A
    JR Z,.accept
    LD HL,SAT
.scan:
    LD A,(HL)
    INC A
    LD E,A
    LD A,(p_w_y)
    SUB E
    JR NC,.after
    NEG
.after:
    CP 16
    JR NC,.next
    INC C
    LD A,C
    CP 5
    JR NC,.reject
.next:
    LD DE,4
    ADD HL,DE
    DJNZ .scan
    JR .accept
.reject:
    OR A
    RET
.accept:
    SCF
    RET
ac_eligible_code_end:
    ASSERT $ <= x_accepted
    DS x_accepted-$,0
ac_eligible_end:

    ORG x_clip_pattern
ac_clip:
    PUSH DE
    LD A,(x_clip)
    CP 11
    JR C,.left
    AND 7
    LD DE,x_right_masks
    JR .mask
.left:
    LD DE,ys_mask
.mask:
    ADD A,A
    LD L,A
    LD H,0
    ADD HL,DE
    LD D,(HL)
    INC HL
    LD E,(HL)
    LD HL,$C500
    LD B,8
.row:
    LD A,(HL)
    AND D
    LD (HL),A
    LD A,L
    ADD A,16
    LD L,A
    LD A,(HL)
    AND E
    LD (HL),A
    LD A,L
    SUB 15
    LD L,A
    DJNZ .row
    POP DE
    RET
ac_clip_code_end:
    ASSERT $ <= x_right_masks
    DS x_right_masks-$,0
ac_clip_end:

    ORG ys_mask
ac_left_masks:
    INCBIN "left-masks.bin"
    ASSERT $ <= ys_mask+28
    DS ys_mask+28-$,0
ac_left_masks_end:
