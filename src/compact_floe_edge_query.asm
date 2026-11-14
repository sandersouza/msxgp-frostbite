; Composite electrical query. The common kernel supplies the fully proven bit6.
; Geometry compiler ignores only tags whose row evaluator is provably a miss.
cfe_contact:
    CALL cf_contact
    AND 64
    PUSH AF
    CALL ce_build_masks
    LD A,(ce_px)
    CP 8
    JR C,.left
    CP 153
    JR NC,.right
    LD A,255
    JR .clip_ready
.left:
    OR A
    JR Z,.clip_ready
    LD B,A
    LD A,1
.left_shift:
    ADD A,A
    DJNZ .left_shift
    DEC A
    JR .clip_ready
.right:
    SUB 152
    LD B,A
    LD A,255
.right_shift:
    ADD A,A
    DJNZ .right_shift
.clip_ready:
    LD C,A
    LD A,(cf_control)
    LD L,A
    LD H,0
    DUP 5
    ADD HL,HL
    EDUP
    LD D,H
    LD E,L
    ADD HL,HL
    ADD HL,HL
    ADD HL,DE
    LD A,(cf_dx)
    LD E,A
    LD D,0
    ADD HL,DE
    LD DE,$0300
    ADD HL,DE
    LD A,(HL)
    LD L,A
    LD H,0
    LD E,A
    LD D,0
    DUP 3
    ADD HL,HL
    EDUP
    OR A
    SBC HL,DE
    LD DE,$0A00
    ADD HL,DE
    EX DE,HL
    LD HL,CE_OUTPUT_ORIGIN+32
    LD B,7
.visible:
    LD A,(DE)
    AND C
    LD (HL),A
    INC DE
    INC HL
    DJNZ .visible
    LD A,(cf_y)
    LD (CE_CONTACT_INPUT_ORIGIN),A
    LD HL,cf_pose
    LD DE,CE_CONTACT_INPUT_ORIGIN+1
    LD BC,3
    LDIR
    CALL cec_contact
    LD B,A
    POP AF
    OR B
    RET
cfe_end:
