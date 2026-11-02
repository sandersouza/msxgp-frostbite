; Permanent physical roles. A valid key is published only after its complete
; offscreen PGT/CGT upload; active generations are never evicted or aliased.
pf_key EQU $CC90
p_fast_crc_data EQU $E100
p_fx_force EQU $C2E2
p_fx_meta EQU $C2E3
p_fx_bank EQU $C2E5
p_fx_fuse1 EQU $E240
p_fx_fuse2 EQU $E260

p_fast_init:
    LD HL,$D000
    LD DE,$D001
    LD BC,$8FF
    LD (HL),255
    LDIR
    LD HL,$D900
    LD DE,$D901
    LD BC,263
    LD (HL),255
    LDIR
    LD A,255
    LD (p_fx_force),A
    LD HL,p_fixed_counts
    LD DE,$CCA0
    LD BC,6
    LDIR
    IFDEF WITH_PRESENTATION_TEMPLATES
    LD HL,$E5C0
    LD DE,$E5C1
    LD BC,31
    LD (HL),255
    LDIR
    ENDIF
    XOR A
    RET

p_fixed_put:
    CALL p_fixed_resolve
    RET C
    LD HL,(p_w_name)
    LD A,(p_w_tile)
    LD (HL),A
    LD A,(pf_key+5)
    OR A
    JR NZ,.done
    LD A,(p_w_family)
    OR A
    CALL Z,p_fixed_mark_object
.done:
    LD A,(p_w_tile)
    OR A
    RET

p_fixed_resolve:
    LD A,(pf_key+5)
    CP 255
    JP Z,p_fixed_fail
    LD A,(PAGE)
    CP 2
    JP NC,p_fixed_fail
    LD B,A
    LD A,(p_w_cachegroup)
    CP 6
    JP NC,p_fixed_fail
    LD C,A
    LD A,B
    OR A
    LD A,C
    JR Z,.page0
    SUB 3
    JP C,p_fixed_fail
    JR .bank
.page0:
    CP 3
    JP NC,p_fixed_fail
.bank:
    LD (p_fx_bank),A
    CALL p_fixed_choose_id
    RET C
    LD (p_w_tile),A
    CP 128
    JR NC,.footer_bounds
    LD C,A
    LD A,(PAGE)
    DUP 6
    ADD A,A
    EDUP
    XOR C
    AND $40
    JP NZ,p_fixed_fail
    LD A,(p_fx_bank)
    LD L,A
    LD H,0
    LD DE,p_fixed_counts
    ADD HL,DE
    LD A,C
    AND 63
    CP (HL)
    JP NC,p_fixed_fail
    JR .metadata
.footer_bounds:
    LD A,(pf_key+5)
    CP 6
    JP NZ,p_fixed_fail
    LD A,(p_fx_bank)
    CP 2
    JP NZ,p_fixed_fail
    LD A,(p_w_tile)
    SUB 160
    JP C,p_fixed_fail
    LD B,A
    LD A,(PAGE)
    OR A
    LD A,B
    JR Z,.first_footer
    SUB 22
    JP C,p_fixed_fail
.first_footer:
    CP 22
    JP NC,p_fixed_fail
.metadata:
    CALL p_fixed_key_address
    LD (p_fx_meta),HL
    LD DE,pf_key
    LD B,6
.compare:
    LD A,(DE)
    CP (HL)
    JR NZ,.miss
    INC DE
    INC HL
    DJNZ .compare
    JR .name
.miss:
    IFDEF WITH_PRESENTATION_TEMPLATES
    LD A,(pf_key+5)
    CP 9
    JR NZ,.general
    CALL p_template_floe_upload
    JP C,p_fixed_fail
    JR .name
.general:
    ENDIF
    LD A,(p_fx_bank)
    CALL presentation_typed_construct
    JP C,p_fixed_fail
    LD A,(pt_error)
    OR A
    JP NZ,p_fixed_fail
    LD A,(p_w_tile)
    LD L,A
    LD H,0
    DUP 3
    ADD HL,HL
    EDUP
    LD A,(p_fx_bank)
    DUP 3
    ADD A,A
    EDUP
    ADD A,$40
    ADD A,H
    LD H,A
    EX DE,HL
    PUSH DE
    LD HL,pt_tile
    LD B,8
    CALL vdp_write
    POP DE
    LD A,D
    ADD A,$20
    LD D,A
    LD HL,pt_tile+8
    LD B,8
    CALL vdp_write
    LD DE,(p_fx_meta)
    LD HL,pf_key
    LD BC,6
    LDIR                    ;key validity follows both completed table writes
.name:
    LD A,(p_w_tile)
    OR A
    RET

p_fixed_choose_id:
    LD A,(p_fx_force)
    CP 255
    JR Z,.automatic
    LD B,A
    LD A,255
    LD (p_fx_force),A
    LD A,B
    OR A
    RET
