; Zero exactly the accepted five24-byte general-player planes. Temporary SP
; remains in that owned buffer only with maskable interrupts disabled. Save
; the caller's IFF2 and real stack before moving it; restore both before RET.
; AF/BC/DE/HL are scratch; the following original initializer reloads them.
np_clear:
    LD A,I
    PUSH AF
    DI
    LD HL,0
    ADD HL,SP
    EX DE,HL
    LD HL,0
    LD SP,$E7F8
    LD B,15
.zero:
    DUP 4
    PUSH HL
    EDUP
    DJNZ .zero
    EX DE,HL
    LD SP,HL
    POP AF
    JP PO,.done
    EI
.done:
    RET
np_clear_end:
