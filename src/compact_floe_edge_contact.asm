; Standalone accumulation over a qualified39-byte horizontal program.
; C7D0..C7D3 inputs: source Y(0 sentinel or45..77), pose, shift, reflection.
; C800..C81F four masks per row; C820..C826 seven clipped visible masks.
; Scratch C790..C798 and C7D4..C7D5. Program/input reads are immutable.
; Return A7/135 (bit7 only, shadow remains separately qualified).
; Preserve IX/IY/SP/IFF; bounded stack only besides declared scratch.
    IFNDEF CE_CONTACT_INPUT_ORIGIN
    DEFINE CE_CONTACT_INPUT_ORIGIN $C7D0
    ENDIF
    IFNDEF CE_ROW_INPUT_ORIGIN
    DEFINE CE_ROW_INPUT_ORIGIN $C790
    ENDIF
    IFNDEF CE_CONTACT_SCRATCH_ORIGIN
    DEFINE CE_CONTACT_SCRATCH_ORIGIN $C7D4
    ENDIF
    IFNDEF CE_OUTPUT_ORIGIN
    DEFINE CE_OUTPUT_ORIGIN $C800
    ENDIF
cec_contact:
    LD A,(CE_CONTACT_INPUT_ORIGIN+0)
    OR A
    JR NZ,.start
    LD A,7
    RET
.start:
    PUSH IY
    LD IY,CE_OUTPUT_ORIGIN
    LD HL,CE_CONTACT_INPUT_ORIGIN+1
    LD DE,CE_ROW_INPUT_ORIGIN+1
    LD BC,3
    LDIR
    LD A,(CE_CONTACT_INPUT_ORIGIN+0)
    SUB 50
    LD (CE_CONTACT_SCRATCH_ORIGIN+0),A
    XOR A
    LD (CE_CONTACT_SCRATCH_ORIGIN+1),A
.row:
    LD A,(CE_CONTACT_SCRATCH_ORIGIN+0)
    LD (CE_ROW_INPUT_ORIGIN+0),A
    LD A,(IY+0)
    LD (CE_ROW_INPUT_ORIGIN+4),A
    LD A,(IY+1)
    LD (CE_ROW_INPUT_ORIGIN+5),A
    LD A,(IY+2)
    LD (CE_ROW_INPUT_ORIGIN+6),A
    LD A,(IY+3)
    LD (CE_ROW_INPUT_ORIGIN+7),A
    LD A,(CE_CONTACT_SCRATCH_ORIGIN+1)
    CP 7
    LD A,0
    JR NC,.visible_ready
    LD A,(CE_CONTACT_SCRATCH_ORIGIN+1)
    LD L,A
    LD H,0
    LD DE,CE_OUTPUT_ORIGIN+32
    ADD HL,DE
    LD A,(HL)
.visible_ready:
    LD (CE_ROW_INPUT_ORIGIN+8),A
    CALL ce_test_row
    BIT 7,A
    JR NZ,.done
    LD DE,4
    ADD IY,DE
    LD A,(CE_CONTACT_SCRATCH_ORIGIN+0)
    DEC A
    LD (CE_CONTACT_SCRATCH_ORIGIN+0),A
    LD A,(CE_CONTACT_SCRATCH_ORIGIN+1)
    INC A
    LD (CE_CONTACT_SCRATCH_ORIGIN+1),A
    CP 8
    JR C,.row
    LD A,7
.done:
    POP IY
    RET
cec_end:
