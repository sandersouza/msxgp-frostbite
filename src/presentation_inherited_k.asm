    INCLUDE "symbols.inc"
    ORG $7F5F
k_programs EQU $C1C6
k_pointer EQU $C1CE
k_started EQU $C1D0
k_init:
    CALL $7A08              ;preserved I-B initializer
    LD HL,k_programs
    LD DE,k_programs+1
    LD BC,7
    LD (HL),255
    LDIR
    XOR A
    LD (k_started),A
    LD HL,$C080             ;original presentation_init continuation
    RET

; Only p_fixed_floe_prepare calls this wrapper with its fixed page/row owner.
; p_tl_program fully defines60 decoded names for that owner, independently
; of raw masks, foreground and coarse horizontal rotation.
k_decode:
    PUSH AF
    LD A,E
    RLCA
    RLCA
    AND 3
    LD L,A
    LD A,D
    AND 1
    RLCA
    RLCA
    OR L
    ADD A,k_programs&255
    LD L,A
    LD H,k_programs/256
    LD A,(p_tl_program)
    CP (HL)
    JR Z,.hit
    LD (k_pointer),HL
    POP AF
    CALL p_template_decode_names
    RET C
    LD HL,(k_pointer)
    LD A,(p_tl_program)
    LD (HL),A               ;valid only after full original decode
    XOR A
    RET
.hit:
    POP AF
    XOR A
    RET

; Ice copies begin at column0 and consume only p_w_name afterwards.
; The general actor path still derives its own full context with p_fast_cell.
k_name_address:
    LD A,(p_w_top)
    LD L,A
    LD H,0
    DUP 5
    ADD HL,HL
    EDUP
    LD A,(PAGE)
    OR A
    LD DE,$C800
    JR Z,.page
    LD D,$CD
.page:
    ADD HL,DE
    LD (p_w_name),HL
    RET
k_end:
    ASSERT $ <= $8000
