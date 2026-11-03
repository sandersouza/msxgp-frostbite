; Complete inactive NAME rows in contiguous bursts of at most256 bytes.
; Public entry validates an external list before any IO. The private entry
; accepts only p_fast_collect_rows' sorted, bounded list and scheduler PAGE.
p_template_upload_names:
    LD A,(PAGE)
    CP 2
    JR NC,.invalid
    LD A,(p_fd_count)
    CP 25
    JR NC,.invalid
    OR A
    RET Z
    LD B,A
    LD HL,p_fd_list
    LD C,255
.validate:
    LD A,(HL)
    CP 24
    JR NC,.invalid
    LD E,A
    LD A,C
    INC A
    CP E
    JR C,.ordered
    JR NZ,.invalid
.ordered:
    LD C,E
    INC HL
    DJNZ .validate
    JP p_template_upload_names_known
.invalid:
    SCF
    RET

p_template_upload_names_known:
    LD A,(p_fd_count)
    OR A
    RET Z
    LD IY,$58C8             ;VRAM/CPU high-byte origins for PAGE0
    LD A,(PAGE)
    OR A
    JR Z,.page
    LD IY,$5CCD             ;PAGE1 CPU buffer is CD00, VRAM NAME is1C00
.page:
    XOR A
    LD (p_fd_cursor),A
.chunk:
    LD A,(p_fd_cursor)
    ADD A,p_fd_list&255
    LD L,A
    LD H,p_fd_list/256
    LD A,(HL)
    LD (p_fd_loop),A
    LD C,A
    LD B,1
.extend:
    LD A,(p_fd_count)
    LD D,A
    LD A,(p_fd_cursor)
    INC A
    LD (p_fd_cursor),A
    CP D
    JR Z,.publish
    LD A,B
    CP 8
    JR Z,.publish          ;B=0 is the VDP stream's exact256-byte count
    INC L
    LD A,(HL)
    INC C
    CP C
    JR NZ,.publish
    INC B
    JR .extend
.publish:
    LD A,B
    DUP 3
    RRCA
    EDUP
    AND $E0
    LD B,A                 ;rows1..8 ->32,64,...,224,0 bytes
    LD A,(p_fd_loop)
    LD L,A
    LD H,0
    DUP 5
    ADD HL,HL
    EDUP
    LD D,H
    LD E,L
    LD C,IYL
    LD A,H
    ADD A,C
    LD H,A
    LD C,IYH
    LD A,D
    ADD A,C
    LD D,A
    CALL vdp_write
    LD A,(p_fd_count)
    LD HL,p_fd_cursor
    CP (HL)
    JR NZ,.chunk
    OR A
    RET
