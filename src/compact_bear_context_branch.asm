; Exact nine certified contexts from the original1024-byte native directory.
; HL=directory index. Preserve IX/IY/SP/IFF; return A=context0..8 or FF.
cx_find_context:
    LD A,H
    OR A
    JR Z,.group0
    DEC A
    JR Z,.group1
    DEC A
    JR Z,.group2
    DEC A
    JR Z,.group3
.missing:
    LD A,255
    RET
.group0:
    LD A,L
    CP $0F
    LD A,6
    RET Z
    LD A,L
    CP $10
    LD A,2
    RET Z
    LD A,L
    CP $19
    LD A,8
    RET Z
    JR .missing
.group1:
    LD A,L
    CP $02
    LD A,3
    RET Z
    LD A,L
    CP $08
    LD A,7
    RET Z
    JR .missing
.group2:
    LD A,L
    OR A
    LD A,4
    RET Z
    LD A,L
    CP $10
    LD A,0
    RET Z
    JR .missing
.group3:
    LD A,L
    CP $02
    LD A,1
    RET Z
    LD A,L
    CP $06
    LD A,5
    RET Z
    JR .missing
cx_end:
