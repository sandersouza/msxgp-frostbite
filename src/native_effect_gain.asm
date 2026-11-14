; Selected source call sites only; original apply entry points and raw latches
; remain visible to independent audio instrumentation.
neg_event_0:
    EX AF,AF'
    EXX
    LD A,($C719)
    CALL p_audio_apply_19
neg_return_0:
    JP p_audio_event_done
neg_event_1:
    EX AF,AF'
    EXX
    LD A,($C71A)
    CALL p_audio_apply_1A
neg_return_1:
    JP p_audio_event_done

; Reuse the old 19-byte handlers. Equal raw latches still reach projection:
; an unrelated writer must undo the selected presentation gain.
neg_apply_0:
    AND 15
    LD HL,p_audio_volume
    CP (HL)
    JR Z,.project
    LD (HL),A
    CALL p_audio_noise
.project:
    LD A,(p_audio_volume)
    JP neg_filter_0
neg_apply_1:
    AND 15
    LD HL,p_audio_volume+1
    CP (HL)
    JR Z,.project
    LD (HL),A
    CALL p_audio_noise
.project:
    LD A,(p_audio_volume+1)
    JP neg_filter_1

neg_filter_0:
    LD B,8
    CP 4
    JP NZ,p_audio_write_changed
    JP neg_project
neg_filter_1:
    LD B,9
    CP 4
    JP NZ,p_audio_write_changed
    JP neg_project
; Return-address identity is local to this invocation, never a sticky flag.
neg_project:
    LD HL,0
    ADD HL,SP
    LD E,(HL)
    INC HL
    LD D,(HL)
    LD HL,neg_return_0
    BIT 0,B
    JR Z,.compare
    LD HL,neg_return_1
.compare:
    OR A
    SBC HL,DE
    LD A,4
    JP NZ,p_audio_write_changed
    INC A
    JP p_audio_write_changed
neg_end:
