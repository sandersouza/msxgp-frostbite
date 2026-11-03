; Exact four-byte sortedPGT pair pool. Per-strip colour/background/type are
; implicit; published slot metadata still retains its full six-byte key.
p_fp_count EQU $C2D3
p_fp_hash EQU $C2C8
p_fp_slot EQU $C2D6
p_fp_heads EQU $E280
p_fp_links EQU $E290
p_fp_keys EQU $E2A0
p_fp_key EQU $E2E0

p_fixed_pool_init:
    XOR A
    LD (p_fp_count),A
    LD HL,p_fp_heads
    LD DE,p_fp_heads+1
    LD BC,15
    LD (HL),255
    LDIR
    XOR A
    RET

p_fixed_pool_resolve:
    LD A,(p_fp_count)
    CP 17
    JP NC,.fail
    LD HL,p_fp_key
    LD A,(HL)
    INC HL
    XOR (HL)
    INC HL
    XOR (HL)
    INC HL
    XOR (HL)
    AND 15
    LD (p_fp_hash),A
    ADD A,p_fp_heads&255
    LD L,A
    LD H,p_fp_heads/256
    LD A,(HL)
    LD B,16                 ;corrupt chains cannot loop indefinitely
.lookup:
    CP 255
    JR Z,.allocate
    LD HL,p_fp_count
    CP (HL)
    JR NC,.fail
    LD (p_fp_slot),A
    ADD A,A
    ADD A,A
    ADD A,p_fp_keys&255
    LD L,A
    LD H,p_fp_keys/256
    LD DE,p_fp_key
    DUP 4
    LD A,(DE)
    CP (HL)
    JR NZ,.different
    INC DE
    INC HL
    EDUP
    LD A,(p_fp_slot)
    OR A
    RET
.different:
    DEC B
    JR Z,.fail
    LD A,(p_fp_slot)
    ADD A,p_fp_links&255
    LD L,A
    LD H,p_fp_links/256
    LD A,(HL)
    JR .lookup
.allocate:
    LD A,(p_fp_count)
    CP 16
    JR NC,.fail
    LD (p_fp_slot),A
    ADD A,A
    ADD A,A
    ADD A,p_fp_keys&255
    LD E,A
    LD D,p_fp_keys/256
    LD HL,p_fp_key
    LD BC,4
    LDIR
    LD A,(p_fp_hash)
    ADD A,p_fp_heads&255
    LD L,A
    LD H,p_fp_heads/256
    LD A,(HL)
    PUSH AF
    LD A,(p_fp_slot)
    ADD A,p_fp_links&255
    LD E,A
    LD D,p_fp_links/256
    POP AF
    LD (DE),A
    LD A,(p_fp_slot)
    LD (HL),A
    LD HL,p_fp_count
    INC (HL)                ;publish only after the key and links are complete
    LD A,(p_fp_slot)
    OR A
    RET
.fail:
    LD A,255
    SCF
    RET
