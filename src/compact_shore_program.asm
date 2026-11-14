; Compile18 source-clock shore rows from doubled literal bear glyphs.
; Inputs: mode0..5, playerX, bearX. Each output: old/equal/different/exit/visible.
    IFNDEF WS_INPUT_ORIGIN
    DEFINE WS_INPUT_ORIGIN $C780
    ENDIF
    IFNDEF WS_OUTPUT_ORIGIN
    DEFINE WS_OUTPUT_ORIGIN $C800
    ENDIF
    IFNDEF WS_SCRATCH_ORIGIN
    DEFINE WS_SCRATCH_ORIGIN $C7A0
    ENDIF
ws_body EQU WS_SCRATCH_ORIGIN
ws_clocks EQU WS_SCRATCH_ORIGIN+1
ws_initial EQU WS_SCRATCH_ORIGIN+2
ws_px EQU WS_SCRATCH_ORIGIN+3
ws_pointer EQU WS_SCRATCH_ORIGIN+4
ws_old EQU WS_SCRATCH_ORIGIN+6
ws_new EQU WS_SCRATCH_ORIGIN+8
ws_row EQU WS_SCRATCH_ORIGIN+10
ws_visible_distance EQU WS_SCRATCH_ORIGIN+11
ws_clock_distance EQU WS_SCRATCH_ORIGIN+12
ws_sample EQU WS_SCRATCH_ORIGIN+13
ws_clip EQU WS_SCRATCH_ORIGIN+14
ws_clock EQU WS_SCRATCH_ORIGIN+15
ws_event EQU WS_SCRATCH_ORIGIN+16
ws_on EQU WS_SCRATCH_ORIGIN+17
ws_window_distance EQU WS_SCRATCH_ORIGIN+18

ws_build:
    PUSH IY
    LD A,(WS_INPUT_ORIGIN+1)
    LD (ws_px),A
    LD A,(WS_INPUT_ORIGIN+2)
    LD B,A
    CP 15
    LD C,1
    JR NC,.body_offset
    LD C,6
.body_offset:
    ADD A,C
    CALL ws_wrap
    LD (ws_body),A
    LD A,B
.mod15:
    CP 15
    JR C,.remainder
    SUB 15
    JR .mod15
.remainder:
    NEG
    ADD A,14
    LD (ws_clocks),A
    LD B,A
    LD A,(ws_body)
    ADD A,B
    SUB 8
    CALL ws_wrap
    LD (ws_initial),A
    LD B,A
    XOR A
    SUB B
    JR NC,.window_distance
    ADD A,160
.window_distance:
    LD (ws_window_distance),A
    LD A,(ws_body)
    LD B,A
    LD A,(ws_px)
    SUB B
    JR NC,.visible_distance
    ADD A,160
.visible_distance:
    LD (ws_visible_distance),A
    XOR A
    SUB B
    JR NC,.clock_distance
    ADD A,160
.clock_distance:
    LD (ws_clock_distance),A
    LD A,8
    SUB B
    JR NC,.sample
    ADD A,160
.sample:
    CP 16
    JR C,.sample_ready
    LD A,255
.sample_ready:
    LD (ws_sample),A
    LD A,(ws_px)
    CP 8
    JR C,.clip_left
    CP 153
    JR NC,.clip_right
    LD A,255
    JR .clip_ready
.clip_left:
    OR A
    JR Z,.clip_ready
    LD B,A
    LD A,1
.clip_left_loop:
    ADD A,A
    DJNZ .clip_left_loop
    DEC A
    JR .clip_ready
.clip_right:
    SUB 152
    LD B,A
    LD A,255
.clip_right_loop:
    ADD A,A
    DJNZ .clip_right_loop
.clip_ready:
    LD (ws_clip),A
    LD HL,ws_glyphs+36
    LD DE,38
    LD A,(WS_INPUT_ORIGIN)
    OR A
    JR Z,.pointer_ready
    LD B,A
.mode:
    ADD HL,DE
    DJNZ .mode
.pointer_ready:
    LD (ws_pointer),HL
    LD HL,0
    LD (ws_old),HL
    XOR A
    LD (ws_row),A
    LD IY,WS_OUTPUT_ORIGIN
.row:
    LD HL,(ws_pointer)
    LD E,(HL)
    INC HL
    LD D,(HL)
    LD (ws_new),DE
    IFDEF WS_QUERY_TAG
    LD A,(WS_QUERY_TAG)
    LD B,A
    LD A,(ws_row)
    LD C,A
    LD A,B
    SUB C
    INC A
    CP 20
    JR C,.needed
    XOR A
    LD (IY+0),A
    LD (IY+1),A
    LD (IY+2),A
    LD (IY+3),A
    LD (IY+4),A
    JP .next
.needed:
    ENDIF
    LD HL,(ws_new)
    LD A,(ws_visible_distance)
    CALL ws_mask
    LD B,A
    LD A,(ws_clip)
    AND B
    LD (IY+4),A
    XOR A
    LD (IY+0),A
    LD (IY+1),A
    LD (IY+2),A
    LD (IY+3),A
    LD (ws_event),A
    LD (ws_clock),A
    LD A,(ws_row)
    OR A
    JR NZ,.ordinary
    LD HL,(ws_new)
    LD A,(ws_window_distance)
    CALL ws_window
    PUSH HL
    LD A,(ws_clocks)
    ADD A,A
    LD E,A
    LD D,0
    LD HL,ws_selectors
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    POP HL
    LD A,H
    AND D
    LD C,A
    LD A,L
    AND E
    OR C
    LD A,0
    JR Z,.first_off
    INC A
.first_off:
    LD (ws_on),A
    LD A,1
    LD (ws_event),A
    JR .tail
.ordinary:
    LD HL,(ws_old)
    LD A,(ws_clock_distance)
    CALL ws_mask
    LD (ws_clock),A
    CALL ws_align
    LD (IY+0),A
    LD A,(ws_clock)
    AND $E0
    CALL ws_align
    LD (IY+3),A
    LD A,(ws_sample)
    CP 255
    JR Z,.held
    LD HL,(ws_old)
    LD DE,(ws_new)
    OR A
    SBC HL,DE
    JR Z,.held
    LD A,1
    LD (ws_event),A
    LD A,(ws_sample)
    ADD A,A
    LD E,A
    LD D,0
    LD HL,ws_samples
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    LD HL,(ws_new)
    LD A,H
    AND D
    LD C,A
    LD A,L
    AND E
    OR C
    LD A,0
    JR Z,.on_ready
    INC A
    JR .on_ready
.held:
    LD A,(ws_clock)
    AND 1
.on_ready:
    LD (ws_on),A
.tail:
    LD A,(ws_on)
    OR A
    JR Z,.next
    LD A,(ws_px)
    OR A
    JR NZ,.active_player
    LD A,(ws_event)
    OR A
    JR Z,.next
    SET 0,(IY+0)
    JR .next
.active_player:
    CP 9
    JR NC,.next
    DEC A
    CALL ws_power
    LD (IY+2),A
    LD A,(ws_event)
    OR A
    JR Z,.next
    LD A,(ws_px)
    CP 8
    JR NC,.next
    CALL ws_power
    LD (IY+1),A
.next:
    LD HL,(ws_new)
    LD (ws_old),HL
    LD HL,(ws_pointer)
    DEC HL
    DEC HL
    LD (ws_pointer),HL
    LD DE,5
    ADD IY,DE
    LD A,(ws_row)
    INC A
    LD (ws_row),A
    CP 18
    JP C,.row
    POP IY
    RET

; HL=doubled byte, A=(sampleX-bodyX)%160, return its eight visible bits.
ws_mask:
    CP 16
    JR C,.positive
    CP 153
    JR NC,.negative
    XOR A
    RET
.negative:
    NEG
    ADD A,160
    LD B,A
    LD A,H
.right:
    SRL A
    DJNZ .right
    RET
.positive:
    CP 8
    JR C,.small
    SUB 8
    LD B,A
    OR A
    LD A,L
    RET Z
.left_byte:
    ADD A,A
    DJNZ .left_byte
    RET
.small:
    LD B,A
    OR A
    LD A,H
    RET Z
.left_word:
    ADD HL,HL
    DJNZ .left_word
    LD A,H
    RET

ws_window:
    CP 16
    JR C,.left
    CP 145
    JR NC,.right
    LD HL,0
    RET
.left:
    OR A
    RET Z
    LD B,A
.left_loop:
    ADD HL,HL
    DJNZ .left_loop
    RET
.right:
    NEG
    ADD A,160
    LD B,A
.right_loop:
    SRL H
    RR L
    DJNZ .right_loop
    RET

ws_align:
    LD C,A
    LD A,(ws_px)
    CP 9
    JR C,.left
    CP 153
    JR NC,.right
    XOR A
    RET
.left:
    LD B,A
    OR A
    LD A,C
    RET Z
.left_loop:
    ADD A,A
    DJNZ .left_loop
    RET
.right:
    NEG
    ADD A,160
    LD B,A
    LD A,C
.right_loop:
    SRL A
    DJNZ .right_loop
    RET

ws_power:
    LD B,A
    OR A
    LD A,1
    RET Z
.loop:
    ADD A,A
    DJNZ .loop
    RET

ws_wrap:
    CP 160
    RET C
    CP 248
    JR C,.positive
    ADD A,160
    RET
.positive:
    SUB 160
    RET
ws_end:
