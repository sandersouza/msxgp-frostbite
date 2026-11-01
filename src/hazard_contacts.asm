; Actual original-clock contacts. Source sprites/VDP flags are not gameplay data.
; Scratch C790..C79F is outside canonical source RAM and other owned ABIs.
hazard_x EQU $C793
hazard_y EQU $C794
hazard_px EQU $C799
hazard_leaf EQU $C79E

hazard_acquire:
    CALL hazard_shore
    LD IX,$C023
    LD IY,$C031
    LD B,78
    CALL hazard_row
    INC IX
    INC IY
    INC IY
    LD B,52
    CALL hazard_row
    INC IX
    INC IY
    INC IY
    LD B,26
    CALL hazard_row
    INC IX
    INC IY
    INC IY
    LD B,0
    JP hazard_row

hazard_shore:
    LD A,($C064)
    CP hazard_shore_min_y
    RET C
    CP hazard_shore_max_y+1
    RET NC
    SUB 3                  ; captured shore Y4..56 → index1..53
    LD (hazard_y),A
    LD A,($C068)
    CP 160
    JP NC,core_fault
    LD (hazard_x),A
    LD A,($C06F)
    CP 8
    JP NC,core_fault
    LD E,A
    LD D,0
    LD HL,hazard_bear_index
    ADD HL,DE
    LD E,(HL)
    LD A,($C06C)
    RRCA
    RRCA
    RRCA
    RRCA
    AND 1
    OR E
    LD L,A
    LD H,0
    LD BC,hazard_shore_modes
    LD A,($C066)
    CALL hazard_lookup
    BIT 7,A
    RET Z                  ; source ED remains sticky on a nonnegative read
    LD ($C06D),A
    RET

hazard_row:
    LD (IY+0),7
    LD A,($C064)
    SUB B
    RET C
    CP hazard_row_min_y
    RET C
    CP hazard_row_max_y+1
    RET NC
    SUB 31                 ; captured row Y32..65 → index1..34
    LD (hazard_y),A
    LD A,(IX+0)
    LD L,A
    LD H,hazard_shape_index/256
    LD A,(HL)
    CP 255
    JP Z,core_fault
    LD L,A
    LD H,0
    ADD HL,HL              ; shape*2 plus original P1 reflection
    LD A,(IX-18)
    RLCA
    JR NC,.shape
    INC HL
.shape:
    LD A,(IX+53)           ; D8..DB: zero still draws one original copy
    CP 4
    JP NC,core_fault
    LD C,A
    LD A,($C066)
    CP 160
    JP NC,core_fault
    CP 9
    JR C,.edge_left
    CP 152
    JR NC,.edge_right
    PUSH AF
    LD A,($C066)
    SUB (IX+49)            ; D4..D7 object coordinate
    JR NC,.distance
    ADD A,160
.distance:
    LD D,A
    CALL hazard_copy_distance
    JR C,.ordinary_hit
    BIT 0,C                ; NUSIZ1/3: copy+16
    JR Z,.copy32
    LD A,D
    SUB 16
    JR NC,.distance16
    ADD A,160
.distance16:
    CALL hazard_copy_distance
    JR C,.ordinary_hit
.copy32:
    BIT 1,C                ; NUSIZ2/3: copy+32
    JR Z,.ordinary_miss
    LD A,D
    SUB 32
    JR NC,.distance32
    ADD A,160
.distance32:
    CALL hazard_copy_distance
    JR C,.ordinary_hit
.ordinary_miss:
    POP AF
    RET
.ordinary_hit:
    LD (hazard_x),A
    POP AF
    CP 25
    JR C,.ordinary_exception
    LD BC,hazard_ordinary_common_modes
    CALL hazard_lookup_common
    LD (IY+0),A
    RET
.ordinary_exception:
    LD BC,hazard_ordinary_modes
    SUB 9
    CALL hazard_lookup
    LD (IY+0),A
    RET
.edge_right:
    SUB 143                ; physical152..159 → edge index9..16
.edge_left:
    LD (hazard_px),A
    ADD HL,HL
    ADD HL,HL              ; (shape*2+reflection)*4 plus source NUSIZ
    LD E,C
    LD D,0
    ADD HL,DE
    LD A,(IX+49)
    CP 160
    JP NC,core_fault
    LD (hazard_x),A
    LD A,(hazard_px)
    LD BC,hazard_edge_modes
    CALL hazard_lookup
    LD (IY+0),A
    RET

; Candidate copy clocks are admitted only after the complete source alias gate.
; A = modulo160 distance. On hit return C1, A=distance+7 in0..14.
; HL(mode), C(NUSIZ), D(original distance) are preserved.
hazard_copy_distance:
    CP 8
    JR C,.hit
    CP 153
    JR C,.miss
    SUB 160
.hit:
    ADD A,7
    SCF
    RET
.miss:
    OR A
    RET

; HL=mode (16bit), BC=resident directory, A=player index.
hazard_lookup:
    LD (hazard_px),A
    LD D,H
    LD E,L
    ADD HL,HL
    ADD HL,DE
    ADD HL,BC
    CALL floe_deref
    LD A,(hazard_px)
    LD E,A
    LD D,0
    ADD HL,DE
    SLA E
    RL D
    ADD HL,DE
    CALL floe_deref
hazard_lookup_y:
    LD A,(hazard_y)
    LD E,A
    LD D,0
    ADD HL,DE
    SLA E
    RL D
    ADD HL,DE
    CALL floe_deref
    LD A,(hazard_x)
    LD E,A
    JP contact_compact

; Compiler proves the complete raw profiles at PX25..151 byte-identical.
; Resident mode pointers skip the banked player directory for that range.
hazard_lookup_common:
    LD D,H
    LD E,L
    ADD HL,HL
    ADD HL,DE
    ADD HL,BC
    CALL floe_deref
    JP hazard_lookup_y

; HL=mapped five-byte nibble-rank row root, E=source coordinate0..159.
; The immutable verified tables keep every record/block in a bank-local32B slot.
; Returns the exact source electrical byte. IX/IY are preserved.
contact_compact:
    LD B,H
    LD C,L
    LD A,E
    AND 15
    LD (hazard_leaf),A
    LD A,E
    RRCA
    RRCA
    RRCA
    RRCA
    AND 15
    LD D,A
    RRCA
    AND 7
    LD E,A
    LD A,D
    LD D,0
    ADD HL,DE
    RRCA
    LD A,(HL)
    JR NC,.low
    RRCA
    RRCA
    RRCA
    RRCA
.low:
    AND 15
    JR Z,.zero
    ADD A,A
    ADD A,3                ; first reference starts at root+5
    LD E,A
    LD H,B
    LD L,C
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    LD A,D
    SRL A
    ADD A,contact_block_bank
    LD ($7000),A
    CALL contact_slot
    LD A,(hazard_leaf)
    ADD A,A
    LD E,A
    LD D,0
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    LD A,D
    SRL A
    ADD A,contact_record_bank
    LD ($7000),A
    CALL contact_slot
    LD DE,29
    ADD HL,DE
    LD A,(HL)
    OR 7
    LD C,A
    OR A
    SBC HL,DE
    LD A,(floe_viewbyte)
    LD E,A
    LD D,0
    ADD HL,DE
    LD A,(floe_viewmask)
    AND (HL)
    LD A,C
    RET Z
    OR 128
    RET
.zero:
    LD A,7
    RET

contact_slot:
    EX DE,HL
    ADD HL,HL
    ADD HL,HL
    ADD HL,HL
    ADD HL,HL
    ADD HL,HL
    LD A,H
    AND 63
    OR 128
    LD H,A
    RET
