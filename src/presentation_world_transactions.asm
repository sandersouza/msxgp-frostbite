; Private K decoder. Caller already selected one of eight fixed physical roles
; and checked the immutable program identity. No generic public ABI is removed.
    INCLUDE "symbols.inc"
    ORG v_origin
v_decode:
    PUSH DE                 ;immutable sixty-byte cache destination
    LD HL,(k_pointer)
    LD A,L
    SUB k_programs&255
    LD B,A                  ;owner0..7 from the validated K wrapper
    SRL A
    ADD A,116
    PUSH AF                 ;directory bank, two 1KiB owners per 2KiB tail
    LD A,B
    AND 1
    ADD A,A
    ADD A,A
    LD H,A
    LD L,0
    LD A,(p_tl_program)
    LD E,A
    LD D,0
    ADD HL,DE
    ADD HL,DE
    ADD HL,DE
    ADD HL,DE
    LD DE,$B800
    ADD HL,DE
    POP AF
    CALL t_mapper
    LD C,(HL)
    INC HL
    LD B,(HL)
    INC HL
    LD A,(HL)
    OR A
    JR Z,.missing
    CALL t_mapper
    LD H,B
    LD L,C
    POP DE
    LD BC,60
    LDIR
    XOR A
    RET
.missing:
    POP DE
    SCF
    RET
v_end:
    ASSERT $ <= $F000

; The row driver selected the fixed actor role and a dirty NAME row. Hold
; cursors in registers; materialize the original context only for fusion.
v_cells:
    LD A,(p_w_index)
    LD B,A
    LD A,(v_mask)
    INC B
    JR .mask_test
.mask_shift:
    SRL A
.mask_test:
    DJNZ .mask_shift
    LD (v_rowmask),A
    LD HL,(p_w_name)
    LD A,(p_w_col)
    LD D,A
    LD A,(qe_roleid)
    LD E,A
    LD A,(p_geo_columns)
    LD B,A
    LD C,0
.cell:
    LD A,(v_rowmask)
    SRL A
    LD (v_rowmask),A
    JR NC,.next
    LD A,D
    CP 2
    JR C,.next
    LD A,(HL)
    CP 128
    JR C,.fuse
    LD (HL),E
    LD A,E
    LD (p_w_tile),A
    JR .next
.fuse:
    LD (p_w_name),HL
    LD A,D
    LD (p_w_col),A
    LD A,C
    LD (p_w_line),A
    PUSH BC
    PUSH DE
    PUSH HL
    LD A,(p_w_group)
    LD B,A
    LD A,(pfw_geo_variant)
    LD C,A
    XOR A
    CALL qe_geometry          ;rare exact typed fusion needs the original IDs
    JP C,p_world_fail
    POP HL
    POP DE
    POP BC
    PUSH BC
    PUSH DE
    PUSH HL
    LD A,(p_w_index)
    ADD A,C
    ADD A,A
    LD L,A
    LD H,0
    LD DE,p_geo_ids
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    LD (pfw_id),DE
    CALL qe_fuse
    POP HL
    POP DE
    POP BC
    JP C,p_world_fail
.next:
    INC E
    INC C
    INC D
    LD A,D
    CP 31
    JR C,.advance
    LD D,1
    LD HL,(qe_rowbase)
    INC HL
    JR .pointer
.advance:
    INC HL
.pointer:
    DJNZ .cell
    LD (p_w_name),HL
    LD A,D
    LD (p_w_col),A
    LD A,C
    LD (p_w_line),A
    LD HL,p_w_index
    ADD A,(HL)
    LD (HL),A
    JP qe_nextrow
v_cells_end:
    ASSERT $ <= $F000


; One immutable byte describes complete descriptor dimensions and nonzero IDs.
; The full original descriptor remains the independent fusion fallback.
v_mask EQU $E834
v_rowmask EQU $E835
v_geometry:
    LD A,C
    LD (pfw_geo_variant),A
    LD A,B
    DUP 4
    SRL A
    EDUP
    ADD A,142
    PUSH AF
    LD A,B
    AND 15
    LD L,A
    LD H,0
    DUP 7
    ADD HL,HL
    EDUP
    LD E,C
    LD D,0
    ADD HL,DE
    LD DE,$B800
    ADD HL,DE
    POP AF
    CALL t_mapper
    LD B,(HL)
    LD A,B
    AND 63
    LD (v_mask),A
    BIT 6,B
    LD A,2
    JR Z,.columns
    INC A
.columns:
    LD (p_geo_columns),A
    BIT 7,B
    LD A,1
    JR Z,.rows
    INC A
.rows:
    LD (p_geo_rows),A
    XOR A
    LD (pfw_geo_valid),A       ;a later full lookup must not reuse stale IDs
    LD A,7
    CALL t_mapper
    XOR A
    RET
v_geometry_end:
    ASSERT $ <= $F000
