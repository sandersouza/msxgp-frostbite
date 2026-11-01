    ORG $4000
    DB "AB"
    DW start
    DS 12,0
    DB "FBN0"
start:
    DI
    LD SP,$F380
    CALL map_native_page2
    LD A,$53
    LD ($C6FC),A
idle:
    JP idle
rpc_start:
    DI
    LD SP,$F380
    LD A,(core_sp)
    AND 128
    LD (core_stack_high),A
    LD A,(core_sp)
    AND 127
    LD L,A
    LD H,$C0
    PUSH HL
    POP IX
    LD A,($C6F4)
    LD E,A
    LD BC,($C6F2)
    LD H,$C0
    LD L,B
    PUSH HL
    POP IY
    LD HL,($C6F0)
    PUSH HL
    POP AF
    LD HL,rpc_done
    PUSH HL
    LD HL,($C6FE)
    JP (HL)
rpc_done:
    IFDEF WITH_NATIVE_INPUT
    PUSH AF
    POP HL
    LD ($C6F0),HL
    LD ($C6F2),BC
    LD A,E
    LD ($C6F4),A
    PUSH IX
    POP HL
    LD A,(core_stack_high)
    OR L
    LD (core_sp),A
    ENDIF
    JP idle
map_native_page2:
    CALL $0138
    RRCA
    RRCA
    AND 3
    LD C,A
    LD E,A
    LD D,0
    LD HL,$FCC1
    ADD HL,DE
    BIT 7,(HL)
    JR Z,.slot
    LD HL,$FCC5
    ADD HL,DE
    LD A,(HL)
    AND $0C
    OR C
    OR $80
    JR .enable
.slot:
    LD A,C
.enable:
    LD H,$80
    JP $0024
    IFDEF WITH_NATIVE_INPUT
    INCLUDE "native_input.asm"
    ENDIF
    DS $8000-$,$FF
    INCLUDE "native_cpu.asm"
    INCLUDE "core.inc"
core_code_end:
    ALIGN 1024
original_data:
    INCBIN "data.bin"
native_contract_end:
    ASSERT $ <= $C000
    DS $C000-$,$FF
