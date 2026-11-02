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
