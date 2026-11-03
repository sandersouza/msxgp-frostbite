; Finite original-derived geometry reader. Resident page1 code may switchpage2.
; Lookup input A=family(row/floe/bear), B=group, C=phase variant.
; Result: columns/rows, byte stride and up to12 uint16 pattern IDs in RAM.
    INCLUDE "presentation_geometry.inc"
p_geo_ids EQU $C2A0
p_geo_columns EQU $C2B8
p_geo_rows EQU $C2B9
p_geo_stride EQU $C2BA
p_geo_family EQU $C2BB
p_geo_error EQU $C2BC
p_geo_index EQU $C2BD
p_geo_bank EQU $C2C0
p_geo_remaining EQU $C2C3

presentation_geometry_lookup:
    LD (p_geo_family),A
    XOR A
    LD (p_geo_error),A
    LD A,1
    LD ($7000),A
    LD A,(p_geo_family)
    OR A
    JR Z,.row
    DEC A
    JR Z,.floe
    DEC A
    JP NZ,p_geo_fail
    LD A,B
    CP 16
    JP NC,p_geo_fail
    LD A,C
    CP 32
    JP NC,p_geo_fail
    LD HL,p_geo_bear_roots_data
    JR .root
.row:
    LD A,B
    CP 66
    JP NC,p_geo_fail
    LD A,C
    CP 128
    JP NC,p_geo_fail
    LD HL,p_geo_row_roots_data
    JR .root
.floe:
    IFDEF WITH_PRESENTATION_TEMPLATES
    JP p_geo_fail           ;complete templates own this family in this profile
    ELSE
    LD A,B
    CP 9
    JP NC,p_geo_fail
    LD A,C
    CP 128
    JP NC,p_geo_fail
    LD HL,p_geo_floe_roots_data
    ENDIF
.root:
    LD E,B
    LD D,0
    ADD HL,DE
    SLA E
    RL D
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    INC HL
    LD A,(HL)
    LD ($7000),A
    EX DE,HL
    LD E,C
    LD D,0
    SLA E
    RL D
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    LD A,D
    AND 15
    LD H,A
    LD L,E
    LD (p_geo_index),HL
    LD A,1
    LD ($7000),A
    LD A,D
    RRCA
    RRCA
    RRCA
    RRCA
    AND 15
    CP p_geo_class_count
    JP NC,p_geo_fail
    ADD A,A
    ADD A,A
    ADD A,A
    LD L,A
    LD H,0
    LD DE,p_geo_classes_data
    ADD HL,DE
    LD A,(HL)
    LD (p_geo_columns),A
    INC HL
    LD A,(HL)
    LD (p_geo_rows),A
    INC HL
    LD A,(HL)
    LD (p_geo_stride),A
    INC HL
    LD E,(HL)
    INC HL
    LD D,(HL)
    INC HL
    PUSH HL
    POP IX
    LD HL,(p_geo_index)
    OR A
    SBC HL,DE
    JP NC,p_geo_fail
    LD DE,(p_geo_index)
    LD HL,0
    LD A,(p_geo_stride)
.multiply:
    SRL A
    JR NC,.skip_add
    ADD HL,DE
.skip_add:
    SLA E
    RL D
    OR A
    JR NZ,.multiply
    LD E,(IX+0)
    LD D,(IX+1)
    ADD HL,DE
    LD A,(IX+2)
    ADC A,0
    ADD A,A
    ADD A,A
    LD B,A
    LD A,H
    RLCA
    RLCA
    AND 3
    OR B
    CALL p_geo_map
    RET C
    LD A,H
    AND 63
    OR 128
    LD H,A
    LD DE,p_geo_ids
    LD A,(p_geo_stride)
    LD C,A
    LD B,0
    LD A,H
    CP $BF
    JR NZ,.copy
    LD A,L
    ADD A,C
    JR NC,.copy
    LD A,L
    NEG
    LD C,A
    LD A,(p_geo_stride)
    SUB C
    LD (p_geo_remaining),A
    LDIR
    LD A,(p_geo_remaining)
    OR A
    RET Z
    LD A,(p_geo_bank)
    INC A
    CALL p_geo_map
    RET C
    LD HL,$8000
    LD A,(p_geo_remaining)
    LD C,A
    LD B,0
.copy:
    LDIR
    OR A
    RET

; DE=pattern ID; exactly eight source-derived expanded bytes to scratchCC80.
presentation_geometry_pattern:
    IFDEF WITH_PRESENTATION_TEMPLATES
    JP p_template_pattern
    ELSE
    LD A,D
    CP p_geo_pattern_count/256
    JR C,.valid
    JP NZ,p_geo_fail
    LD A,E
    CP p_geo_pattern_count&255
    JP NC,p_geo_fail
.valid:
    LD H,D
    LD L,E
    ADD HL,HL
    ADD HL,HL
    ADD HL,HL
    LD A,D
    RRCA
    RRCA
    RRCA
    AND 31
    CALL p_geo_map
    RET C
    LD A,H
    AND 63
    OR 128
    LD H,A
    LD DE,$CC80
    LD BC,8
    LDIR
    OR A
    RET
    ENDIF

; Logical assetbanks0..10 mapto3..13;11..13 mapto253..255.
p_geo_map:
    CP 14
    JR NC,p_geo_fail
    LD (p_geo_bank),A
    CP 11
    JR C,.low
    ADD A,242
    JR .write
.low:
    ADD A,3
.write:
    LD ($7000),A
    OR A
    RET
p_geo_fail:
    LD A,1
    LD (p_geo_error),A
    SCF
    RET
