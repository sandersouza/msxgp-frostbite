; A original footer tile ID0..187. Exact16-byte shared scratch atC520.
; Immutable unused PGT/CGT pair addresses; original sprite/name tables untouched.
; Both entries preserve IX/IY; t_restore_interrupts retains the platform policy.
vp_address:
    LD L,A
    LD H,0
    ADD HL,HL
    LD DE,vp_directory
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    RET
vp_store:
    CALL vp_address
    SET 6,D
    LD HL,$C520
    LD B,8
    CALL vp_write_half
    LD A,D
    ADD A,$20
    LD D,A
    LD B,8
    JP vp_write_half
vp_write_half:
    DI
    LD A,E
    OUT ($99),A
    LD A,D
    OUT ($99),A
    CALL t_restore_interrupts
    LD C,$98
.loop:
    OUTI
    JP NZ,.loop
    RET
vp_read:
    CALL vp_address
    LD HL,$C520
    CALL vp_read_half
    LD A,D
    ADD A,$20
    LD D,A
    LD HL,$C528
    CALL vp_read_half
    LD HL,$C520
    RET
vp_read_half:
    DI
    LD A,E
    OUT ($99),A
    LD A,D
    OUT ($99),A
    CALL t_restore_interrupts
    LD B,8
.loop:
    IN A,($98)
    LD (HL),A
    INC HL
    DJNZ .loop
    RET
vp_end:
