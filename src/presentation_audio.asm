; Read-only source-audio observers. Main AF/BC/DE/HL, source carry in E and
; IX/IY stay intact; only alternate registers and the owned E000..E014 work
; are used. DI is the platform contract. No BIOS or joystick-register writes.
p_audio_control EQU $E000
p_audio_frequency EQU $E002
p_audio_volume EQU $E004
p_audio_psg EQU $E006
p_audio_gpio EQU $E011
p_audio_owner EQU $E012
p_audio_parts EQU $E013

    MACRO p_audio_observer event_name, apply_name, source
event_name:
    EX AF,AF'
    EXX
    LD A,(source)
    CALL apply_name
    JP p_audio_event_done
    ENDM

    p_audio_observer p_audio_event_15,p_audio_apply_15,$C715
    p_audio_observer p_audio_event_16,p_audio_apply_16,$C716
    p_audio_observer p_audio_event_17,p_audio_apply_17,$C717
    p_audio_observer p_audio_event_18,p_audio_apply_18,$C718
    p_audio_observer p_audio_event_19,p_audio_apply_19,$C719
    p_audio_observer p_audio_event_1A,p_audio_apply_1A,$C71A

; Source pointer helpers have already decoded the original address to HL.
; Copy it into the alternate set without changing its main-register value.
p_audio_event_indexed:
    PUSH HL
    EX AF,AF'
    EXX
    POP HL
    LD A,H
    CP $C7
    JP NZ,p_audio_event_done
    LD A,L
    SUB $15
    CP 6
    JP NC,p_audio_event_done
    LD C,(HL)
    ADD A,A
    ADD A,p_audio_dispatch&255
    LD L,A
    LD H,p_audio_dispatch/256
    LD E,(HL)
    INC L
    LD D,(HL)
    EX DE,HL
    LD A,C
    LD DE,p_audio_event_done
    PUSH DE
    JP (HL)                ;internal apply RET returns through the same restore
p_audio_event_done:
    EXX
    EX AF,AF'
p_audio_event_restored:
    RET

; Internal apply entries accept unmodified bus value A. They return normally,
; permitting audited lowering of original clear-store effects without nested
; alternate-register swaps. They never write the emulated source bus itself.
    MACRO p_audio_control_handler name, channel
name:
    AND 15
    LD HL,p_audio_control+channel
    CP (HL)
    RET Z
    LD (HL),A
    ADD A,p_audio_mixer_parts&255
    LD L,A
    LD H,p_audio_mixer_parts/256
    LD A,(HL)
    LD (p_audio_parts+channel),A
    CALL p_audio_period_0+channel*(p_audio_period_1-p_audio_period_0)
    CALL p_audio_noise
    JP p_audio_mixer
    ENDM
    p_audio_control_handler p_audio_apply_15,0
    p_audio_control_handler p_audio_apply_16,1

    MACRO p_audio_frequency_handler name, channel
name:
    AND 31
    LD HL,p_audio_frequency+channel
    CP (HL)
    RET Z
    LD (HL),A
    CALL p_audio_period_0+channel*(p_audio_period_1-p_audio_period_0)
    JP p_audio_noise
    ENDM
    p_audio_frequency_handler p_audio_apply_17,0
    p_audio_frequency_handler p_audio_apply_18,1

    MACRO p_audio_volume_handler name, channel
name:
    AND 15
    LD HL,p_audio_volume+channel
    CP (HL)
    RET Z
    LD (HL),A
    CALL p_audio_noise
    LD A,(p_audio_volume+channel)
    LD B,8+channel
    JP p_audio_write_changed
    ENDM
    p_audio_volume_handler p_audio_apply_19,0
    p_audio_volume_handler p_audio_apply_1A,1

    MACRO p_audio_period_handler name, channel
name:
    LD A,(p_audio_parts+channel)
    BIT 0,A
    RET NZ                 ;DC or noise-only retains the previous tone period
    LD A,(p_audio_control+channel)
    ADD A,A
    ADD A,p_audio_tone_pointers&255
    LD L,A
    LD H,p_audio_tone_pointers/256
    LD E,(HL)
    INC L
    LD D,(HL)
    EX DE,HL
    LD A,(p_audio_frequency+channel)
    ADD A,A
    ADD A,L                ;each64-byte row is aligned; index0..62 cannot carry
    LD L,A
    LD E,(HL)
    INC L
    LD D,(HL)
    LD A,E
    LD B,channel*2
    CALL p_audio_write_changed
    LD A,D                 ;the write helper preserves DE
    LD B,channel*2+1
    JP p_audio_write_changed
    ENDM
    p_audio_period_handler p_audio_period_0,0
    p_audio_period_handler p_audio_period_1,1

p_audio_noise:
    LD A,(p_audio_control)
    CP 8
    JR NZ,.second
    LD A,(p_audio_volume)
    OR A
    JR Z,.second
    XOR A
    JR .selected
.second:
    LD A,(p_audio_control+1)
    CP 8
    JR NZ,.inactive
    LD A,(p_audio_volume+1)
    OR A
    JR Z,.inactive
    LD A,1
    JR .selected
.inactive:
    LD A,255
.selected:
    LD (p_audio_owner),A
    CP 2
    RET NC
    ADD A,p_audio_frequency&255
    LD L,A
    LD H,p_audio_frequency/256
    LD A,(HL)
    ADD A,p_audio_noise_periods&255
    LD L,A
    LD H,p_audio_noise_periods/256
    LD A,(HL)
    LD B,6
    JP p_audio_write_changed

p_audio_mixer:
    LD A,(p_audio_parts)
    AND 9
    LD B,A
    LD A,(p_audio_parts+1)
    AND 9
    ADD A,A
    OR B
    OR 36                  ;C tone/noise are disabled for every source mode
    LD C,A
    LD A,(p_audio_gpio)
    OR C
    LD B,7
    JP p_audio_write_changed

; A=value, B=owned register0..10. Preserve DE for the period's second byte.
p_audio_write_changed:
    LD C,A
    LD A,B
    ADD A,p_audio_psg&255
    LD L,A
    LD H,p_audio_psg/256
    LD A,C
    CP (HL)
    RET Z
    LD (HL),A
p_audio_write_port:
    PUSH AF
    LD A,B
    OUT ($A0),A
    POP AF
    OUT ($A1),A
    RET

; Called before native reset. Initializing audio never selects GPIO14/15 and
; retains the BIOS/input peripheral directions read from the actual PSG7.
p_audio_init:
    LD A,7
    OUT ($A0),A
    IN A,($A2)
    AND $C0
    LD (p_audio_gpio),A
    OR 63
    LD (p_audio_psg+7),A
    LD HL,p_audio_defaults
    LD DE,p_audio_psg
    LD BC,11
    LDIR
    LD A,(p_audio_gpio)
    OR 63
    LD (p_audio_psg+7),A
    LD HL,p_audio_control
    LD DE,p_audio_control+1
    LD BC,5
    LD (HL),0
    LDIR
    LD A,255
    LD (p_audio_owner),A
    LD A,9
    LD (p_audio_parts),A
    LD (p_audio_parts+1),A
    LD HL,p_audio_psg
    LD B,0
.register:
    LD A,B
    CP 4
    JR C,.write
    CP 6
    JR C,.advance          ;C tone registers4/5 remain completely unowned
.write:
    LD A,(HL)
    CALL p_audio_write_port
.advance:
    INC HL
    INC B
    LD A,B
    CP 11
    JR NZ,.register
    RET

    ALIGN 16
p_audio_dispatch:
    DW p_audio_apply_15,p_audio_apply_16,p_audio_apply_17
    DW p_audio_apply_18,p_audio_apply_19,p_audio_apply_1A
    ASSERT (p_audio_dispatch&255)+12 <= 256
    ASSERT (p_audio_tone_pointers&255)+32 <= 256
    ASSERT (p_audio_noise_periods&255)+32 <= 256
    ASSERT (p_audio_mixer_parts&255)+16 <= 256
