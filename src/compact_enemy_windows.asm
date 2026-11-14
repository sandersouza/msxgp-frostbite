; A=0..131, two immutable literal eight-byte planes per original SGT.
; No glyph generation or per-frame decompression. IX/IY remain untouched.
sw_planes:
    LD L,A
    LD H,0
    ADD HL,HL
    ADD HL,HL
    LD BC,sw_directory
    ADD HL,BC
    LD C,(HL)
    INC HL
    LD B,(HL)
    INC HL
    LD E,(HL)
    INC HL
    LD D,(HL)
    LD HL,sw_pool
    ADD HL,BC
    EX DE,HL
    LD BC,sw_pool
    ADD HL,BC
    EX DE,HL
    RET

; Output exactly C500..C51F for the unchanged original clipping routine.
sw_read:
    PUSH AF
    LD HL,$C500
    LD DE,$C501
    LD BC,31
    LD (HL),0
    LDIR
    POP AF
    CALL sw_planes
    PUSH DE
    LD DE,$C500
    LD BC,8
    LDIR
    POP HL
    LD DE,$C510
    LD BC,8
    LDIR
    RET

; A=index, DE=VDP write address. Preserve original paced OUTI/JP streamer.
; No RAM output buffer on the ordinary unclipped path.
sw_upload:
    PUSH AF
    LD A,E
    OUT ($99),A
    LD A,D
    OUT ($99),A
    POP AF
    CALL sw_planes
    PUSH DE
    LD BC,$0898
    CALL vdp_stream
    LD HL,sw_zero
    LD B,8
    CALL vdp_stream
    POP HL
    LD B,8
    CALL vdp_stream
    LD HL,sw_zero
    LD B,8
    JP vdp_stream
sw_zero:
    DS 8,0
sw_end:
