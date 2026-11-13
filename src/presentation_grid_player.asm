; Optional view-only P0 translation, before original static cache/eligibility.
    INCLUDE "symbols.inc"
    ORG $6235
ag_player_entry:
    LD A,119
    CALL t_mapper
    JP ag_player
ag_player_exit:
    LD A,2
    CALL t_mapper
    JP ys_static
ag_bridge_end:
    ASSERT $ <= $6249

    ORG $BC91
ag_player:
    LD A,(p_w_coarse)
    ADD A,$BE
    LD H,A
    LD A,($F064)
    LD L,A
    LD A,(HL)
    OR A
    JP Z,ag_player_exit
    LD C,A
    LD A,(p_s_count)
    OR A
    JP Z,ag_player_exit
    LD B,A
    LD HL,SAT
    LD DE,4
.loop:
    LD A,(HL)
    ADD A,C
    LD (HL),A
    ADD HL,DE
    DJNZ .loop
    JP ag_player_exit
ag_player_end:
    ASSERT $ <= $BE00
    DS $BE00-$,0
ag_deltas:
    INCBIN "grid-deltas.bin"
ag_player_bank_end:
    ASSERT $ = $C000
