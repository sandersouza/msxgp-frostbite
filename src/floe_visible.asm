; Exact F019→F476 visible reduction. Source gameplay remains the native core.
; Literal-view contact tables come from complete original-clock observation.
; WITH_HAZARDS adds the actual odd/shore source channels and compact row reader.
floe_profile EQU $C780       ; word address, byte bank
floe_baseptr EQU $C783       ; word resident base-shadow row
floe_viewbyte EQU $C785
floe_viewmask EQU $C786

visible_step:
    LD A,($C045)
    BIT 7,A
    JR Z,.palette
    LD A,($C04D)
    LD ($C053),A
    XOR A
    LD ($C01E),A
.palette:
    LD A,($C045)
    RLCA
    LD A,($C04B)
    JR C,.night
    AND 4
    JR NZ,.night
    LD HL,$0A84
    LD D,4
    JR .colors
.night:
    LD HL,$0280
    LD D,12
.colors:
    LD ($C03B),HL
    LD A,($C04B)
    CP 3
    JR NC,.ground
    LD D,H
.ground:
    LD A,D
    LD ($C03D),A
    LD A,($C04D)
    CP 15
    LD A,H
    JR NZ,.door
    XOR A
    BIT 2,L                ; day BB84 / night BB80
    JR NZ,.door
    LD A,($C001)
    LD D,A
    LD A,($C002)
    XOR D
    AND 8
    LD A,0
    JR NZ,.door
    LD A,56
.door:
    LD ($C03E),A
    LD HL,floe_final_pointers
    LD DE,$C005
    LD BC,12
    LDIR
    LD HL,$FFFF
    LD ($C038),HL
    XOR A
    LD ($C03A),A
    LD A,($C03F)
    BIT 7,A
    JR Z,.contacts
    LD HL,$C030
    LD DE,$C031
    LD BC,7
    LD (HL),7
    LDIR
    JR .footer
.contacts:
    CALL floe_acquire
    IFDEF WITH_HAZARDS
    CALL hazard_acquire
    ENDIF
.footer:
    LD A,2
    LD ($7000),A
    LD A,(original_data+$3B8)
    LD ($C078),A
    LD HL,$FFFF
    LD ($C079),HL
    LD HL,$F430
    LD ($C07E),HL
    LD A,($C046)
    AND 31
    SUB 12
    JR C,.phase_zero
    CP 8
    JR C,.phase
    LD A,7
    JR .phase
.phase_zero:
    XOR A
.phase:
    LD E,A
    LD D,0
    LD HL,original_data+$388
    ADD HL,DE
    LD B,(HL)
    LD C,A
    DEC C
    LD ($C6F2),BC
    LD HL,$0080             ; source A0, N1/Z0; source C is separate
    LD ($C6F0),HL
    LD A,1
    LD ($C6F4),A
    XOR A
    LD (core_v),A
    RET

floe_acquire:
    LD A,($C01D)
    RRCA
    RRCA
    RRCA
    RRCA
    LD L,A
    LD A,($C01C)
    OR L
    LD L,A
    LD H,floe_control_index/256
    LD A,(HL)
    CP 255
    JP Z,core_fault
    ADD A,A
    ADD A,A
    LD E,A
    LD D,0
    LD HL,floe_control_pointers
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    INC HL
    LD A,(HL)
    INC HL
    LD H,(HL)
    LD L,A
    LD (floe_baseptr),HL
    EX DE,HL
    LD A,($C066)
    CP 160
    JP NC,core_fault
    LD E,A
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
    LD (floe_profile),DE
    LD (floe_profile+2),A
    LD A,($C06E)
    CP 6
    JP NC,core_fault
    ADD A,A
    LD D,A
    ADD A,A
    ADD A,A
    ADD A,A
    ADD A,A
    ADD A,D
    ADD A,D
    ADD A,D                ; pose*38
    LD D,A
    LD A,($C06B)
    CP 19
    JP NC,core_fault
    ADD A,A
    ADD A,D
    LD D,A
    LD A,($C06C)
    AND 8
    RRCA
    RRCA
    RRCA
    OR D
    LD C,A
    AND 7
    LD E,A
    LD HL,floe_bit_masks
    LD D,0
    ADD HL,DE
    LD A,(HL)
    LD (floe_viewmask),A
    LD A,C
    RRCA
    RRCA
    RRCA
    AND 31
    LD (floe_viewbyte),A
    LD IX,$C01F
    LD IY,$C030
    LD B,123
    CALL floe_row
    INC IX
    INC IY
    INC IY
    LD B,97
    CALL floe_row
    INC IX
    INC IY
    INC IY
    LD B,71
    CALL floe_row
    INC IX
    INC IY
    INC IY
    LD B,45
    JP floe_row

floe_row:
    LD (IY+1),7
    LD A,(IX+0)
    CP 160
    JP NC,core_fault
    LD E,A
    LD D,0
    LD HL,(floe_baseptr)
    ADD HL,DE
    LD A,(HL)
    LD (IY+0),A
    LD A,($C064)
    SUB B
    RET C
    CP 33
    RET NC
    INC A                 ; Y0 sentinel is index0, near45..77 are indices1..33
    LD L,A
    LD H,0
    LD D,H
    LD E,L
    ADD HL,HL
    ADD HL,DE
    LD DE,(floe_profile)
    ADD HL,DE
    LD A,(floe_profile+2)
    LD ($7000),A
    CALL floe_deref
    LD A,($C066)
    LD B,A
    LD A,(IX+0)
    SUB B
    JR NC,.relative
    ADD A,160
.relative:
    LD E,A
    IFDEF WITH_HAZARDS
    CALL contact_compact
    LD (IY+0),A
    RET
    ELSE
    LD D,0
    ADD HL,DE
    SLA E
    RL D
    ADD HL,DE
    CALL floe_deref
    LD A,(floe_viewbyte)
    LD E,A
    LD D,0
    ADD HL,DE
    LD A,(floe_viewmask)
    AND (HL)
    LD C,7
    JR Z,.shadow
    SET 7,C
.shadow:
    LD DE,29
    ADD HL,DE
    LD A,(floe_viewmask)
    AND (HL)
    JR Z,.store
    SET 6,C
.store:
    LD (IY+0),C
    RET
    ENDIF

floe_deref:
    LD E,(HL)
    INC HL
    LD D,(HL)
    INC HL
    LD A,(HL)
    LD ($7000),A
    EX DE,HL
    RET

floe_final_pointers:
    DB $90,$FF,$98,$FF,$A0,$FF,$A8,$FF,$B0,$FF,$B8,$FF
floe_bit_masks:
    DB 1,2,4,8,16,32,64,128
    IFDEF WITH_HAZARDS
    INCLUDE "hazard_contacts.asm"
    ENDIF
    INCLUDE "contact_resident.inc"
