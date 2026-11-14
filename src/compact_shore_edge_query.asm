; Shore edge query; source A=playerX and HL=original alias/reflection mode.
se_query:
    LD A,($C066)             ; the resident mapper bridge consumes A
    LD B,A
    LD A,L
    LD (WS_INPUT_ORIGIN),A
    LD A,B
    LD (WS_INPUT_ORIGIN+1),A
    LD A,(hazard_x)
    LD (WS_INPUT_ORIGIN+2),A
    LD A,(hazard_y)
    LD (MP_INPUT_ORIGIN),A
    LD A,18
    LD (MP_INPUT_ORIGIN+1),A
    LD A,($C06E)
    LD (MP_INPUT_ORIGIN+2),A
    LD A,($C06B)
    LD (MP_INPUT_ORIGIN+3),A
    LD A,($C06C)
    AND 8
    DUP 3
    RRCA
    EDUP
    LD (MP_INPUT_ORIGIN+4),A
    LD HL,WS_OUTPUT_ORIGIN
    LD (MP_INPUT_ORIGIN+5),HL
    CALL ws_build
    JP mp_contact
se_end:
