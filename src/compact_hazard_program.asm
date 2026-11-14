; Standalone ordinary row-program compiler, not linked into gameplay.
; Inputs C780..C784: playerX, objectX, NUSIZ, shape index, reflection.
; Outputs eight five-byte rows atC800..C827; scratchC7A0..C7BF.
; Each row: old/equal/different/exit/visible. Preserve IX/IY/SP/IFF.
    IFNDEF HP_INPUT_ORIGIN
    DEFINE HP_INPUT_ORIGIN $C780
    ENDIF
    IFNDEF HP_OUTPUT_ORIGIN
    DEFINE HP_OUTPUT_ORIGIN $C800
    ENDIF
    IFNDEF HP_SCRATCH_ORIGIN
    DEFINE HP_SCRATCH_ORIGIN $C7A0
    ENDIF
    IFNDEF CX_OUTPUT_ORIGIN
    DEFINE CX_OUTPUT_ORIGIN $C790
    ENDIF
hp_ctx EQU HP_SCRATCH_ORIGIN+0
hp_row EQU HP_SCRATCH_ORIGIN+4
hp_pointer EQU HP_SCRATCH_ORIGIN+5
hp_old EQU HP_SCRATCH_ORIGIN+7
hp_new EQU HP_SCRATCH_ORIGIN+8
hp_clock EQU HP_SCRATCH_ORIGIN+9
hp_screen EQU HP_SCRATCH_ORIGIN+10
hp_last EQU HP_SCRATCH_ORIGIN+11
hp_event EQU HP_SCRATCH_ORIGIN+12
hp_on EQU HP_SCRATCH_ORIGIN+13

hp_build:
    PUSH IY
    CALL cx_context
    LD HL,CX_OUTPUT_ORIGIN
    LD DE,hp_ctx
    LD BC,4
    LDIR
    LD A,(HP_INPUT_ORIGIN+3)
    LD L,A
    LD H,0
    LD DE,hp_shapes
    ADD HL,DE
    LD A,(HL)
    ADD A,7
    LD L,A
    LD A,(HP_INPUT_ORIGIN+4)
    AND 1
    ADD A,hp_enemy/256
    LD H,A
    LD (hp_pointer),HL
    LD A,(hp_ctx+3)
    CP 8
    JR NC,.screen_right
    NEG
    ADD A,7
    CALL hp_sample
    DEC A
    JR .screen_ready
.screen_right:
    CP 153
    LD A,255
    JR C,.screen_ready
    LD A,(hp_ctx+3)
    SUB 152
    LD B,A
    LD A,255
.screen_shift:
    ADD A,A
    DJNZ .screen_shift
.screen_ready:
    LD (hp_screen),A
    LD (hp_last),A
    LD A,(hp_ctx+3)
    CP 18
    JR C,.clip_ready
    CP 25
    JR NC,.last_zero
    SUB 17
    LD B,A
    LD A,255
.last_shift:
    ADD A,A
    DJNZ .last_shift
    JR .last_ready
.last_zero:
    XOR A
.last_ready:
    LD (hp_last),A
.clip_ready:
    XOR A
    LD (hp_old),A
    LD (hp_row),A
    LD IY,HP_OUTPUT_ORIGIN
.row:
    LD HL,(hp_pointer)
    LD A,(HL)
    LD (hp_new),A
    IFDEF HP_QUERY_TAG
    LD A,(HP_QUERY_TAG)
    LD B,A
    LD A,(hp_row)
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
    LD A,(hp_ctx+1)
    LD C,A
    LD A,(hp_old)
    CALL hp_shift
    LD (hp_clock),A
    CALL hp_align
    LD (IY+0),A
    LD A,(hp_clock)
    AND $E0
    CALL hp_align
    LD (IY+3),A
    LD A,(hp_ctx)
    LD C,A
    LD A,(hp_new)
    CALL hp_shift
    LD B,A
    LD A,(hp_row)
    CP 7
    LD A,(hp_screen)
    JR C,.visible_ready
    LD A,(hp_last)
.visible_ready:
    AND B
    LD (IY+4),A
    XOR A
    LD (IY+1),A
    LD (IY+2),A
    LD (hp_event),A
    LD A,(hp_old)
    LD B,A
    LD A,(hp_new)
    CP B
    JR Z,.held
    LD A,(hp_ctx+2)
    CP 255
    JR Z,.held
    CALL hp_sample
    LD B,A
    LD A,(hp_new)
    AND B
    LD (hp_on),A
    LD A,1
    LD (hp_event),A
    JR .after
.held:
    LD A,(hp_clock)
    AND 1
    LD (hp_on),A
.after:
    LD A,(hp_on)
    OR A
    JR Z,.next
    LD A,(hp_ctx+3)
    OR A
    JR NZ,.active_player
    LD A,(hp_event)
    OR A
    JR Z,.next
    SET 0,(IY+0)
    JR .next
.active_player:
    CP 9
    JR NC,.next
    NEG
    ADD A,8
    CALL hp_sample
    LD (IY+2),A
    LD A,(hp_event)
    OR A
    JR Z,.next
    LD A,(hp_ctx+3)
    CP 8
    JR NC,.next
    LD A,(IY+2)
    ADD A,A
    LD (IY+1),A
.next:
    LD A,(hp_new)
    LD (hp_old),A
    LD HL,(hp_pointer)
    DEC HL
    LD (hp_pointer),HL
    LD DE,5
    ADD IY,DE
    LD A,(hp_row)
    INC A
    LD (hp_row),A
    CP 8
    JP C,.row
    POP IY
    RET

; A source byte, C signed-distance index0..14 orFF. True shift, no wrap.
hp_shift:
    LD B,A
    LD A,C
    CP 255
    JR Z,.zero
    CP 7
    JR C,.right
    SUB 7
    LD C,A
    LD A,B
    RET Z
    LD B,C
.left_loop:
    ADD A,A
    DJNZ .left_loop
    RET
.right:
    NEG
    ADD A,7
    LD C,A
    LD A,B
    LD B,C
.right_loop:
    SRL A
    DJNZ .right_loop
    RET
.zero:
    XOR A
    RET

; Map clock0..7 bits back to player bits, including X153's single tail bit.
hp_align:
    LD C,A
    LD A,(hp_ctx+3)
    CP 9
    JR C,.left
    CP 153
    JR C,.zero
    NEG
    ADD A,160
    LD B,A
    LD A,C
.right_loop:
    SRL A
    DJNZ .right_loop
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
.zero:
    XOR A
    RET

hp_sample:
    LD L,A
    LD H,0
    LD DE,hp_samples
    ADD HL,DE
    LD A,(HL)
    RET
hp_end:
    ASSERT (hp_enemy & 255) == 0
