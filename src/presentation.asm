; Native presentation profile bootstrap. INCOMPLETE private renderer:
; source-pixel acceptance must fail until the live compositor is implemented.
INPUT       EQU $C100
PAGE        EQU $C200
ROWCOUNT    EQU $C21F
PHASE       EQU $C212
DELTA       EQU $C214
STEPS       EQU $C216
TICKS       EQU $C218
PALFLAG     EQU $C21B
READY       EQU $C2FE
SAT         EQU $C400
NAMES       EQU $C800

vdp_write:
    LD A,E
    OUT ($99),A
    LD A,D
    OUT ($99),A
    LD C,$98
vdp_stream:
.byte:
    OUTI
    JP NZ,.byte              ;29 standard MSX cycles/data write
    RET

presentation_init:
    LD HL,$C400
    LD DE,$C401
    LD BC,$1FF
    LD (HL),0
    LDIR
    LD HL,$C800
    LD DE,$C801
    LD BC,$1FFF             ;ends E7FF; E800-F33F remains guarded
    LD (HL),0
    LDIR
    LD A,208
    LD (SAT),A
    RET

cache_init:
    RET

prepare:
presentation_prepare:
    LD A,1
    LD ($7000),A
    LD A,(PAGE)
    XOR 1
    LD (PAGE),A
    CALL presentation_cache_begin
    LD A,(PAGE)
    OR A
    LD DE,$C500
    JR Z,.snapshot
    LD E,$80
.snapshot:
    LD HL,$C000
    LD BC,128
    LDIR
    RET

commit:
presentation_commit:
    LD HL,SAT
    LD DE,$5B00
    LD B,1
    CALL vdp_write
    LD A,(PAGE)
    ADD A,6
    OUT ($99),A
    LD A,$82
    OUT ($99),A
    RET

    INCLUDE "presentation_cache.asm"