.automatic:
    LD A,(pf_key+5)
    CP 6
    JP Z,p_fixed_footer_id
    CP 5
    JP Z,p_fixed_igloo_id
    CP 16
    JR C,.world
    CP 19
    JP NC,p_fixed_fail
    LD A,(p_w_top)
    CP 3
    JP NC,p_fixed_fail
    ADD A,A
    LD B,A
    ADD A,A
    ADD A,A
    ADD A,B
    ADD A,8
    LD B,A
    LD A,(p_w_col)
    SUB 5
    CP 10
    JP NC,p_fixed_fail
    ADD A,B
    JP p_fixed_dynamic_id
.world:
    OR A
    JP NZ,p_fixed_fail
    LD A,(p_w_family)
    CP 2
    JR Z,.bear
    OR A
    JP NZ,p_fixed_fail
    LD A,(p_w_row)
    OR A
    JR Z,.object0
    DEC A
    JR Z,.object1
    DEC A
    JR Z,.object2
    DEC A
    JP NZ,p_fixed_fail
    LD D,4
    LD E,9
    JR .object_rows
.object0:
    LD D,3
    LD E,19
    JR .object_rows
.object2:
    LD D,10
    LD E,12
.object_rows:
    LD A,(p_w_top)
    SUB E
    CP 2
    JP NC,p_fixed_fail
    LD B,A
    ADD A,A
    ADD A,B
    ADD A,D
    JR .object_column
.object1:
    LD A,(p_w_top)
    CP 15
    LD A,16
    JR Z,.object_column
    LD A,(p_w_top)
    CP 16
    JP NZ,p_fixed_fail
    XOR A
.object_column:
    LD B,A
    LD A,(p_w_line)
    CP 3
    JP NC,p_fixed_fail
    ADD A,B
    JR p_fixed_dynamic_id
.bear:
    LD A,(p_w_top)
    SUB 6
    CP 3
    JP NC,p_fixed_fail
    CP 2
    JR Z,.bear_last
    ADD A,A
    ADD A,A
    JR .bear_column
.bear_last:
    XOR A
.bear_column:
    LD B,A
    LD A,(p_w_line)
    CP 4
    JP NC,p_fixed_fail
    ADD A,B
p_fixed_dynamic_id:
    LD B,A
    LD A,(PAGE)
    DUP 6
    ADD A,A
    EDUP
    OR B
    OR A
    RET

p_fixed_igloo_id:
    LD A,(p_w_top)
    SUB 3
    CP 3
    JP NC,p_fixed_fail
    ADD A,A
    LD B,A
    ADD A,A
    ADD A,B
    ADD A,38
    LD B,A
    LD A,(p_w_col)
    SUB 22
    CP 6
    JP NC,p_fixed_fail
    ADD A,B
    JR p_fixed_dynamic_id
p_fixed_footer_id:
    LD A,(p_h_footer_index)
    CP 22
    JP NC,p_fixed_fail
    LD B,A
    LD A,(PAGE)
    OR A
    LD A,160
    JR Z,.base
    LD A,182
.base:
    ADD A,B
    OR A
    RET

p_fixed_key_address:
    LD A,(p_w_tile)
    CP 128
    JR NC,.footer
    AND 63
    LD L,A
    LD H,0
    LD E,L
    LD D,H
    ADD HL,HL
    ADD HL,DE
    ADD HL,HL
    PUSH HL
    LD A,(p_w_cachegroup)
    ADD A,A
    LD E,A
    LD D,0
    LD HL,p_fast_key_roots
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    POP HL
    ADD HL,DE
    RET
.footer:
    SUB 160
    LD L,A
    LD H,0
    LD E,L
    LD D,H
    ADD HL,HL
    ADD HL,DE
    ADD HL,HL
    LD DE,$D900
    ADD HL,DE
    RET

p_fixed_mark_object:
    LD A,(p_w_coarse)
    OR A
    LD A,(p_w_top)
    JR Z,.normal
    CP 12
    RET NZ
    JR .first_map
.normal:
    CP 20
    JR Z,.second_map
    CP 15
    RET NZ
.first_map:
    LD E,p_fx_fuse1&255
    JR .write
.second_map:
    LD E,p_fx_fuse2&255
.write:
    LD A,(p_w_col)
    ADD A,E
    LD L,A
    LD H,p_fx_fuse1/256
    LD A,(p_w_copy)
    LD B,A
    ADD A,A
    ADD A,B
    LD B,A
    LD A,(p_w_line)
    ADD A,B
    LD (HL),A
    RET

p_fixed_fail:
    CALL p_world_fail
    LD A,255
    SCF
    RET
p_fixed_counts:
    DB 56,60,50,56,60,50
p_fast_key_roots:
    DW $D000,$D180,$D300,$D480,$D600,$D780
    ALIGN 8
p_fast_bits:
    DB 1,2,4,8,16,32,64,128
