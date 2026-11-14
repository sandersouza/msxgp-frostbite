; Called only for original common enemy profile: PX25..151 and one nearby copy.
ci_common:
    LD A,(t_enabled)
    OR A
    JR Z,.legacy
    LD A,L
    AND 1
    LD (cf_absolute_x),A
    LD A,L
    SRL A
    LD (cf_control),A
    LD A,(hazard_y)
    ADD A,hazard_row_min_y
    LD (cf_y),A
    LD A,(hazard_x)
    LD (cf_dx),A
    LD A,($C06E)
    LD (cf_pose),A
    LD A,($C06B)
    LD (cf_shift),A
    LD A,($C06C)
    AND 8
    DUP 3
    RRCA
    EDUP
    LD (cf_reflection),A
    JP cf_enemy_contact
.legacy:
    LD D,H
    LD E,L
    ADD HL,HL
    JP hazard_lookup_common+3
ci_common_end:
