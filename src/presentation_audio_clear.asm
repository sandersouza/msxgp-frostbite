; Preserve the original order: both zero-page TIA alias passes precede every
; canonical RAM clear. Mirror each actual audio store before applying it.
; The frozen bulk-clear helper then supplies its unchanged VM/flags result.
p_audio_core_clear:
    CALL p_audio_emit_clear
    JP core_clear

    MACRO p_audio_clear_zero target, address, threshold
    LD A,B
    CP threshold+1
    JR NC,1F
    PUSH BC                 ;internal apply may clobber all work registers
    XOR A
    LD (address),A
    CALL target
    POP BC
1:
    ENDM

; B=source entry X0..255. No source CPU register or flag is changed here.
; Only the original applicable decoded audio IO-shadow writes are performed.
p_audio_emit_clear:
    PUSH AF
    PUSH BC
    PUSH DE
    PUSH HL
    DUP 2,alias
    p_audio_clear_zero p_audio_apply_15,$C715,alias*64+$15
    p_audio_clear_zero p_audio_apply_16,$C716,alias*64+$16
    p_audio_clear_zero p_audio_apply_17,$C717,alias*64+$17
    p_audio_clear_zero p_audio_apply_18,$C718,alias*64+$18
    p_audio_clear_zero p_audio_apply_19,$C719,alias*64+$19
    p_audio_clear_zero p_audio_apply_1A,$C71A,alias*64+$1A
    EDUP
    POP HL
    POP DE
    POP BC
    POP AF
    RET
