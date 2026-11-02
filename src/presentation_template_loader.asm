; A=root0..159, B=source-control delta, C=target Y0..185.
; Complete raw-floe IDs atE2A0 and packed30-byte program atE2C0.
; Unused ID bytes are retained. No canonical, descriptor or VRAM writes.
p_tl_count EQU $C2D3
p_tl_root EQU $C2EC
p_tl_delta EQU $C2ED
p_tl_y EQU $C2EE
p_tl_program EQU $C2F0
p_tl_delta_index EQU $C2F1
p_tl_keys EQU $E2A0
p_tl_names EQU $E2C0

p_template_load:
    CP 160
    JP NC,p_template_fail
    LD (p_tl_root),A
    LD A,C
    CP 186
    JP NC,p_template_fail
    LD (p_tl_y),A
    LD A,B
    LD (p_tl_delta),A
    LD D,A
    LD HL,p_template_deltas
    LD B,p_template_delta_count
    LD E,0
.delta:
    LD A,D
    CP (HL)
    JR Z,.found
    INC HL
    INC E
    DJNZ .delta
    JP p_template_fail
.found:
    LD A,E
    LD (p_tl_delta_index),A
    LD A,(p_tl_y)
    AND 7
    LD B,A
    ADD A,A
    ADD A,A
    ADD A,B
    LD L,A
    LD H,0
    DUP 5
    ADD HL,HL
    EDUP                    ;phase*160
    LD A,E
    DUP 4
    ADD A,A
    EDUP
    LD E,A
    LD D,0
    ADD HL,DE
    LD A,(p_tl_root)
    AND 15
    LD E,A
    ADD HL,DE
    ADD HL,HL
    LD DE,p_template_template_index_offset&$FFFF
    ADD HL,DE
    LD A,p_template_template_index_offset/65536
    ADC A,0
    CALL p_template_address
    RET C
    LD E,(HL)
    INC HL
    LD D,(HL)
    EX DE,HL
    LD DE,p_template_template_keys_offset&$FFFF
    ADD HL,DE
    LD A,p_template_template_keys_offset/65536
    ADC A,0
    CALL p_template_address
    RET C
    LD A,(HL)
    CP p_template_program_count
    JP NC,p_template_fail
    LD (p_tl_program),A
    INC HL
    LD A,(HL)
    OR A
    JP Z,p_template_fail
    CP 15
    JP NC,p_template_fail
    LD (p_tl_count),A
    ADD A,A
    LD C,A
    LD B,0
    INC HL
    LD DE,p_tl_keys
    LDIR
    LD A,(p_tl_program)
    LD L,A
    LD H,0
    DUP 5
    ADD HL,HL
    EDUP
    LD DE,p_template_template_names_offset&$FFFF
    ADD HL,DE
    LD A,p_template_template_names_offset/65536
    ADC A,0
    CALL p_template_address
    RET C
    LD DE,p_tl_names
    LD BC,30
    LDIR
    XOR A
    LD (p_tr_error),A
    RET
