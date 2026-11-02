; Complete source-derived floe strip, BEFORE interning any physical tile.
; A=root0..159, B=signed delta-11..19, C=target Y0..185. CF=error.
; All copies/planes contribute to a64-cell grid: count + sorted unique IDs.
; Empty/one-ID cells deliberately retain their unused ID bytes.
p_ff_counts EQU $E200
p_ff_first EQU $E300
p_ff_second EQU $E400
p_ff_copy EQU $C2EB
p_ff_root EQU $C2EC
p_ff_delta EQU $C2ED
p_ff_y EQU $C2EE
p_ff_plane EQU $C2EF
p_ff_group EQU $C2F0
p_ff_origin EQU $C2F1
p_ff_index EQU $C2F2
p_ff_grow EQU $C2F3
p_ff_gcol EQU $C2F4
p_ff_ptr EQU $C2F5
p_ff_cell EQU $C2F7
p_ff_id EQU $C2F8
p_ff_error EQU $C2FA

p_fixed_floe_build:
    CP 160
    JP NC,p_fixed_floe_fail
    LD (p_ff_root),A
    LD A,B
    ADD A,11
    CP 31
    JP NC,p_fixed_floe_fail
    LD A,B
    LD (p_ff_delta),A
    LD A,C
    CP 186
    JP NC,p_fixed_floe_fail
    LD (p_ff_y),A
    XOR A
    LD (p_ff_error),A
    LD (p_ff_copy),A
    LD HL,p_ff_counts
    LD DE,p_ff_counts+1
    LD BC,63
    LD (HL),A
    LDIR
.copy:
    XOR A
    LD (p_ff_plane),A
.plane:
    ; Proper signed16-bit modular arithmetic: negative source positions
    ; wrap at160, never at256. No gameplay state is written.
    LD A,(p_ff_root)
    LD L,A
    LD H,0
    LD A,(p_ff_copy)
    LD E,A
    LD D,H
    ADD HL,DE
    LD A,(p_ff_plane)
    OR A
    JR Z,.no_shift
    LD A,(p_ff_delta)
    LD E,A
    ADD A,A
    SBC A,A
    LD D,A
    ADD HL,DE
.no_shift:
    LD DE,-8
    ADD HL,DE
    BIT 7,H
    JR Z,.nonnegative
    LD DE,160
    ADD HL,DE
.nonnegative:
    LD A,L
    CP 160
    JR C,.wrapped
    SUB 160
.wrapped:
    LD L,A
    AND 15
    DUP 3
    ADD A,A
    EDUP
    LD C,A
    LD A,(p_ff_y)
    AND 7
    OR C
    LD C,A
    ; NAME origin=1+floor(3*x/16), including transparent8-source prefix.
    LD H,0
    LD E,L
    LD D,H
    ADD HL,HL
    ADD HL,DE
    DUP 4
    SRL H
    RR L
    EDUP
    INC L
    LD A,L
    LD (p_ff_origin),A
    LD B,0
    LD A,(p_ff_delta)
    CP 9
    JR NC,.group
    LD B,A
.group:
    LD A,1
    CALL p_fast_geometry_lookup
    JP C,p_fixed_floe_fail
    LD HL,p_geo_ids
    LD (p_ff_ptr),HL
    XOR A
    LD (p_ff_grow),A
.grid_row:
    XOR A
    LD (p_ff_gcol),A
.grid_col:
    LD HL,(p_ff_ptr)
    LD E,(HL)
    INC HL
    LD D,(HL)
    INC HL
    LD (p_ff_ptr),HL
    LD A,D
    OR E
    JR Z,.next_col
    LD (p_ff_id),DE
    LD A,(p_ff_gcol)
    LD B,A
    LD A,(p_ff_origin)
    ADD A,B
    CP 31
    JR C,.column
    SUB 30
.column:
    CP 2
    JR C,.next_col
    LD B,A
    LD A,(p_ff_grow)
    DUP 5
    ADD A,A
    EDUP
    ADD A,B
    CALL p_fixed_floe_insert
    RET C
.next_col:
    LD A,(p_ff_gcol)
    INC A
    LD (p_ff_gcol),A
    LD B,A
    LD A,(p_geo_columns)
    CP B
    JR NZ,.grid_col
    LD A,(p_ff_grow)
    INC A
    LD (p_ff_grow),A
    LD B,A
    LD A,(p_geo_rows)
    CP B
    JR NZ,.grid_row
    LD A,(p_ff_delta)
    CP 9
    JR C,.next_copy
    LD A,(p_ff_plane)
    OR A
    JR NZ,.next_copy
    INC A
    LD (p_ff_plane),A
    JP .plane
.next_copy:
    LD A,(p_ff_copy)
    ADD A,32
    LD (p_ff_copy),A
    CP 96
    JP C,.copy
    XOR A
    RET

; A=relative cell, p_ff_id=nonzero uint16. At most two DISTINCT IDs.
p_fixed_floe_insert:
    LD (p_ff_cell),A
    LD L,A
    LD H,p_ff_counts/256
    LD A,(HL)
    OR A
    JR NZ,.existing
    INC (HL)
    LD A,L
    ADD A,A
    LD L,A
    LD H,p_ff_first/256
    LD DE,(p_ff_id)
    LD (HL),E
    INC HL
    LD (HL),D
    OR A
    RET
.existing:
    LD B,A
    LD A,L
    ADD A,A
    LD L,A
    LD H,p_ff_first/256
    LD E,(HL)
    INC HL
    LD D,(HL)
    LD HL,(p_ff_id)
    OR A
    SBC HL,DE
    RET Z
    LD A,B
    DEC A                   ;DEC preserves the16-bit comparison's carry
    JR NZ,.second
    ; First DE and new p_ff_id ordered by the just-computed16-bit compare.
    JR NC,.ordered
    LD HL,(p_ff_id)
    LD (p_ff_id),DE
    EX DE,HL
.ordered:
    LD A,(p_ff_cell)
    LD L,A
    LD H,p_ff_counts/256
    INC (HL)
    ADD A,A
    LD L,A
    LD H,p_ff_first/256
    LD (HL),E
    INC HL
    LD (HL),D
    DEC L
    LD H,p_ff_second/256
    LD DE,(p_ff_id)
    LD (HL),E
    INC HL
    LD (HL),D
    OR A
    RET
.second:
    LD A,(p_ff_cell)
    ADD A,A
    LD L,A
    LD H,p_ff_second/256
    LD E,(HL)
    INC HL
    LD D,(HL)
    LD HL,(p_ff_id)
    OR A
    SBC HL,DE
    RET Z
p_fixed_floe_fail:
    LD A,1
    LD (p_ff_error),A
    SCF
    RET
