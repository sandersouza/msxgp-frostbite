; Exact common-X shore query, including the original bear's initial fine motion.
cs_common:
    CP 9
    JP C,shore_edge_gate
    CP 153
    JP NC,shore_edge_gate
    LD D,A
    LD A,(t_enabled)
    OR A
    LD A,D
    JP Z,hazard_lookup
    LD (cf_dx),A
    LD A,L
    LD (cf_control),A
    LD A,(hazard_x)
    CP 15
    LD E,1
    JR NC,.body
    LD E,6
.body:
    ADD A,E
    CP 160
    JR C,.body_ready
    SUB 160
.body_ready:
    LD E,A
    LD A,(cf_dx)
    SUB E
    JR NC,.distance
    ADD A,160
.distance:
    CP 153
    JR C,.positive
    SUB 160
.positive:
    ADD A,7
    CP 23
    JR NC,.miss
    LD (cf_dx),A
    LD A,(hazard_y)
    ADD A,hazard_shore_min_y
    LD (cf_y),A
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
    JP cf_bear_contact
.miss:
    LD A,7
    RET
cs_end:
