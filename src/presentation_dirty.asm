; Bank2 normalized visual state and dirty-row dependencies. No mapper writes
; are allowed here: all reads are canonical RAM or fixed resident helpers.
p_fd_state EQU $E540
p_fd_rows EQU $C2D8
p_fd_history EQU $C2DB
p_fd_delta EQU $C2C9
p_fd_hm EQU $C2CA

p_dirty_describe:
    CALL p_dirty_capture
    LD HL,$C540
    LD A,(PAGE)
    OR A
    JR Z,.history
    LD L,$A0
.history:
    LD (p_fd_history),HL
    PUSH HL
    POP IX
    LD IY,p_fd_state
    XOR A
    LD (p_fd_rows),A
    LD (p_fd_rows+1),A
    LD (p_fd_rows+2),A
    LD A,(IX)
    CP 1
    JP NZ,.full
    LD E,50
    LD B,2
    CALL p_dirty_compare
    JP NZ,.full
    LD A,(IX+1)
    CP 32
    JR NZ,.old_not_blank
    LD A,(IY+1)
    CP 32
    JP Z,.save
    JP .full
.old_not_blank:
    LD A,(IY+1)
    CP 32
    JP Z,.full
    XOR (IX+1)
    BIT 1,A
    JP NZ,.full
    LD C,A
    BIT 0,C
    JR Z,.gradient
    LD A,255
    LD (p_fd_rows),A
    LD A,1
    LD (p_fd_rows+1),A
.gradient:
    LD A,C
    AND 28
    JR Z,.header
    LD A,(p_fd_rows)
    OR 8
    LD (p_fd_rows),A
.header:
    LD E,3
    LD B,8
    CALL p_dirty_compare
    JR Z,.igloo5
    LD A,(p_fd_rows)
    OR 7
    LD (p_fd_rows),A
.igloo5:
    LD E,11
    LD B,2
    CALL p_dirty_compare
    JR Z,.igloo4
    LD A,(p_fd_rows)
    OR 32
    LD (p_fd_rows),A
.igloo4:
    LD E,13
    LD B,2
    CALL p_dirty_compare
    JR Z,.igloo3
    LD A,(p_fd_rows)
    OR 16
    LD (p_fd_rows),A
.igloo3:
    LD A,(IX+15)
    CP (IY+15)
    JR Z,.bear
    LD A,(p_fd_rows)
    OR 8
    LD (p_fd_rows),A
.bear:
    LD E,16
    LD B,4
    CALL p_dirty_compare
    JR Z,.objects
    LD A,(p_fd_rows)
    OR 192
    LD (p_fd_rows),A
    LD A,(p_fd_rows+1)
    OR 1
    LD (p_fd_rows+1),A
.objects:
    XOR A
    LD (p_w_row),A
.object:
    LD A,(p_w_row)
    LD E,A
    ADD A,A
    ADD A,A
    ADD A,E
    ADD A,20
    LD E,A
    LD B,5
    CALL p_dirty_compare
    JR Z,.next_object
    IFDEF WITH_PRESENTATION_TEMPLATES
    CALL p_template_dirty_object
    ELSE
    CALL p_world_row_y
    ADD A,153
    LD B,8
    CALL p_dirty_span
    ENDIF
.next_object:
    LD HL,p_w_row
    INC (HL)
    LD A,(HL)
    CP 4
    JR NZ,.object
    LD A,(IX+48)
    CP (IY+48)
    LD A,0
    JR Z,.delta
    INC A
.delta:
    LD (p_fd_delta),A
    XOR A
    LD (p_w_row),A
.floe:
    LD A,(p_fd_delta)
    OR A
    JR NZ,.floe_changed
    LD A,(p_w_row)
    ADD A,A
    ADD A,40
    LD E,A
    LD B,2
    CALL p_dirty_compare
    JR Z,.next_floe
.floe_changed:
    IFDEF WITH_PRESENTATION_TEMPLATES
    CALL p_template_dirty_floe
    ELSE
    CALL p_world_row_y
    ADD A,167
    LD B,7
    CALL p_dirty_span
    ENDIF
.next_floe:
    LD HL,p_w_row
    INC (HL)
    LD A,(HL)
    CP 4
    JR NZ,.floe
    LD A,(IX+49)
    CP (IY+49)
    JR Z,.save
    LD A,(p_fd_rows+2)
    OR 192
    LD (p_fd_rows+2),A
    JR .save
.full:
    LD A,255
    LD (p_fd_rows),A
    LD (p_fd_rows+1),A
    LD (p_fd_rows+2),A
.save:
    LD HL,p_fd_state
    LD DE,(p_fd_history)
    LD BC,64
    LDIR
    RET

; Compare E=offset/B=length in the two64-byte states. All static callers use
; lengths2,4,5or8. Both histories remain in one256-byte page, so byte pointer
; increments are sufficient; unrolled suffixes avoid a DJNZ for every field.
p_dirty_compare:
    LD C,E
    PUSH IY
    POP DE
    LD A,E
    ADD A,C
    LD E,A
    PUSH IX
    POP HL
    LD A,L
    ADD A,C
    LD L,A
    LD A,B
    CP 4
    JR C,.two
    JR Z,.four
    RRA
    JR C,.five
.eight:
    DUP 3
    LD A,(DE)
    CP (HL)
    RET NZ
    INC E
    INC L
    EDUP
.five:
    LD A,(DE)
    CP (HL)
    RET NZ
    INC E
    INC L
.four:
    DUP 2
    LD A,(DE)
    CP (HL)
    RET NZ
    INC E
    INC L
    EDUP
.two:
    LD A,(DE)
    CP (HL)
    RET NZ
    INC E
    INC L
    LD A,(DE)
    CP (HL)
    RET

p_dirty_span:
    LD C,A
    ADD A,B
    DEC A
    DUP 3
    SRL A
    EDUP
    LD E,A
    LD A,C
    DUP 3
    SRL A
    EDUP
    LD C,A
.row:
    LD A,C
    CALL p_dirty_mark_row
    LD A,C
    CP E
    RET Z
    INC C
    JR .row

p_dirty_mark_row:
    PUSH BC
    PUSH DE
    PUSH HL
    LD C,A
    AND 7
    LD E,A
    LD D,0
    LD HL,p_fast_bits
    ADD HL,DE
    LD B,(HL)
    LD A,C
    DUP 3
    SRL A
    EDUP
    LD E,A
    LD HL,p_fd_rows
    ADD HL,DE
    LD A,(HL)
    OR B
    LD (HL),A
    POP HL
    POP DE
    POP BC
    RET

p_dirty_capture:
    LD A,1
    LD (p_fd_state),A
    LD A,(p_bg_profile)
    LD (p_fd_state+1),A
    LD HL,$C048
    LD DE,p_fd_state+3
    LD BC,3
    LDIR
    LD A,($C065)
    LD (p_fd_state+6),A
    LD A,($C04C)
    LD (p_fd_state+7),A
    LD A,($C047)
    LD (p_fd_state+8),A
    LD A,($C04B)
    CP 20
    LD A,0
    ADC A,0
    XOR 1
    LD (p_fd_state+9),A
    LD A,($C065)
    AND $F0
    JR NZ,.no_blink
    LD A,($C071)
    OR A
    JR NZ,.no_blink
    LD A,($C001)
    AND 8
    JR NZ,.no_blink
    LD A,1
    JR .blink
.no_blink:
    XOR A
.blink:
    LD (p_fd_state+10),A
    LD HL,$C040
    LD DE,p_fd_state+11
    LD BC,5
    LDIR
    LD A,($C068)
    LD (p_fd_state+16),A
    LD A,($C06F)
    LD (p_fd_state+17),A
    LD A,($C06C)
    AND 16
    LD (p_fd_state+18),A
    LD A,($C04B)
    CP 3
    LD A,0
    ADC A,0
    XOR 1
    LD (p_fd_state+19),A
    ; Fixed field addresses avoid repeated indexed-source address arithmetic.
    DUP 4,r
    LD A,($C023+r)
    LD (p_fd_state+20+r*5),A
    LD A,($C011+r)
    AND 128
    LD (p_fd_state+21+r*5),A
    LD A,($C027+r)
    AND 254
    LD (p_fd_state+22+r*5),A
    LD A,($C058+r)
    LD (p_fd_state+23+r*5),A
    LD A,($C054+r)
    LD (p_fd_state+24+r*5),A
    EDUP
    LD A,($C01C)
    CALL p_world_nibble
    LD (p_fd_hm),A
    ADD A,16
    LD C,A
    LD A,($C01D)
    CALL p_world_nibble
    LD B,A
    LD A,(p_fd_hm)
    SUB B
    ADD A,4
    LD (p_fd_state+48),A
    DUP 4,r
    LD A,($C01F+r)
    ADD A,16
    SUB C
    JR NC,$+4              ; skip the two-byte signed-wrap correction
    ADD A,160
    CALL normalize_x
    LD (p_fd_state+40+r*2),A
    LD A,($C02B+r)
    AND 254
    LD (p_fd_state+41+r*2),A
    EDUP
    LD A,($C046)
    AND 31
    SUB 12
    JR NC,.phase_positive
    XOR A
.phase_positive:
    CP 8
    JR C,.phase
    LD A,7
.phase:
    LD (p_fd_state+49),A
    LD A,(INPUT+30)
    AND 1
    LD (p_fd_state+50),A
    LD A,(INPUT+31)
    AND 1
    LD (p_fd_state+51),A
    RET
