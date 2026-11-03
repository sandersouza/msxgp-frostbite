; Exact16-byte tile cache. CPU/source ABI state is already saved by caller.
; Six groups=(generation*3+SCREEN2bank),64slots/group; no probabilistic reuse.
p_cache_counts EQU $CCA0
p_cache_miss EQU $CCA6         ;0=reused,1=new,2=overflow/invalid
p_cache_group EQU $CCA7
p_cache_hash EQU $CCA8
p_cache_slot EQU $CCA9
p_cache_count EQU $CCAA
p_cache_pointer EQU $CCAB
p_cache_signature EQU $CCAD
p_cache_used EQU $CCB0         ;6x8bytes, cleared only for inactive generation
p_cache_scratch EQU $CC80

; A=inactive generation0/1. Old cache content remains available for reuse;
; allocation may evict only slots not referenced by this newly prepared frame.
presentation_cache_begin:
    CP 2
    JP NC,presentation_cache_full
    OR A
    LD HL,p_cache_used
    JR Z,.clear
    LD HL,p_cache_used+24
.clear:
    XOR A
    LD (p_cache_miss),A
    LD (HL),A
    LD D,H
    LD E,L
    INC DE
    LD BC,23
    LDIR
    XOR A
    RET

; A=group0..5; scratch contains pattern8 then color8. Returns bank-local ID
;0..127. FF+miss2 rejects a full generation; it never drops/approximates a tile.
presentation_cache_tile:
    CP 6
    JP NC,presentation_cache_full
    LD (p_cache_group),A
    XOR A
    LD (p_cache_miss),A
    LD (p_cache_slot),A
    LD HL,p_cache_scratch
    DUP 16
    ADD A,(HL)
    RLCA
    INC HL
    EDUP
    LD (p_cache_hash),A
    LD A,(p_cache_group)
    LD L,A
    LD H,0
    DUP 6
    ADD HL,HL
    EDUP
    LD DE,$CB00
    ADD HL,DE
    LD (p_cache_signature),HL
    LD A,(p_cache_group)
    LD L,A
    LD H,0
    LD DE,p_cache_counts
    ADD HL,DE
    LD A,(HL)
    LD (p_cache_count),A
    LD C,A
    LD B,0
    OR A
    JP Z,presentation_cache_allocate
    LD HL,(p_cache_signature)
.lookup:
    LD A,(p_cache_hash)
    CPIR
    JP NZ,presentation_cache_allocate
    PUSH BC
    PUSH HL
    LD A,L
    DEC A
    AND 63
    LD (p_cache_slot),A
    LD L,A
    LD H,0
    DUP 4
    ADD HL,HL
    EDUP
    LD A,(p_cache_group)
    ADD A,A
    ADD A,A
    ADD A,$D0
    ADD A,H
    LD H,A
    LD DE,p_cache_scratch
    DUP 16
    LD A,(DE)
    CP (HL)
    JP NZ,.different
    INC DE
    INC HL
    EDUP
    POP HL
    POP BC
    JP presentation_cache_mark
.different:
    POP HL
    POP BC
    LD A,B
    OR C
    JP NZ,.lookup
    JP presentation_cache_allocate

presentation_cache_full:
    LD A,2
    LD (p_cache_miss),A
    LD A,255
    SCF
    RET

presentation_cache_allocate:
    LD A,(p_cache_group)
    ADD A,A
    ADD A,A
    ADD A,A
    ADD A,p_cache_used&255
    LD L,A
    LD H,p_cache_used/256
    LD D,0
    LD B,8
.free_byte:
    LD A,(HL)
    CP 255
    JR NZ,.partial
    INC HL
    LD A,D
    ADD A,8
    LD D,A
    DJNZ .free_byte
    JR presentation_cache_full
.partial:
    LD C,A
    LD E,1
.free_bit:
    LD A,C
    AND E
    JR Z,.selected
    INC D
    SLA E
    JR .free_bit
.selected:
    LD A,D
    LD (p_cache_slot),A
    LD HL,p_cache_count
    CP (HL)
    JR C,.copy
    LD A,(p_cache_group)
    LD L,A
    LD H,0
    LD DE,p_cache_counts
    ADD HL,DE
    INC (HL)
.copy:
    LD A,(p_cache_slot)
    LD L,A
    LD H,0
    DUP 4
    ADD HL,HL
    EDUP
    LD A,(p_cache_group)
    ADD A,A
    ADD A,A
    ADD A,$D0
    ADD A,H
    LD H,A
    EX DE,HL
    LD HL,p_cache_scratch
    LD BC,16
    LDIR
    LD A,(p_cache_group)
    LD L,A
    LD H,0
    DUP 6
    ADD HL,HL
    EDUP
    LD DE,$CB00
    ADD HL,DE
    LD A,(p_cache_slot)
    LD E,A
    LD D,0
    ADD HL,DE
    LD A,(p_cache_hash)
    LD (HL),A
    LD A,1
    LD (p_cache_miss),A
presentation_cache_mark:
    LD A,(p_cache_slot)
    AND 7
    LD E,A
    LD D,0
    LD HL,p_cache_bit_masks
    ADD HL,DE
    LD E,(HL)
    LD A,(p_cache_slot)
    RRCA
    RRCA
    RRCA
    AND 7
    LD D,A
    LD A,(p_cache_group)
    ADD A,A
    ADD A,A
    ADD A,A
    ADD A,D
    ADD A,p_cache_used&255
    LD L,A
    LD H,p_cache_used/256
    LD A,(HL)
    OR E
    LD (HL),A
    LD A,(p_cache_slot)
    LD B,A
    LD A,(p_cache_group)
    CP 3
    LD A,B
    JR C,.first_generation
    ADD A,64
.first_generation:
    OR A
    RET
p_cache_bit_masks:
    DB 1,2,4,8,16,32,64,128
