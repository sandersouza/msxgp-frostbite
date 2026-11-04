; Internal native-band feasibility replacement. Enemy-only entry from I.
; All data/state semantics remain M-C; resident callers never execute banked
; code after a helper has changed the mapping without restoring its code bank.
    INCLUDE "symbols.inc"
    ORG $4B6E
n_entry:
    LD A,n_code_bank
    LD ($7000),A
    JP n_primitive
n_geometry:
    CALL p_fast_geometry_lookup
    JR n_restore
n_actor:
    CALL i_actor
    JR n_restore
n_fuse:
    CALL p_template_object_fuse
n_restore:
    PUSH AF
    LD A,n_code_bank
    LD ($7000),A
    POP AF
    RET
n_resident_end:
    ASSERT $ <= $4C00

    ORG n_code_origin
n_meta EQU $C1D1
n_tile EQU $C1D3
n_water EQU $C1D4
n_scratch_end EQU $C1D5
n_primitive:
    LD A,(p_w_copy)
    OR A
    JR NZ,.ready
    LD (i_valid),A
.ready:
    LD A,1
    LD (i_active),A
    LD A,(p_w_color)
    CP 4
    JP Z,n_done
    CALL p_fast_primitive_dirty
    JP Z,n_done
    LD A,(p_w_copy)
    OR A
    CALL Z,p_fast_clear_memo
    LD A,(p_w_x)
    AND 15
    ADD A,A
    ADD A,A
    ADD A,A
    LD B,A
    LD A,(p_w_y)
    AND 7
    OR B
    LD C,A
    LD A,(p_w_group)
    LD B,A
    XOR A
    CALL n_geometry
    JP C,n_fail
    LD A,(p_w_x)
    LD L,A
    LD H,0
    LD DE,n_columns
    ADD HL,DE
    LD A,(HL)
    LD (p_w_origin),A
    LD A,(p_w_y)
    SRL A
    SRL A
    SRL A
    LD (p_w_top),A
    XOR A
    LD (p_w_index),A
n_row:
    XOR A
    LD (p_w_line),A
    LD A,(p_w_origin)
    LD (p_w_col),A
    LD A,(p_w_top)
    CALL p_fast_row_dirty
    JR NZ,.dirty
    LD A,(p_geo_columns)
    LD B,A
    LD A,(p_w_index)
    ADD A,B
    LD (p_w_index),A
    JP n_next_row
.dirty:
    CALL p_fast_cell
    ; One fixed context per row, shared by every nonzero cell and copy.
    LD A,(p_w_top)
    ADD A,A
    ADD A,A
    LD B,A
    LD A,(PAGE)
    OR A
    LD A,B
    JR Z,.context
    ADD A,96
.context:
    LD L,A
    LD H,p_actor_contexts/256
    LD A,(HL)
    CP 3
    JP NC,n_fail
    LD (p_fx_bank),A
    ; Enemy contexts occupy only banks 1 and 2, water IDs 130 and 129.
    NEG
    ADD A,131
    LD (n_water),A
    INC L
    LD A,(HL)
    LD (n_tile),A
    INC L
    LD E,(HL)
    INC L
    LD D,(HL)
    LD (n_meta),DE
n_cell:
    LD A,(p_w_col)
    CP 31
    JR C,.bounded
    SUB 30
    LD (p_w_col),A
    CALL p_fast_cell
    LD A,(p_w_col)
.bounded:
    CP 2
    JP C,n_next_cell
    LD A,(p_w_index)
    ADD A,A
    ADD A,p_geo_ids&255
    LD L,A
    LD H,p_geo_ids/256
    LD E,(HL)
    INC L
    LD D,(HL)
    LD A,D
    OR E
    JP Z,n_next_cell
    LD (pfw_id),DE
    LD HL,(p_w_name)
    LD A,(HL)
    CP 128
    JR NC,.mono
    CALL n_fuse
    JP n_next_cell
.mono:
    LD A,(p_w_index)
    ADD A,pfw_memo&255
    LD L,A
    LD H,pfw_memo/256
    LD A,(HL)
    CP 255
    JR Z,.miss
    LD HL,(p_w_name)
    LD (HL),A
    CALL p_fixed_mark_object
    JP n_next_cell
.miss:
    LD DE,(pfw_id)
    LD (pf_key),DE
    LD A,(n_water)
    LD (pf_key+2),A
    XOR A
    LD (pf_key+3),A
    LD (pf_key+5),A
    LD A,(p_w_color)
    LD (pf_key+4),A
    LD A,(p_w_line)
    LD B,A
    LD A,(n_tile)
    ADD A,B
    LD (p_w_tile),A
    LD A,B
    ADD A,A
    LD E,A
    ADD A,A
    ADD A,E
    LD E,A
    LD D,0
    LD HL,(n_meta)
    ADD HL,DE
    CALL n_actor
    JP C,n_fail
    LD HL,(p_w_name)
    LD A,(p_w_tile)
    LD (HL),A
    CALL p_fixed_mark_object
    LD A,(p_w_index)
    ADD A,pfw_memo&255
    LD L,A
    LD H,pfw_memo/256
    LD A,(p_w_tile)
    LD (HL),A
n_next_cell:
    LD HL,p_w_index
    INC (HL)
    LD HL,p_w_name
    INC (HL)
    LD HL,p_w_col
    INC (HL)
    LD HL,p_w_line
    INC (HL)
    LD A,(p_geo_columns)
    CP (HL)
    JP NZ,n_cell
n_next_row:
    LD A,(p_geo_stride)
    SRL A
    LD B,A
    LD A,(p_w_index)
    CP B
    JR Z,n_done
    LD HL,p_w_top
    INC (HL)
    JP n_row
n_done:
    XOR A
    LD (i_active),A
    RET
n_fail:
    XOR A
    LD (i_active),A
    JP p_world_fail
n_columns:
    INCBIN "columns.bin"
n_end:
    ASSERT $ <= n_code_limit
