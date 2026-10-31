; Original diagnostic scaffold. No Atari game code or generated assets.
    ORG $4000
    DB "AB"
    DW start
    DS 12,0

TICKS   EQU $C002
DIR     EQU $C004
FIRE    EQU $C005
PREV    EQU $C006
PRESSES EQU $C007

start:
    DI
    IM 1
    LD SP,$F380
    XOR A
    LD HL,$C000
    LD B,16
.clear:
    LD (HL),A
    INC HL
    DJNZ .clear
    LD A,15
    LD ($F3E9),A              ; FORCLR
    LD A,4
    LD ($F3EA),A              ; BAKCLR
    LD ($F3EB),A              ; BDRCLR
    LD A,1
    CALL $005F               ; CHGMOD: SCREEN 1, native MSX1 tile mode
    LD HL,message
    CALL print_string

    LD A,7
    CALL $0096               ; RDPSG: preserve the joystick I/O direction bits
    AND $C0
    OR $3E                   ; tone A only; no noise/tone on B/C
    LD E,A
    LD A,7
    CALL $0093               ; WRTPSG
    LD E,0
    XOR A
    CALL $0093               ; period A low
    LD A,1
    LD E,1
    CALL $0093               ; period A high: 256
    CALL update_sound
    LD A,'F'
    LD ($C000),A
    LD A,'B'
    LD ($C001),A              ; publish ready signature after initialization
    EI
loop:
    HALT
    LD HL,(TICKS)
    INC HL
    LD (TICKS),HL
    CALL read_controls
    CALL update_sound
    CALL show_status
    JR loop

read_controls:
    XOR A
    CALL $00D5               ; GTSTCK(0): diagnostic cursor keys
    OR A
    JR NZ,.have_dir
    LD A,1
    CALL $00D5               ; GTSTCK(1): joystick 1
.have_dir:
    LD (DIR),A
    XOR A
    CALL $00D8               ; GTTRIG(0): SPACE
    OR A
    JR NZ,.pressed
    LD A,1
    CALL $00D8               ; GTTRIG(1): joystick 1 fire
    OR A
    JR Z,.have_fire
.pressed:
    LD A,1
.have_fire:
    LD (FIRE),A
    LD C,A
    LD A,(PREV)
    XOR 1
    AND C
    JR Z,.save
    LD HL,PRESSES
    INC (HL)
.save:
    LD A,C
    LD (PREV),A
    RET

update_sound:
    LD A,(FIRE)
    OR A
    LD E,0
    JR Z,.volume
    LD E,8
.volume:
    LD A,8
    CALL $0093               ; steady PSG A test tone only while fire is held
    RET

show_status:
    LD HL,$0C08              ; POSIT: column12,row8, one-based
    CALL $00C6
    LD HL,(TICKS)
    LD A,H
    CALL hex_byte
    LD A,L
    CALL hex_byte
    LD HL,$1209              ; direction digit
    CALL $00C6
    LD A,(DIR)
    ADD A,'0'
    CALL put_char
    LD HL,$120A              ; fire digit
    CALL $00C6
    LD A,(FIRE)
    ADD A,'0'
    CALL put_char
    RET

hex_byte:
    PUSH AF
    RRCA
    RRCA
    RRCA
    RRCA
    AND 15
    CALL hex_digit
    POP AF
    AND 15
hex_digit:
    ADD A,'0'
    CP '9'+1
    JR C,put_char
    ADD A,7
put_char:
    PUSH HL
    CALL $00A2               ; CHPUT
    POP HL
    RET

print_string:
    LD A,(HL)
    OR A
    RET Z
    CALL put_char
    INC HL
    JR print_string

message:
    DB "FROSTBITE MSX1",13,10
    DB "DIAGNOSTIC v0.0.1",13,10,13,10
    DB "16K ROM - NO MAPPER",13,10
    DB "64K RAM / 16K VRAM",13,10
    DB "NO GAMEPLAY YET",13,10,13,10
    DB "HEARTBEAT: 0000",13,10
    DB "ARROWS/JOY1 DIR: 0",13,10
    DB "SPACE/JOY1 FIRE: 0",13,10,13,10
    DB "HOLD FIRE FOR TEST TONE",13,10,13,10
    DB "TEST VIDEO / INPUT / PSG",13,10
    DB "STANDARD Z80 + TMS9918",0

    ASSERT $ < $8000
    DS $8000-$,$FF
