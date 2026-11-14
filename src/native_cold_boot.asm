; Transient entry in SAT/P0 scratch, replaced only after JP t_main. All static
; game bytes are already loaded. Loader flags survive the decoder atF360..362.
; The source clock remains the original60 Hz scheduler; renderer clock is free.
 ORG $C400
nc_entry:
 DI
 LD SP,$F380
 LD A,($F360)
 LD (t_slot_primary),A
 LD A,($F361)
 LD (t_slot_secondary),A
 LD A,($F362)
 LD (t_slot_expanded),A
 XOR A
 LD (t_enabled),A
 LD (t_in_irq),A
 LD HL,nc_registers
 LD B,8
 LD C,$80
.register:
 LD A,(HL)
 OUT ($99),A
 LD A,C
 OUT ($99),A
 INC HL
 INC C
 DJNZ .register
 CALL input_init
 CALL p_audio_init
 CALL nc_detect_period
 CALL native_reset
nc_source_ready:
 LD A,208
 LD (SAT),A
 LD A,1
 LD (t_enabled),A
 LD (t_in_irq),A
 JP t_main
nc_wait_vblank:
 IN A,($99)
 AND $80
 JR Z,nc_wait_vblank
 RET
nc_detect_period:
 CALL nc_wait_vblank
 CALL nc_wait_vblank
 LD HL,0
.count:
 INC HL
 IN A,($99)
 RLCA
 JR NC,.count
 LD DE,1800
 OR A
 SBC HL,DE
 LD HL,0
 LD A,0
 JR C,.ntsc
 LD HL,11628
 LD A,1
.ntsc:
 LD (DELTA),HL
 LD (PALFLAG),A
 RET
nc_registers:
 DB $02,$C2,$06,$FF,$03,$36,$07,$01
nc_end:
 ASSERT $ <= $C540
 ORG t_start_clock
nc_clock:
 DI
 LD A,$C3
 LD ($0038),A
 LD HL,t_irq
 LD ($0039),HL
 IM 1
 IN A,($99)
 LD A,$E2
 OUT ($99),A
 LD A,$81
 OUT ($99),A
 LD A,1
 LD (t_enabled),A
 XOR A
 LD (t_in_irq),A
 EI
 RET
nc_clock_end:
 ASSERT $ <= t_irq
