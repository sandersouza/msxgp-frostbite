; Source state remains C000; only the renderer reads the coherent F000 snapshot.
    INCLUDE "symbols.inc"
t_enabled EQU $E880
t_in_irq EQU $E881
t_bank EQU $E882
t_saved_bank EQU $E883
t_ready EQU $E884
t_ready_page EQU $E885
t_vblanks EQU $E886
t_last_commit EQU $E888
t_commits EQU $E88A
t_snapshot_step EQU $E88C
t_late EQU $E88E
t_spurious EQU $E890
t_slot_primary EQU $E892
t_slot_secondary EQU $E893
t_slot_expanded EQU $E894
t_fault EQU $E895

    ORG t_resident_origin
; Shadow first: an IRQ between these writes safely preselects the intended bank.
t_mapper:
    LD (t_bank),A
    LD ($7000),A
    RET
t_bootstrap:
    XOR A
    LD (t_enabled),A
    LD (t_in_irq),A
    JP map_page2
t_resident_end:
    ASSERT $ <= $4C00

    ORG t_initializer_origin
t_initializer:
    CALL qe_init
    LD A,115
    CALL t_mapper
    LD HL,$B800
    LD DE,t_prepare_gate
    LD BC,t_ram_end-t_prepare_gate
    LDIR
    LD HL,$E880
    LD DE,$E881
    LD BC,127
    LD (HL),0
    LDIR
    LD A,1
    CALL t_mapper
    RET
t_initializer_end:
    ASSERT $ <= $7F5F

    ORG $E900
t_prepare_gate:
    DI
    PUSH AF
    PUSH BC
    PUSH DE
    PUSH HL
    CALL diagnostic_selectors ;presentation flags change only between pictures
    LD HL,$C000
    LD DE,$F000
    LD BC,128
    LDIR
    LD HL,(TICKS)
    LD (t_snapshot_step),HL
    POP HL
    POP DE
    POP BC
    POP AF
    LD A,1                 ;original prepare prologue contract
    CALL t_mapper
    CALL t_restore_interrupts
    RET

t_restore_interrupts:
    PUSH AF
    LD A,(t_enabled)
    OR A
    JR Z,.done
    LD A,(t_in_irq)
    OR A
    JR NZ,.done
    EI
.done:
    POP AF
    RET

t_vdp_write:
    DI
    LD A,E
    OUT ($99),A
    LD A,D
    OUT ($99),A
    LD C,$98
    CALL t_restore_interrupts
    JP vdp_stream

t_fill:
    DI
    LD C,A
    LD A,E
    OUT ($99),A
    LD A,D
    OUT ($99),A
    CALL t_restore_interrupts
    LD A,C
.byte:
    OUT ($98),A
    NOP
    DEC B
    JP NZ,.byte
    RET

t_main:
    CALL t_start_clock
.frame:
    CALL presentation_prepare
.prepared:
    DI
    LD A,(PAGE)
    LD (t_ready_page),A
    LD A,1
    LD (t_ready),A
.wait:
    DI
    LD A,(t_ready)
    OR A
    JR Z,.next
    EI
    HALT
    JR .wait
.next:
    EI
    JP .frame

t_start_clock:
    DI
    IN A,($A8)
    RLCA
    RLCA
    AND 3
    LD L,A
    LD H,0
    LD DE,$FCC1
    ADD HL,DE
    BIT 7,(HL)
    JR Z,.primary
    LD A,1
    LD (t_slot_expanded),A
    LD A,($FFFF)
    CPL
    LD B,A
    RLCA
    RLCA
    AND 3
    LD C,A
    LD A,B
    AND $FC
    OR C
    LD (t_slot_secondary),A
    LD ($FFFF),A           ;preserve all other pages of this expanded primary
.primary:
    IN A,($A8)
    LD B,A
    RLCA
    RLCA
    AND 3
    LD C,A
    LD A,B
    AND $FC
    OR C
    LD (t_slot_primary),A
    OUT ($A8),A
    LD A,$C3
    LD ($0038),A
    LD HL,t_irq
    LD ($0039),HL
    LD A,($0038)
    CP $C3
    JR NZ,.fault
    LD HL,($0039)
    LD DE,t_irq
    OR A
    SBC HL,DE
    JR NZ,.fault
    IM 1
    IN A,($99)             ;discard the pre-takeover pending status
    LD A,$E2               ;16KiB VRAM/display/interrupts/16px sprites
    OUT ($99),A
    LD A,$81
    OUT ($99),A
    LD A,1
    LD (t_enabled),A
    EI
    RET
.fault:
    LD A,1
    LD (t_fault),A
    DI
    JR $

t_irq:
    PUSH AF
    IN A,($99)
    AND $80
    JR NZ,.vblank
    PUSH HL
    LD HL,(t_spurious)
    INC HL
    LD (t_spurious),HL
    POP HL
    POP AF
    EI
    RETI
.vblank:
    PUSH BC
    PUSH DE
    PUSH HL
    PUSH IX
    PUSH IY
    EX AF,AF'
    PUSH AF
    EX AF,AF'
    EXX
    PUSH BC
    PUSH DE
    PUSH HL
    EXX
    LD A,(t_bank)
    LD (t_saved_bank),A
    LD A,1
    LD (t_in_irq),A
.service:
    LD HL,(t_vblanks)
    INC HL
    LD (t_vblanks),HL
    LD A,(t_ready)
    OR A
    JR Z,.source
    LD DE,(t_last_commit)
    OR A
    SBC HL,DE
    LD A,H
    OR A
    JR NZ,.commit
    LD A,L
    CP 2
    JR C,.source
.commit:
    CALL presentation_commit
.committed:
    XOR A
    LD (t_ready),A
    LD HL,(t_vblanks)
    LD (t_last_commit),HL
    LD HL,(t_commits)
    INC HL
    LD (t_commits),HL
.source:
    CALL scheduler
    CALL charge_steps
    IN A,($99)
    AND $80
    JR Z,.restore
    LD HL,(t_late)
    INC HL
    LD (t_late),HL
    JP .service             ;account for the pending tick; never silently drop it
.restore:
    LD A,(t_saved_bank)
    CALL t_mapper
    XOR A
    LD (t_in_irq),A
    EXX
    POP HL
    POP DE
    POP BC
    EXX
    EX AF,AF'
    POP AF
    EX AF,AF'
    POP IY
    POP IX
    POP HL
    POP DE
    POP BC
    POP AF
.exit:
    EI
    RETI
t_ram_end:
    ASSERT $ <= $F000
