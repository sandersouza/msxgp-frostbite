; C7F0 phase0..159, C7F1 owner0..7. Return original32-byte row atC480.
; Only the first9 bytes of each palette page are read; page holes stay free.
; No mapper/VDP/scratch accesses. IX/IY/SP/IFF preserved.
cg_build:
    LD A,($C7F0)
    LD L,A
    LD H,HIGH cg_directory
    LD L,(HL)
    LD H,0
    DUP 5
    ADD HL,HL
    EDUP
    LD DE,cg_rows
    ADD HL,DE
    LD A,($C7F1)
    ADD A,HIGH cg_palettes
    LD B,A
    LD DE,$C480
    DUP 30
    LD C,(HL)
    LD A,(BC)
    LD (DE),A
    INC L
    INC E
    EDUP
    XOR A
    LD (DE),A
    INC E
    LD (DE),A
    RET
cg_end:

    ASSERT (cg_rows & 31) == 0
    ASSERT (cg_rows & 255) + 31 < 256
    ASSERT ($C480 & 255) + 31 < 256
