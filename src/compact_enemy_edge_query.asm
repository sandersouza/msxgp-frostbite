; Ordinary exceptional-X query. Source IX identifies the selected hazard lane.
he_query:
    LD A,(hazard_y)
    LD (MP_INPUT_ORIGIN),A
    LD A,8
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
    LD HL,HP_OUTPUT_ORIGIN
    LD (MP_INPUT_ORIGIN+5),HL
    LD A,($C066)
    LD (HP_INPUT_ORIGIN),A
    LD A,(IX+49)
    LD (HP_INPUT_ORIGIN+1),A
    LD A,(IX+53)
    LD (HP_INPUT_ORIGIN+2),A
    LD A,(IX+0)
    LD E,A
    LD D,0
    LD HL,hazard_shape_index
    ADD HL,DE
    LD A,(HL)
    CP 33
    JP NC,core_fault
    LD (HP_INPUT_ORIGIN+3),A
    LD A,(IX-18)
    RLCA
    AND 1
    LD (HP_INPUT_ORIGIN+4),A
    CALL hp_build
    JP mp_contact
he_end:
