; Standard MSX1 ports, per MSX Technical Data Book sections1.4/1.7.12.
; Fresh direct-I/O sampler; raw mapping audited from the supplied Seaquest
; adapter, with all state addresses/source-phase assumptions replaced.
; Both entry points preserve AF/BC/DE/HL/IX/IY, source V/mode and leave DI.
input_keys EQU $C620
input_psg15 EQU $C621

input_init:
    LD A,$3F
    LD ($C342),A
    RET

sample_fire:
sample_directions:
sample_native_input:
    PUSH AF
    PUSH BC
    PUSH DE
    PUSH HL
    DI
    IN A,($AA)
    LD D,A
    AND $F0
    OR 6
    OUT ($AA),A
    IN A,($A9)
    RRCA
    RRCA
    RRCA
    RRCA
    RRCA
    AND 3
    OR $3C
    LD ($C342),A
    LD A,D
    AND $F0
    OR 8
    OUT ($AA),A
    IN A,($A9)
    LD (input_keys),A
    LD A,D
    OUT ($AA),A

    LD A,15
    OUT ($A0),A
    IN A,($A2)
    LD (input_psg15),A
    AND $8F                 ; both common/strobe pins low while reading joysticks
    OR $0F
    LD E,A
    OUT ($A1),A
    LD A,14
    OUT ($A0),A
    IN A,($A2)
    LD B,A
    RLCA
    RLCA
    RLCA
    AND $80
    LD ($C30C),A
    LD A,B
    AND 15
    RLCA
    RLCA
    RLCA
    RLCA
    LD C,A
    SET 6,E
    LD A,15
    OUT ($A0),A
    LD A,E
    OUT ($A1),A
    LD A,14
    OUT ($A0),A
    IN A,($A2)
    LD B,A
    RLCA
    RLCA
    RLCA
    AND $80
    IFDEF INPUT_CORRUPT_PORT2
    XOR $80
    ENDIF
    LD ($C30D),A
    LD A,B
    AND 15
    OR C
    LD ($C340),A
    LD A,15
    OUT ($A0),A
    LD A,(input_psg15)
    OUT ($A1),A

    LD A,(input_keys)
    LD B,15
    BIT 5,A
    JR NZ,.down
    RES 0,B
.down:
    BIT 6,A
    JR NZ,.left
    RES 1,B
.left:
    BIT 4,A
    JR NZ,.right
    RES 2,B
.right:
    BIT 7,A
    JR NZ,.keyboard
    RES 3,B
.keyboard:
    LD A,($C047)             ; original C7 is0/1, not the old Seaquest selector
    OR A
    LD A,B
    JR NZ,.second
    RLCA
    RLCA
    RLCA
    RLCA
    OR 15
    JR .mask
.second:
    OR $F0
.mask:
    LD B,A
    LD A,($C340)
    AND B
    LD ($C340),A
    LD A,(input_keys)
    BIT 0,A
    JR NZ,.done
    LD A,($C047)
    LD E,A
    LD D,0
    LD HL,$C30C
    ADD HL,DE
    LD (HL),0
.done:
    POP HL
    POP DE
    POP BC
    POP AF
sample_native_return:
    RET
