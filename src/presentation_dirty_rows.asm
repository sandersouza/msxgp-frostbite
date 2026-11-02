; Resident offscreen row transactions. Unchanged names keep their live owner;
; every dirty row releases its old owners before the background is replaced.
p_fd_loop EQU $C2CB
p_fd_program EQU $C2CC
p_fd_count EQU $C2CE
p_fd_cursor EQU $C2CF
p_fd_ids EQU $C2D0
p_fd_list EQU $E580

; Build the bounded sorted row list once. Three consumers then visit only
; set bits, rather than rescanning all24 rows for every transaction phase.
p_fast_collect_rows:
    LD DE,p_fd_list
    DUP 3,group_index
    LD A,(p_fd_rows+group_index)
    LD B,A
    DUP 8,bit_index
    BIT bit_index,B
    JR Z,$+6                ;skip LD A,n / LD(DE),A / INC DE (four bytes)
    LD A,group_index*8+bit_index
    LD (DE),A
    INC DE
    EDUP
    EDUP
    LD A,E
    SUB p_fd_list&255
    LD (p_fd_count),A
    RET

p_fast_list_row:
    LD A,(p_fd_cursor)
    ADD A,p_fd_list&255
    LD L,A
    LD H,p_fd_list/256
    LD A,(HL)
    LD (p_fd_loop),A
    RET

p_fast_rows_any:
    LD A,(p_fd_rows)
    LD B,A
    LD A,(p_fd_rows+1)
    OR B
    LD B,A
    LD A,(p_fd_rows+2)
    OR B
    RET

; A=SCREEN2 row0..23. Preserve every register except AF for cell walkers.
p_fast_row_dirty:
    PUSH BC
    PUSH DE
    PUSH HL
    LD C,A
    AND 7
    LD E,A
    LD D,0
    LD HL,p_fast_bits
    ADD HL,DE
    LD B,(HL)
    LD A,C
    DUP 3
    SRL A
    EDUP
    LD E,A
    LD HL,p_fd_rows
    ADD HL,DE
    LD A,(HL)
    AND B
    POP HL
    POP DE
    POP BC
    RET

p_fast_primitive_dirty:
    LD B,8
    LD A,(p_w_family)
    CP 1
    JR NZ,.bear
    LD B,7
.bear:
    CP 2
    JR NZ,.span
    LD B,20
.span:
    LD A,(p_w_y)
    LD C,A
    ADD A,B
    DEC A
    DUP 3
    SRL A
    EDUP
    LD B,A
    LD A,C
    DUP 3
    SRL A
    EDUP
    LD C,A
.row:
    LD A,C
    CALL p_fast_row_dirty
    RET NZ
    LD A,C
    CP B
    JR Z,.empty
    INC C
    JR .row
.empty:
    XOR A
    RET

p_fast_release_dirty:
    CALL p_fast_collect_rows
    OR A
    RET Z
    LD A,(p_fd_rows)
    CP 255
    JR NZ,.scan
    LD A,(p_fd_rows+1)
    CP 255
    JR NZ,.scan
    LD A,(p_fd_rows+2)
    CP 255
    JP Z,p_fast_begin_page
.scan:
    XOR A
    LD (p_fd_cursor),A
.row:
    CALL p_fast_list_row
    LD (p_w_top),A
    XOR A
    LD (p_w_col),A
    CALL p_fast_cell
    LD HL,(p_w_name)
    LD B,32
.cell:
    LD A,(HL)
    CP 128
    JR NC,.advance
    PUSH BC
    PUSH HL
    LD C,A
    LD A,(p_w_cachegroup)
    CALL p_fast_ref_drop
    POP HL
    POP BC
    JP C,p_world_fail
.advance:
    INC HL
    DJNZ .cell
    LD HL,p_fd_cursor
    INC (HL)
    LD A,(p_fd_count)
    CP (HL)
    JR NZ,.row
    RET

p_fast_background_rows:
    LD A,(p_fd_count)
    OR A
    RET Z
    LD A,1
    LD ($7000),A
    XOR A
    LD (p_fd_cursor),A
    LD A,(p_bg_profile)
    CP 32
    JR Z,.blank
    LD A,(p_bg_theme)
    ADD A,A
    LD L,A
    LD H,0
    LD DE,p_bg_roots
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    EX DE,HL
    LD (p_fd_program),HL
.row:
    CALL p_fast_list_row
    LD E,A
    LD D,0
    LD L,A
    LD H,D
    ADD HL,HL
    ADD HL,DE
    LD DE,(p_fd_program)
    ADD HL,DE
    LD A,(HL)
    LD (p_fd_ids),A
    INC HL
    LD A,(HL)
    LD (p_fd_ids+1),A
    INC HL
    LD A,(HL)
    LD (p_fd_ids+2),A
    LD A,(p_fd_loop)
    CP 3
    JR NZ,.fill
    LD A,(p_bg_profile)
    AND 28
    LD B,A
    LD A,(p_bg_theme)
    AND 1
    ADD A,A
    OR B
    LD L,A
    LD H,0
    LD DE,p_bg_gradient_data
    ADD HL,DE
    LD A,(HL)
    LD (p_fd_ids+1),A
    INC HL
    LD A,(HL)
    LD (p_fd_ids+2),A
.fill:
    CALL p_fast_background_row
    LD HL,p_fd_cursor
    INC (HL)
    LD A,(p_fd_count)
    CP (HL)
    JR NZ,.row
    RET
.blank:
    LD A,128
    LD (p_fd_ids),A
    LD (p_fd_ids+1),A
    LD (p_fd_ids+2),A
.blank_row:
    CALL p_fast_list_row
    CALL p_fast_background_row
    LD HL,p_fd_cursor
    INC (HL)
    LD A,(p_fd_count)
    CP (HL)
    JR NZ,.blank_row
    RET

p_fast_background_row:
    LD A,(p_fd_loop)
    LD (p_w_top),A
    XOR A
    LD (p_w_col),A
    CALL p_fast_cell
    LD DE,(p_w_name)
    LD A,128
    LD (DE),A
    INC DE
    LD A,(p_fd_ids)
    LD (DE),A
    INC DE
    LD A,(p_fd_ids+1)
    LD (DE),A
    INC DE
    LD A,(p_fd_ids+2)
    DUP 28
    LD (DE),A
    INC DE
    EDUP
    LD A,128
    LD (DE),A
    RET

p_fast_upload_dirty:
    LD A,(p_fd_count)
    OR A
    RET Z
    XOR A
    LD (p_fd_cursor),A
.row:
    CALL p_fast_list_row
    LD (p_w_top),A
    LD L,A
    LD H,0
    DUP 5
    ADD HL,HL
    EDUP
    LD A,(PAGE)
    OR A
    LD DE,$5800
    JR Z,.page
    LD D,$5C
.page:
    ADD HL,DE
    PUSH HL
    XOR A
    LD (p_w_col),A
    CALL p_fast_cell
    POP DE
    LD HL,(p_w_name)
    LD B,32
    CALL vdp_write
    LD HL,p_fd_cursor
    INC (HL)
    LD A,(p_fd_count)
    CP (HL)
    JR NZ,.row
    RET
