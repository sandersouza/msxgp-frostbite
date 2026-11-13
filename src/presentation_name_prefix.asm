; Keep complete dirty transactions; omit only an unchanged warm NAME prefix.
    INCLUDE "symbols.inc"
    ORG ac_names
prefix_names:
    LD A,(PAGE)
    OR A
    LD HL,$C902
    JR Z,.page
    LD H,$CE
.page:
    LD DE,32
    LD A,128
    LD B,7
.mask:
    LD (HL),A
    ADD HL,DE
    LD (HL),A
    ADD HL,DE
    DJNZ .mask
    LD (HL),A
    LD HL,(hy_lo)
    LD A,L
    XOR 14
    OR H
    JR NZ,.publish
    LD A,(p_fd_rows)
    INC A
    JR Z,.publish
    AND 7
    JR NZ,.publish
    LD A,(p_fd_count)
    SUB 3
    LD (p_fd_count),A
    CALL NZ,prefix_compact
.publish:
    JP p_template_upload_names_known
prefix_ram_end:
    ASSERT $ <= ac_names_code_end
    DS ac_names_code_end-$,0
prefix_ram_padded_end:
    ORG $6A32
prefix_compact:
    LD C,A
    LD B,0
    LD HL,p_fd_list+3
    LD DE,p_fd_list
    LDIR
    RET
prefix_fixed_end:
    ASSERT $ <= $6A46
