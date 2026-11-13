; Standalone accumulation over a qualified39-byte horizontal program.
; C7D0..C7D3 inputs: source Y(0 sentinel or45..77), pose, shift, reflection.
; C800..C81F four masks per row; C820..C826 seven clipped visible masks.
; Scratch C790..C798 and C7D4..C7D5. Program/input reads are immutable.
; Return A7/135 (bit7 only, shadow remains separately qualified).
; Preserve IX/IY/SP/IFF; bounded stack only besides declared scratch.
cec_contact:
    LD A,($C7D0)
    OR A
    JR NZ,.start
    LD A,7
    RET
.start:
    PUSH IY
    LD IY,$C800
    LD HL,$C7D1
    LD DE,$C791
    LD BC,3
    LDIR
    LD A,($C7D0)
    SUB 50
    LD ($C7D4),A
    XOR A
    LD ($C7D5),A
.row:
    LD A,($C7D4)
    LD ($C790),A
    LD A,(IY+0)
    LD ($C794),A
    LD A,(IY+1)
    LD ($C795),A
    LD A,(IY+2)
    LD ($C796),A
    LD A,(IY+3)
    LD ($C797),A
    LD A,($C7D5)
    CP 7
    LD A,0
    JR NC,.visible_ready
    LD A,($C7D5)
    LD L,A
    LD H,0
    LD DE,$C820
    ADD HL,DE
    LD A,(HL)
.visible_ready:
    LD ($C798),A
    CALL ce_test_row
    BIT 7,A
    JR NZ,.done
    LD DE,4
    ADD IY,DE
    LD A,($C7D4)
    DEC A
    LD ($C7D4),A
    LD A,($C7D5)
    INC A
    LD ($C7D5),A
    CP 8
    JR C,.row
    LD A,7
.done:
    POP IY
    RET
cec_end:
