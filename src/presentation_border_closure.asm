; Same reserved resident NAME publisher, with the final sea row included.
    INCLUDE "symbols.inc"
    ORG ac_names
closure_names:
    LD A,(PAGE)
    OR A
    LD HL,$C902
    JR Z,.page
    LD H,$CE
.page:
    LD DE,32
    LD A,128
    DUP 14
    LD (HL),A
    ADD HL,DE
    EDUP
    LD (HL),A               ;row22 closes the sea through targetY183
    JP p_template_upload_names_known
closure_code_end:
    ASSERT $ <= ac_names_code_end
    DS ac_names_code_end-$,0
closure_end:
