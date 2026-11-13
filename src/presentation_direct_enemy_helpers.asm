; Resident gates: bank7 code cannot return directly through remapped ROM.
qe_init:
    LD HL,$E800
    LD DE,$E801
    LD BC,127
    LD (HL),255
    LDIR
    RET
qe_entry:
    LD A,7
    LD ($7000),A
    JP qe_primitive
qe_geometry:
    CALL p_fast_geometry_lookup
    PUSH AF
    LD A,7
    LD ($7000),A
    POP AF
    RET
qe_generate:
    CALL i_generate
    LD A,7
    LD ($7000),A
    RET
qe_fuse:
    CALL p_template_object_fuse
    PUSH AF
    LD A,7
    LD ($7000),A
    POP AF
    RET
