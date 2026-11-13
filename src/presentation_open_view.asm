; Open edge: no black NAME stamps; keep qualified warm header omission.
 INCLUDE "symbols.inc"
 ORG ac_names
aq_names:
 CALL aq_visible_credit
 LD HL,(hy_lo)
 LD A,L
 XOR 14
 OR H
 JR NZ,.publish
 LD A,(p_fd_rows)
 INC A
 JR Z,.publish
 AND 7
 JR NZ,.publish
 LD A,(p_fd_count)
 SUB 3
 LD (p_fd_count),A
 CALL NZ,prefix_compact
.publish:
 JP p_template_upload_names_known
aq_credit:
 LD A,(PAGE)
 OR A
 LD HL,$CAEF
 JR Z,.page
 LD H,$CF
.page:
 LD A,134
 LD B,9
.tile:
 LD (HL),A
 INC L
 INC A
 DJNZ .tile
 RET
aq_names_end:
 ASSERT $ <= $F5B8
 DS $F5B8-$,0
aq_names_padded_end:
 ORG $6610
aq_unmasked_return:
 RET
aq_visible_credit:
 LD A,($F03F)
 RLA
 RET C
 LD A,(p_fd_rows+2)
 RLCA
 RET NC
 JP aq_credit
aq_visible_credit_end:
 ASSERT $ <= $6623
 DS $6623-$,0
aq_visible_credit_padded_end:
 ORG w_player_setup
aq_player_setup:
 LD A,w_palette/256
 LD (w_color_page),A
 JP p_player_cache_lookup
aq_enemy_x:
 CP 160
 JR C,.normalized
 SUB 160
.normalized:
 OR A
 RET NZ
 POP HL
 JP $F7B1
 ASSERT $ <= $ECC0
 DS $ECC0-$,0
aq_player_setup_end:
 ORG ah_end
aq_boot:
 CALL t_fill
 LD HL,aq_patterns
 LD DE,$5000+134*8
 LD B,72
 CALL vdp_write
 LD A,$F1
 LD DE,$7000+134*8
 LD B,72
 JP t_fill
aq_patterns:
 INCBIN "credit-patterns.bin"
aq_boot_end:
 ASSERT $ <= $C000

    ORG x_eligible
aq_eligible:
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
    LD HL,p_world_copies
    ADD HL,DE
    LD (x_offsets),HL
    ; B still contains the copy count; no need to reload disposable scratch.
.edges:
    LD A,(p_w_base)
    ADD A,(HL)
    CALL normalize_x
    DEC A
    CP 157
    JR NC,.reject          ;hide X0; wrapped X158/159 need native pixels
    INC A
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
aq_eligible_code_end:
    ASSERT $ <= x_accepted
    DS x_accepted-$,0
aq_eligible_end:
