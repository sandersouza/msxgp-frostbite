; Isolated analytic horizontal mask compiler, not linked into the game.
; C780control0..9, C782relative floeX, C786absolute floeX. Other input bytes
; unused. Writes four masks per row atC800..C81F and scratchC7A0..C7BF.
; Preserves IX/IY/SP/IFF, clobbers AF/BC/DE/HL. No mapper or VDP access.
ce_row EQU $C7A0
ce_px EQU $C7A1
ce_qp EQU $C7A2
ce_qm EQU $C7A3
ce_kp EQU $C7A4
ce_km EQU $C7A5
ce_max EQU $C7A6
ce_sp EQU $C7A7
ce_sm EQU $C7A9
ce_before EQU $C7AB
ce_exit EQU $C7AD
ce_after EQU $C7AE
ce_after_ne EQU $C7AF
ce_union EQU $C7B0

ce_build_masks:
    PUSH IY
    LD IY,$C800
    LD A,($C786)
    LD B,A
    LD A,($C782)
    LD C,A
    LD A,B
    SUB C
    JR NC,.px_ready
    ADD A,160
.px_ready:
    LD (ce_px),A
    XOR A
    SUB B
    JR NC,.qp_ready
    ADD A,160
.qp_ready:
    LD (ce_qp),A
    SUB 4
    JR NC,.qm_ready
    ADD A,160
.qm_ready:
    LD (ce_qm),A
    XOR A
    LD (ce_row),A
.row:
    LD A,(ce_row)
    OR A
    JR Z,.initial_clocks
    CP 7
    JR Z,.clear_clocks
    DEC A
    LD L,A
    LD H,0
    LD DE,ce_edge_motion_clocks
    ADD HL,DE
    LD A,(HL)
    LD (ce_kp),A
    LD (ce_km),A
    JR .windows
.initial_clocks:
    LD A,($C780)
    ADD A,A
    LD L,A
    LD H,0
    LD DE,ce_edge_control_clocks
    ADD HL,DE
    LD A,(HL)
    LD (ce_kp),A
    INC HL
    LD A,(HL)
    LD (ce_km),A
    JR .windows
.clear_clocks:
    LD A,8
    LD (ce_kp),A
    LD (ce_km),A
.windows:
    LD A,(ce_kp)
    LD C,A
    LD A,(ce_qp)
    CALL ce_held
    LD (ce_sp),HL
    LD A,(ce_km)
    LD C,A
    LD A,(ce_qm)
    CALL ce_held
    LD (ce_sm),HL
    LD A,(ce_kp)
    LD B,A
    LD A,(ce_km)
    CP B
    JR NC,.maximum
    LD A,B
.maximum:
    CP 8
    JR NC,.max_ready
    LD A,8
.max_ready:
    LD (ce_max),A
    LD A,(ce_row)
    OR A
    JP Z,.first
    CP 7
    JP Z,.clear
    LD HL,(ce_sp)
    LD DE,(ce_sm)
    LD A,L
    OR E
    LD L,A
    LD A,H
    OR D
    LD H,A
    LD (ce_union),HL
    LD A,L
    AND 7
    LD (ce_exit),A
    LD A,H
    AND $10
    LD (ce_after_ne),A
    LD A,(ce_max)
    CP 13
    JR C,.before_clocks
    LD A,12
.before_clocks:
    CALL ce_low_mask
    LD HL,(ce_union)
    LD A,L
    AND E
    LD L,A
    LD A,H
    AND D
    LD H,A
    LD (ce_before),HL
    LD A,(ce_max)
    CALL ce_low_mask
    LD A,(ce_union+1)
    AND D
    AND $70
    LD (ce_after),A
    JP .emit
.first:
    LD HL,0
    LD (ce_before),HL
    XOR A
    LD (ce_exit),A
    LD (ce_after_ne),A
    LD A,(ce_kp)
    CP 13
    JR C,.first_clock
    LD A,12
.first_clock:
    LD B,A
    LD A,(ce_qp)
    ADD A,B
    CALL ce_active
    LD (ce_after),A
    LD A,(ce_kp)
    CALL ce_low_mask
    LD A,(ce_sp+1)
    AND D
    AND $70
    LD B,A
    LD A,(ce_after)
    OR B
    LD B,A
    LD A,(ce_sm+1)
    AND $40
    OR B
    LD (ce_after),A
    JR .emit
.clear:
    LD A,(ce_sm)
    AND 1
    LD B,A
    LD A,(ce_sp)
    OR B
    LD L,A
    LD H,0
    LD (ce_before),HL
    LD A,(ce_sp)
    AND 63
    OR B
    LD (ce_exit),A
    XOR A
    LD (ce_after),A
    LD (ce_after_ne),A
    LD A,(ce_sp)
    AND 128
    JR Z,.emit
    LD A,(ce_qp)
    ADD A,8
    CALL ce_active
    OR A
    JR NZ,.emit
    INC A
    LD (ce_after_ne),A
.emit:
    LD A,(ce_before)
    CALL ce_align
    LD E,A
    LD A,(ce_px)
    CP 8
    JR NC,.old_ready
    LD B,A
    LD A,(ce_before+1)
    AND 15
    JR NZ,.old_hold
    LD A,B
    OR A
    JR NZ,.old_ready
    LD A,(ce_after)
    OR A
    JR Z,.old_ready
.old_hold:
    LD A,B
    CALL ce_power
    OR E
    LD E,A
.old_ready:
    LD (IY+0),E
    XOR A
    LD (IY+1),A
    LD (IY+2),A
    LD A,(ce_after)
    OR A
    JR Z,.different
    LD A,(ce_px)
    DEC A
    CP 7
    JR NC,.different
    INC A
    CALL ce_power
    LD (IY+1),A
.different:
    LD A,(ce_after)
    LD B,A
    LD A,(ce_after_ne)
    OR B
    JR Z,.exit_mask
    LD A,(ce_px)
    DEC A
    CP 8
    JR NC,.exit_mask
    CALL ce_power
    LD (IY+2),A
.exit_mask:
    LD A,(ce_exit)
    CALL ce_align
    LD (IY+3),A
    LD DE,4
    ADD IY,DE
    LD A,(ce_kp)
    LD B,A
    LD A,(ce_qp)
    ADD A,B
    CALL ce_wrap
    SUB 8
    JR NC,.next_qp
    ADD A,160
.next_qp:
    LD (ce_qp),A
    LD A,(ce_km)
    LD B,A
    LD A,(ce_qm)
    ADD A,B
    CALL ce_wrap
    SUB 8
    JR NC,.next_qm
    ADD A,160
.next_qm:
    LD (ce_qm),A
    LD A,(ce_row)
    INC A
    LD (ce_row),A
    CP 8
    JP C,.row
    POP IY
    RET

; A=normalized source counter, C=clock count0..15; HL=held16-bit window.
ce_held:
    PUSH BC
    LD L,A
    LD H,0
    ADD HL,HL
    LD BC,ce_edge_windows
    ADD HL,BC
    LD E,(HL)
    INC HL
    LD D,(HL)
    POP BC
    PUSH BC
    LD L,C
    LD H,0
    ADD HL,HL
    LD BC,ce_edge_bits
    ADD HL,BC
    LD A,(HL)
    AND E
    LD B,A
    INC HL
    LD A,(HL)
    AND D
    OR B                   ; Z records the last sample before the stop
    POP BC
    LD L,C
    LD H,0
    ADD HL,HL              ; 16-bit ADD/INC/LD preserve Z
    LD BC,ce_edge_low_masks
    ADD HL,BC
    LD A,(HL)
    INC HL
    LD H,(HL)
    LD L,A
    JR Z,.off
    LD A,L
    CPL
    OR E
    LD L,A
    LD A,H
    CPL
    OR D
    LD H,A
    RET
.off:
    LD A,L
    AND E
    LD L,A
    LD A,H
    AND D
    LD H,A
    RET

ce_low_mask:
    LD L,A
    LD H,0
    ADD HL,HL
    LD DE,ce_edge_low_masks
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    RET

; A clock sequence, result aligned to original player bits; preserves DE.
ce_align:
    LD C,A
    LD A,(ce_px)
    CP 9
    JR C,.left
    CP 154
    JR C,.zero
    NEG
    ADD A,160
    LD B,A
    LD A,C
.shift_left:
    ADD A,A
    DJNZ .shift_left
    JR .reverse
.left:
    LD B,A
    OR A
    LD A,C
    JR Z,.reverse
.shift_right:
    SRL A
    DJNZ .shift_right
.reverse:
    LD L,A
    LD H,ce_edge_reverse/256
    LD A,(HL)
    RET
.zero:
    XOR A
    RET

ce_power:
    LD B,A
    OR A
    LD A,1
    RET Z
.shift:
    ADD A,A
    DJNZ .shift
    RET

ce_active:
    CALL ce_wrap
    CP 72
    JR NC,.off
    AND 31
    CP 8
    JR NC,.off
    LD A,1
    RET
.off:
    XOR A
    RET

ce_wrap:
    CP 160
    RET C
    SUB 160
    RET
ce_end:
    ASSERT (ce_edge_reverse & 255) == 0
