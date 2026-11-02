; Specialized MISS path after p_fixed_resolve has checked page/group/slot and
; selected p_fx_meta. Raw tag9 masks are immutable ROM bytes; their complete
; CGT is FG:4. Reuse that CGT only when the prior published grammar proves it.
p_tp_skip EQU $C2E7
p_template_floe_upload:
    XOR A
    LD (pt_error),A
    LD A,(p_fx_bank)
    DEC A
    CP 2
    JP NC,p_template_upload_fail
    LD A,(p_fx_bank)
    CP 1
    LD A,pt_water_id1
    JR Z,.water
    LD A,pt_water_id2
.water:
    LD HL,pf_key+2
    CP (HL)
    JP NZ,p_template_upload_fail
    INC HL
    LD A,(HL)
    OR A
    JP NZ,p_template_upload_fail
    INC HL
    LD A,(HL)
    OR A
    JP Z,p_template_upload_fail
    CP 16
    JP NC,p_template_upload_fail
    INC HL
    LD A,(HL)
    CP 9
    JP NZ,p_template_upload_fail
; Only p_template_strip_publish may enter here after validating shared fields.
p_template_floe_upload_checked:
    LD DE,(pf_key)
    CALL p_template_floe_address
    JP C,p_template_upload_fail
    PUSH HL                 ;retain mapped ROM address while inspecting metadata
    LD HL,(p_fx_meta)
    INC HL
    INC HL
    LD DE,pf_key+2
    LD B,4
.same_cgt:
    LD A,(DE)
    CP (HL)
    JR NZ,.new_cgt
    INC DE
    INC HL
    DJNZ .same_cgt
    LD A,1
    JR .remember
.new_cgt:
    XOR A
.remember:
    LD (p_tp_skip),A
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
    POP HL
    PUSH DE
    LD B,8
    CALL vdp_write          ;all eight original PGT bytes, directly from ROM
    POP DE
    LD A,(p_tp_skip)
    OR A
    JR NZ,.publish
    LD A,D
    ADD A,$20
    LD D,A
    LD A,(pf_key+4)
    DUP 4
    RLCA
    EDUP
    OR 4
    LD HL,pt_tile+8
    DUP 8
    LD (HL),A
    INC HL
    EDUP
    LD HL,pt_tile+8
    LD B,8
    CALL vdp_write
.publish:
    LD HL,pf_key
    LD DE,(p_fx_meta)
    LD BC,6
    LDIR                    ;valid only after every required table write
    OR A
    RET
p_template_upload_fail:
    LD A,1
    LD (pt_error),A
    SCF
    RET
