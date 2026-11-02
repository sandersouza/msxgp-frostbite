; Lossless fixed-template atlas. DE=logical pattern ID -> CC80..87, CF=error.
; Original128/C6 ABI, descriptor IDs/shape, heap and all VRAM remain untouched.
    INCLUDE "presentation_template.inc"
    ASSERT p_template_pattern_pairs_offset = 0
    ASSERT p_template_pattern_count <= 16384
    ASSERT p_template_half_count <= 16384
p_tr_halves EQU $C2D4
p_tr_error EQU $C2BC

p_template_floe_pattern:
    CALL p_template_floe_address
    RET C
    LD DE,$CC80
    DUP 8
    LDI                    ;fixed length; BC is scratch, no repeat test required
    EDUP
    OR A
    RET

; DE=raw floe ID -> mapped immutable eight-byte ROM mask at HL.
p_template_floe_address:
    ASSERT p_template_floe_patterns_offset/$4000 = 10
    ASSERT (p_template_floe_patterns_offset+p_template_floe_count*8-1)/$4000 = 11
    XOR A
    LD (p_tr_error),A
    LD A,D
    CP p_template_floe_count/256
    JR C,.valid
    JP NZ,p_template_fail
    LD A,E
    CP p_template_floe_count&255
    JP NC,p_template_fail
.valid:
    LD H,D
    LD L,E
    DUP 3
    ADD HL,HL
    EDUP
    LD DE,$8000+(p_template_floe_patterns_offset&$3FFF)
    ADD HL,DE
    LD A,13                ;logical asset bank10, physical bank13
    BIT 6,H
    JR Z,.mapped
    RES 6,H                ;C000..CE87 wraps to8000..8E87 in logical bank11
    LD A,253
.mapped:
    LD ($7000),A
    OR A
    RET

p_template_pattern:
    XOR A
    LD (p_tr_error),A
    LD A,D
    CP p_template_pattern_count/256
    JR C,.valid
    JP NZ,p_template_fail
    LD A,E
    CP p_template_pattern_count&255
    JP NC,p_template_fail
.valid:
    LD H,D
    LD L,E
    ADD HL,HL
    ADD HL,HL
    XOR A
    CALL p_template_address
    RET C
    LD DE,p_tr_halves
    LD BC,4
    LDIR
    LD HL,(p_tr_halves)
    LD DE,$CC80
    CALL p_template_half
    RET C
    LD HL,(p_tr_halves+2)
    LD DE,$CC84
    JP p_template_half

p_template_half:
    LD A,H
    CP p_template_half_count/256
    JR C,.valid
    JP NZ,p_template_fail
    LD A,L
    CP p_template_half_count&255
    JP NC,p_template_fail
.valid:
    PUSH DE
    ADD HL,HL
    ADD HL,HL
    LD DE,p_template_pattern_halves_offset&$FFFF
    ADD HL,DE
    LD A,p_template_pattern_halves_offset/65536
    ADC A,0
    CALL p_template_address
    POP DE
    RET C
    LD BC,4
    LDIR
    OR A
    RET

; A:HL logical byte offset -> mapped HL, exactly the declared14 asset banks.
p_template_address:
    LD B,A
    LD A,H
    RLCA
    RLCA
    AND 3
    LD C,A
    LD A,B
    ADD A,A
    ADD A,A
    OR C
    CP 14
    JR NC,p_template_fail
    CP 11
    JR C,.low
    ADD A,242
    JR .mapped
.low:
    ADD A,3
.mapped:
    LD ($7000),A
    LD A,H
    AND 63
    OR 128
    LD H,A
    OR A
    RET
p_template_fail:
    LD A,1
    LD (p_tr_error),A
    SCF
    RET
