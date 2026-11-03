; A=first CID0..241, B=water CID, DE=one64-byte cache owner atDE00..DFFF.
; Expand E2C0's thirty packed bytes to sixty names; code0 is water, code1..15
; is first+code-1. The compiler separately guarantees its code1..14 grammar.
p_td_codes EQU $E600
p_template_decode_names:
    CP 242
    JP NC,.fail
    LD C,A
    LD A,D
    CP $DE
    JR Z,.address
    CP $DF
    JP NZ,.fail
.address:
    LD A,E
    AND 63
    JP NZ,.fail
    LD HL,p_td_codes
    LD (HL),B
    INC L
    LD A,C
    DUP 15
    LD (HL),A
    INC L
    INC A
    EDUP
    IFDEF WITH_PRESENTATION_TEMPLATES
    ; A complete fixed-role owner selects immutable low/high-byte pages.
    ; Retain the generic contract for other valid first/water combinations.
    PUSH BC
    LD A,D
    AND 1
    RLCA
    RLCA
    LD L,A
    LD A,E
    RLCA
    RLCA
    AND 3
    OR L
    ADD A,A
    OR p_td_roles&255
    LD L,A
    LD H,p_td_roles/256
    LD A,(HL)
    CP C
    JP NZ,.generic
    INC L
    LD A,(HL)
    CP B
    JP NZ,.generic
    LD A,L
    AND 14
    ADD A,($8000+(p_template_name_pairs_offset&$3FFF))/256
    LD H,A
    LD A,255
    LD ($7000),A
    POP BC
    LD BC,$E2C0
    DUP 30
    LD A,(BC)
    LD L,A
    LD A,(HL)
    LD (DE),A
    INC E
    INC H
    LD A,(HL)
    LD (DE),A
    INC E
    DEC H
    INC C
    EDUP
    XOR A
    RET
.generic:
    POP BC
    ENDIF
    LD HL,$E2C0
    LD B,p_td_codes/256
    DUP 30
    LD A,(HL)
    AND 15
    LD C,A
    LD A,(BC)
    LD (DE),A
    INC E
    LD A,(HL)
    DUP 4
    RRCA
    EDUP
    AND 15
    LD C,A
    LD A,(BC)
    LD (DE),A
    INC E
    INC L
    EDUP
    XOR A
    RET
.fail:
    SCF
    RET
    IFDEF WITH_PRESENTATION_TEMPLATES
    ASSERT (p_template_name_pairs_offset&511) = 0
    ASSERT p_template_name_pairs_offset/$4000 = 13
    ASSERT (p_template_name_pairs_offset+4095)/$4000 = 13
    ALIGN 16
p_td_roles:
    DB 25,129,9,129,35,130,19,130,89,129,73,129,99,130,83,130
    ENDIF
