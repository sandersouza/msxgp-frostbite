; C7F0 phase0..159, C7F1 owner0..7. Return exact30-byte literal NAME window.
; Only the legacy row copier's live30 bytes are stored. No scratch writes.
gw_lookup:
    LD A,($C7F0)
    LD L,A
    LD H,HIGH gw_directory
    LD L,(HL)
    LD H,0
    DUP 4
    ADD HL,HL
    EDUP
    LD A,($C7F1)
    ADD A,A
    LD E,A
    LD D,0
    ADD HL,DE
    LD DE,gw_index
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    EX DE,HL
    IFNDEF GW_INLINE
    RET
    ENDIF
gw_end:
