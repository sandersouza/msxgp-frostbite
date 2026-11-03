; Four exact seven-byte P0 keys per inactive generation. Metadata keeps the
; existing32-byte format. Selection does not upload VRAM or publish validity.
p_pc_way EQU $C297
p_pc_next EQU $E610
p_pc_patternbase EQU $E612
p_pc_total EQU $E613

p_player_variant_default:
    LD A,(PAGE)
    CP 2
    JP NC,p_player_variant_fail
    XOR A
    JP p_player_variant_set

p_player_variant_lookup:
    CALL p_player_variant_default
    RET C
.scan:
    LD A,(IX)
    CP 1
    JR NZ,.next
    LD HL,p_pc_key
    DUP 7,i
    LD A,(HL)
    CP (IX+1+i)
    JR NZ,.next
    INC L
    EDUP
    OR A
    RET
.next:
    LD A,(p_pc_way)
    INC A
    CP 4
    JR NC,.replace
    CALL p_player_variant_set
    JR .scan
.replace:
    LD A,(PAGE)
    ADD A,p_pc_next&255
    LD L,A
    LD H,p_pc_next/256
    LD A,(HL)
    AND 3
    LD B,A
    INC A
    AND 3
    LD (HL),A
    LD A,B
    CALL p_player_variant_set
    LD (IX),0               ;the old way is invalid before any future upload
    SCF
    RET

; An uncached P0 may need more than six patterns. Invalidate every way of the
; inactive generation before using its first contiguous slots for that frame.
p_player_variant_uncached:
    CALL p_player_variant_default
    RET C
    LD (IX),0
    LD (IX+32),0
    LD (IX+64),0
    LD (IX+96),0
    OR A
    RET

; Internal bounded way A0..3 after PAGE validation.
p_player_variant_set:
    LD (p_pc_way),A
    LD L,A
    LD H,0
    DUP 5
    ADD HL,HL
    EDUP
    LD A,(PAGE)
    OR A
    JR Z,.metadata
    LD DE,128
    ADD HL,DE
.metadata:
    LD DE,$C080
    ADD HL,DE
    LD (p_pc_pointer),HL
    PUSH HL
    POP IX
    LD A,(p_pc_way)
    LD B,A
    ADD A,A
    ADD A,B
    DUP 3
    ADD A,A
    EDUP
    LD B,A
    LD A,(PAGE)
    OR A
    LD A,B
    JR Z,.pattern
    ADD A,96
.pattern:
    LD (p_pc_patternbase),A
    OR A
    RET
p_player_variant_fail:
    SCF
    RET
