; Fresh Frostbite logical-CPU helpers. BC=X/Y, E=6502 carry, A=6502 A.
; Z80 S/Z retain source N/Z; source V and D/I/B/unused live independently.
core_v EQU $C600
core_mode EQU $C601
core_sp EQU $C602
core_bitbits EQU $C603
core_lhs EQU $C604
core_rhs EQU $C605
core_low EQU $C606
core_high EQU $C607
core_half EQU $C608
core_result EQU $C609
core_cin EQU $C60A
core_stack_high EQU $C60B

core_zp_read:
    BIT 7,A
    JR NZ,core_zp_ram
    AND 15
    LD L,A
    LD H,$C3
    RET
core_zp_write:
    BIT 7,A
    JR NZ,core_zp_ram
    AND 63
    LD L,A
    LD H,$C7
    RET
core_zp_ram:
    AND 127
    LD L,A
    LD H,$C0
    RET

core_address_read:
    BIT 4,H
    JR NZ,core_address_rom
    BIT 7,L
    LD A,L
    JP Z,core_zp_read
    BIT 1,H
    JP Z,core_zp_ram
    AND 7
    ADD A,$40
    LD L,A
    LD H,$C3
    RET
core_address_write:
    BIT 4,H
    JP NZ,core_fault
    BIT 7,L
    LD A,L
    JP Z,core_zp_write
    BIT 1,H
    JP Z,core_zp_ram
    AND 31
    ADD A,$40
    LD L,A
    LD H,$C7
    RET
core_address_rom:
    LD A,H
    AND 15
    CP 12
    JP C,core_fault
    AND 3
    ADD A,original_data/256
    LD H,A
    RET
core_fault:
    DI
    LD A,$EE
    LD ($C6FD),A
    JP core_fault

core_push_return:
    PUSH AF
    PUSH DE
    LD D,H
    LD E,L
    LD A,(core_sp)
    AND 127
    LD L,A
    LD H,$C0
    LD (HL),D
    LD A,(core_sp)
    DEC A
    LD (core_sp),A
    AND 127
    LD L,A
    LD (HL),E
    LD A,(core_sp)
    DEC A
    LD (core_sp),A
    POP DE
    POP AF
    RET
core_return:
    INC IX
    INC IX
    RET

; Partial evaluation of an exact LDA0/STA0,X/TXS/INX/BNE loop. All256 starting
; X values are checked against the original. Separate write mirrors stay separate.
core_clear:
    PUSH BC
    PUSH DE
    LD A,B
    BIT 7,A
    JR NZ,.ram_only
    CP 64
    JR NC,.partial_io
    XOR A
.partial_io:
    AND 63
    LD L,A
    LD H,$C7
    LD A,64
    SUB L
    LD C,A
    LD B,0
    CALL .zero
    LD HL,$C000
    LD BC,128
    JR .clear_ram
.ram_only:
    AND 127
    LD L,A
    LD H,$C0
    LD A,128
    SUB L
    LD C,A
    LD B,0
.clear_ram:
    CALL .zero
    POP DE
    POP BC
    LD B,0
    LD IX,$C07F
    LD A,128
    LD (core_stack_high),A
    XOR A
    RET
.zero:
    LD (HL),0
    DEC BC
    LD A,B
    OR C
    RET Z
    LD D,H
    LD E,L
    INC DE
    LDIR
    RET

core_bit:
    LD A,H
    AND $C0
    LD (core_bitbits),A
    AND $40
    LD (core_v),A
    LD A,D
    AND H
    PUSH AF
    POP HL
    RES 7,L
    LD A,(core_bitbits)
    BIT 7,A
    JR Z,.positive
    SET 7,L
.positive:
    PUSH HL
    POP AF
    LD A,D
    RET

core_capture_v:
    PUSH AF
    POP HL
    LD A,L
    AND 4
    RLCA
    RLCA
    RLCA
    RLCA
    LD (core_v),A
    PUSH HL
    POP AF
    RET

core_adc:
    LD D,A
    LD A,(core_mode)
    BIT 3,A
    LD A,D
    JP NZ,core_adc_decimal
    SRL E
    ADC A,H
    LD E,0
    JR NC,.no_carry
    LD E,1
.no_carry:
    JP core_capture_v

core_sbc:
    LD D,A
    LD A,(core_mode)
    BIT 3,A
    LD A,D
    JP NZ,core_sbc_decimal
    SRL E
    CCF
    SBC A,H
    LD E,0
    JR C,.borrow
    LD E,1
.borrow:
    JP core_capture_v

; NMOS ADC: N/Z/V use the unadjusted nibble ALU result, not final BCD A.
core_adc_decimal:
    LD (core_lhs),A
    LD A,H
    LD (core_rhs),A
    AND 15
    LD L,A
    LD A,D
    AND 15
    ADD A,L
    ADD A,E
    LD (core_low),A
    CP 10
    LD A,0
    JR C,.low_ok
    INC A
.low_ok:
    LD (core_half),A
    LD A,D
    RRCA
    RRCA
    RRCA
    RRCA
    AND 15
    LD L,A
    LD A,(core_rhs)
    RRCA
    RRCA
    RRCA
    RRCA
    AND 15
    ADD A,L
    LD L,A
    LD A,(core_half)
    ADD A,L
    LD (core_high),A
    CP 10
    LD E,0
    JR C,.high_ok
    LD E,1
.high_ok:
    LD A,(core_high)
    AND 15
    RLCA
    RLCA
    RLCA
    RLCA
    LD H,A
    LD A,(core_low)
    AND 15
    OR H
    LD (core_result),A
    LD A,(core_lhs)
    LD H,A
    LD A,(core_rhs)
    XOR H
    CPL
    LD L,A
    LD A,(core_result)
    XOR H
    AND L
    AND $80
    RRCA
    LD (core_v),A
    LD A,(core_result)
    OR A
    PUSH AF
    LD A,(core_low)
    AND 15
    LD L,A
    LD A,(core_half)
    OR A
    LD A,L
    JR Z,.low_adjusted
    ADD A,6
    AND 15
.low_adjusted:
    LD L,A
    LD A,(core_high)
    CP 10
    LD A,(core_high)
    JR C,.high_adjusted
    ADD A,6
.high_adjusted:
    AND 15
    RLCA
    RLCA
    RLCA
    RLCA
    OR L
    LD D,A
    POP AF
    LD A,D
    RET

; NMOS SBC: flags are binary; low/high decimal borrow corrections are separate.
core_sbc_decimal:
    LD (core_lhs),A
    LD A,H
    LD (core_rhs),A
    LD A,E
    LD (core_cin),A
    LD A,D
    SRL E
    CCF
    SBC A,H
    LD E,0
    JR C,.binary_borrow
    LD E,1
.binary_borrow:
    CALL core_capture_v
    LD (core_result),A
    PUSH AF
    LD A,(core_rhs)
    CPL
    AND 15
    LD L,A
    LD A,(core_lhs)
    AND 15
    ADD A,L
    LD L,A
    LD A,(core_cin)
    ADD A,L
    CP 16
    LD A,0
    JR C,.low_borrow
    INC A
.low_borrow:
    LD (core_half),A
    LD A,(core_rhs)
    CPL
    RRCA
    RRCA
    RRCA
    RRCA
    AND 15
    LD L,A
    LD A,(core_lhs)
    RRCA
    RRCA
    RRCA
    RRCA
    AND 15
    ADD A,L
    LD L,A
    LD A,(core_half)
    ADD A,L
    CP 16
    LD A,(core_result)
    JR NC,.high_adjusted
    ADD A,$A0
.high_adjusted:
    AND $F0
    LD H,A
    LD A,(core_result)
    LD L,A
    LD A,(core_half)
    OR A
    LD A,L
    JR NZ,.low_adjusted
    ADD A,10
.low_adjusted:
    AND 15
    OR H
    LD D,A
    POP AF
    LD A,D
    RET
