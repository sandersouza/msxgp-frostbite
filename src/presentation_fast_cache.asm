; Exact5-byte constructor-key cache. Signatures only select candidates; all5
; bytes are compared. Names own references; only zero-reference slots evict.
; Resident code, no VDP/PSG/mapper/slot/canonicalCPU writes.
pf_counts EQU $CCA0
pf_miss EQU $CCA6
pf_group EQU $CCA7
pf_hash EQU $CCA8
pf_slot EQU $CCA9
pf_count EQU $CCAA
pf_sigptr EQU $CCAD
pf_key EQU $CC90
pf_image EQU $CC80
pf_refs EQU $C080

p_fast_init:
    XOR A
    LD (pf_miss),A
    LD HL,pf_counts
    LD DE,pf_counts+1
    LD BC,5
    LD (HL),A
    LDIR
    LD HL,pf_refs
    LD DE,pf_refs+1
    LD BC,383
    LD (HL),A
    LDIR
    XOR A
    RET

; A=group0..5, pf_key=immutable exactconstructor5bytes. Return ID0..127,
; miss0=hit/1=allocated/2=reject. New caller must construct/store full16bytes
; and acquire a live name reference before another resolve can evict it.
p_fast_resolve:
    CP 6
    JP NC,p_fast_fail
    LD (pf_group),A
    XOR A
    LD (pf_miss),A
    LD HL,pf_key
    DUP 5
    ADD A,(HL)
    RLCA
    INC HL
    EDUP
    LD (pf_hash),A
    LD A,(pf_group)
    LD L,A
    LD H,0
    DUP 6
    ADD HL,HL
    EDUP
    LD DE,$CB00
    ADD HL,DE
    LD (pf_sigptr),HL
    LD A,(pf_group)
    LD E,A
    LD D,0
    LD HL,pf_counts
    ADD HL,DE
    LD A,(HL)
    LD (pf_count),A
    LD C,A
    LD B,0
    OR A
    JP Z,p_fast_allocate
    LD HL,(pf_sigptr)
.lookup:
    LD A,(pf_hash)
    CPIR
    JP NZ,p_fast_allocate
    PUSH BC
    PUSH HL
    LD A,L
    DEC A
    AND 63
    LD (pf_slot),A
    CALL p_fast_key_pointer
    LD DE,pf_key
    DUP 5
    LD A,(DE)
    CP (HL)
    JP NZ,.different
    INC DE
    INC HL
    EDUP
    POP HL
    POP BC
    JP p_fast_identifier
.different:
    POP HL
    POP BC
    LD A,B
    OR C
    JR NZ,.lookup
    JP p_fast_allocate

p_fast_allocate:
    LD A,(pf_group)
    LD L,A
    LD H,0
    DUP 6
    ADD HL,HL
    EDUP
    LD DE,pf_refs
    ADD HL,DE
    LD BC,64
    XOR A
    CPIR
    JP NZ,p_fast_fail
    LD A,L
    DEC A
    AND 63
    LD (pf_slot),A
    LD HL,pf_count
    CP (HL)
    JR C,.key
    LD A,(pf_group)
    LD E,A
    LD D,0
    LD HL,pf_counts
    ADD HL,DE
    INC (HL)
.key:
    CALL p_fast_key_pointer
    EX DE,HL
    LD HL,pf_key
    LD BC,5
    LDIR
    LD HL,(pf_sigptr)
    LD A,(pf_slot)
    LD E,A
    LD D,0
    ADD HL,DE
    LD A,(pf_hash)
    LD (HL),A
    LD A,1
    LD (pf_miss),A
p_fast_identifier:
    LD A,(pf_slot)
    LD B,A
    LD A,(pf_group)
    CP 3
    LD A,B
    JR C,.ready
    ADD A,64
.ready:
    OR A
    RET

p_fast_key_pointer:
    LD A,(pf_group)
    ADD A,A
    LD E,A
    LD D,0
    LD HL,p_fast_key_roots
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    PUSH DE
    LD A,(pf_slot)
    LD L,A
    LD H,0
    LD C,L
    LD B,H
    ADD HL,HL
    ADD HL,HL
    ADD HL,BC
    POP DE
    ADD HL,DE
    RET

; Separate deferred construction permits hits without generating pixels.
p_fast_store:
    LD A,(pf_slot)
    LD L,A
    LD H,0
    DUP 4
    ADD HL,HL
    EDUP
    LD A,(pf_group)
    ADD A,A
    ADD A,A
    ADD A,$D0
    ADD A,H
    LD H,A
    EX DE,HL
    LD HL,pf_image
    LD BC,16
    LDIR
    RET

; A=group, C=bank-localID. Generationbit must match the owning names page.
p_fast_ref_address:
    CP 6
    JP NC,p_fast_fail
    LD B,A
    LD A,C
    CP 128
    JP NC,p_fast_fail
    LD A,B
    CP 3
    LD A,C
    JR C,.first
    CP 64
    JP C,p_fast_fail
    JR .slot
.first:
    CP 64
    JP NC,p_fast_fail
.slot:
    AND 63
    LD E,A
    LD D,0
    LD L,B
    LD H,0
    DUP 6
    ADD HL,HL
    EDUP
    ADD HL,DE
    LD DE,pf_refs
    ADD HL,DE
    OR A
    RET
p_fast_ref_add:
    CALL p_fast_ref_address
    RET C
    LD A,(HL)
    CP 255
    JP Z,p_fast_fail
    INC (HL)
    XOR A
    RET
p_fast_ref_drop:
    CALL p_fast_ref_address
    RET C
    LD A,(HL)
    OR A
    JP Z,p_fast_fail
    DEC (HL)
    XOR A
    RET
p_fast_fail:
    LD A,2
    LD (pf_miss),A
    LD A,255
    SCF
    RET
p_fast_key_roots:
    DW $E800,$E940,$EA80,$EBC0,$ED00,$EE40
