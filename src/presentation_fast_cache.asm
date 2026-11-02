; Metadata-only exact6-byte constructor cache. CRC8 is a bucket index only;
; every candidate compares all6bytes. Live names own refcounts and bitmap.
; Onlyref0slots evict; unlink old bucket before replacement. Pixel values are
; constructed/uploaded by caller onMISS, with no redundant16-byteRAMshadow.
pf_counts EQU $CCA0
pf_miss EQU $CCA6
pf_group EQU $CCA7
pf_hash EQU $CCA8
pf_slot EQU $CCA9
pf_count EQU $CCAA
pf_keybase EQU $CCAB
pf_headptr EQU $CCAD
pf_used EQU $CCB0
pf_nextbase EQU $CCE2
pf_previous EQU $CCE4
pf_key EQU $CC90
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
    LD HL,pf_used
    LD DE,pf_used+1
    LD BC,47
    LD (HL),A
    LDIR
    LD HL,$DB00
    LD DE,$DB01
    LD BC,1535
    LD (HL),255
    LDIR
    XOR A
    RET

p_fast_resolve:
    CP 6
    JP NC,p_fast_fail
    LD (pf_group),A
    XOR A
    LD (pf_miss),A
    LD B,A
    LD IX,pf_key
    LD H,p_fast_crc_data/256
    DUP 6
    LD A,(IX)
    XOR B
    LD L,A
    LD A,(HL)
    LD B,A
    INC IX
    EDUP
    LD (pf_hash),A
    LD A,(pf_group)
    LD L,A
    LD H,0
    DUP 6
    ADD HL,HL
    EDUP
    LD DE,$D900
    ADD HL,DE
    LD (pf_nextbase),HL
    LD A,(pf_group)
    ADD A,A
    LD E,A
    LD D,0
    LD HL,p_fast_key_roots
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    LD (pf_keybase),DE
    LD A,(pf_group)
    LD E,A
    LD D,0
    LD HL,pf_counts
    ADD HL,DE
    LD A,(HL)
    LD (pf_count),A
    LD A,(pf_group)
    ADD A,$DB
    LD H,A
    LD A,(pf_hash)
    LD L,A
    LD (pf_headptr),HL
    LD A,(HL)
.lookup:
    CP 255
    JP Z,p_fast_allocate
    CP 64
    JP NC,p_fast_fail
    LD (pf_slot),A
    CALL p_fast_key_pointer
    LD DE,pf_key
    DUP 6
    LD A,(DE)
    CP (HL)
    JP NZ,.different
    INC DE
    INC HL
    EDUP
    JP p_fast_identifier
.different:
    LD A,(pf_slot)
    CALL p_fast_next_pointer
    LD A,(HL)
    JR .lookup

p_fast_allocate:
    LD A,(pf_group)
    DUP 3
    ADD A,A
    EDUP
    ADD A,pf_used&255
    LD L,A
    LD H,pf_used/256
    LD D,0
    LD B,8
.byte:
    LD A,(HL)
    CP 255
    JR NZ,.partial
    INC HL
    LD A,D
    ADD A,8
    LD D,A
    DJNZ .byte
    JP p_fast_fail
.partial:
    LD C,A
    LD E,1
.bit:
    LD A,C
    AND E
    JR Z,.selected
    INC D
    SLA E
    JR .bit
.selected:
    LD A,D
    LD (pf_slot),A
    LD HL,pf_count
    CP (HL)
    JR NC,.extend
    CALL p_fast_unlink
    RET C
    JR .key
.extend:
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
    LD BC,6
    LDIR
    CALL p_fast_signature_pointer
    LD A,(pf_hash)
    LD (HL),A
    LD HL,(pf_headptr)
    LD A,(HL)
    PUSH AF
    LD A,(pf_slot)
    CALL p_fast_next_pointer
    POP AF
    LD (HL),A
    LD HL,(pf_headptr)
    LD A,(pf_slot)
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
    LD A,(pf_slot)
    LD L,A
    LD H,0
    LD E,L
    LD D,H
    ADD HL,HL
    ADD HL,DE
    ADD HL,HL
    LD DE,(pf_keybase)
    ADD HL,DE
    RET
p_fast_next_pointer:
    LD E,A
    LD D,0
    LD HL,(pf_nextbase)
    ADD HL,DE
    RET
p_fast_signature_pointer:
    LD A,(pf_group)
    LD L,A
    LD H,0
    DUP 6
    ADD HL,HL
    EDUP
    LD A,(pf_slot)
    LD E,A
    LD D,0
    ADD HL,DE
    LD DE,$CB00
    ADD HL,DE
    RET
p_fast_unlink:
    CALL p_fast_signature_pointer
    LD E,(HL)
    LD A,(pf_group)
    ADD A,$DB
    LD H,A
    LD L,E
.search:
    LD (pf_previous),HL
    LD A,(HL)
    CP 64
    JP NC,p_fast_fail
    LD B,A
    LD A,(pf_slot)
    CP B
    LD A,B
    JR Z,.remove
    CALL p_fast_next_pointer
    JR .search
.remove:
    CALL p_fast_next_pointer
    LD A,(HL)
    LD HL,(pf_previous)
    LD (HL),A
    OR A
    RET

; Kept as the constructor completion ABI; no pixel shadow is required.
p_fast_store:
    RET

; A=group, C=ID. Generationbit must match its owning name-page.
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
    OR A
    JR NZ,.live
    INC (HL)
    CALL p_fast_bitmap_pointer
    LD A,(HL)
    OR E
    LD (HL),A
    XOR A
    RET
.live:
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
    JR NZ,.done
    CALL p_fast_bitmap_pointer
    LD A,E
    CPL
    AND (HL)
    LD (HL),A
.done:
    XOR A
    RET
p_fast_bitmap_pointer:
    LD A,C
    AND 7
    LD E,A
    LD D,0
    LD HL,p_fast_bits
    ADD HL,DE
    LD E,(HL)
    LD A,C
    DUP 3
    RRCA
    EDUP
    AND 7
    LD D,A
    LD A,B
    DUP 3
    ADD A,A
    EDUP
    ADD A,D
    ADD A,pf_used&255
    LD L,A
    LD H,pf_used/256
    RET
p_fast_fail:
    LD A,2
    LD (pf_miss),A
    LD A,255
    SCF
    RET
p_fast_key_roots:
    DW $D000,$D180,$D300,$D480,$D600,$D780
p_fast_bits:
    DB 1,2,4,8,16,32,64,128
    ALIGN 256
p_fast_crc_data:
    INCBIN "cache-crc.bin"
