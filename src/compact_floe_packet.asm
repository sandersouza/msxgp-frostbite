; C7D0 word: phase0 packet0..159. Reconstruct only its live PGT prefix.
; Table entries are pool byte offsets. Output C480..C4BF, unused bytes untouched.
; Preserve IX/IY/SP/IFF. No mapper/VDP writes; inputs immutable.
cp_build:
    PUSH IX
    LD HL,($C7D0)
    LD DE,cp_counts
    ADD HL,DE
    LD B,(HL)
    LD HL,($C7D0)
    ADD HL,HL
    LD DE,cp_directory
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    LD HL,cp_indices
    ADD HL,DE
    PUSH HL
    POP IX
    LD DE,$C480
.tile:
    LD L,(IX+0)
    LD H,(IX+1)
    INC IX
    INC IX
    PUSH DE
    LD DE,cp_patterns
    ADD HL,DE
    POP DE
    PUSH BC
    LD BC,8
    DUP 8
    LDI
    EDUP
    POP BC
    DJNZ .tile
    POP IX
    RET
cp_end:
