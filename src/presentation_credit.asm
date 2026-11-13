 INCLUDE "symbols.inc"
 ORG $66AA
as_names:
 PUSH BC
 PUSH DE
 LD HL,$CAD8
 LD A,(PAGE)
 OR A
 JR Z,.page
 LD H,$CF
.page:
 EX DE,HL
 LD HL,as_top
 LD BC,7
 LDIR
 LD E,$F8
 LD HL,as_bottom
 LD BC,7
 LDIR
 POP DE
 POP BC
 LD B,0
 RET
as_top:
 DB 134,135,136,137,138,139,140
as_bottom:
 DB 141,142,143,250,251,252,253
as_names_end:
 ASSERT $ <= $66FA
 DS $66FA-$,0
 ORG aq_boot
as_boot:
 CALL t_fill
 XOR A
 LD ($DA08),A
 LD HL,as_patterns
 LD DE,$5000+134*8
 LD B,80
 CALL vdp_write
 LD HL,as_patterns+80
 LD DE,$5000+250*8
 LD B,32
 CALL vdp_write
 LD HL,as_colors
 LD DE,$7000+134*8
 LD B,80
 CALL vdp_write
 LD HL,as_colors+80
 LD DE,$7000+250*8
 LD B,32
 JP vdp_write
as_patterns:
 INCBIN "aligned-credit-patterns.bin"
as_colors:
 INCBIN "aligned-credit-colors.bin"
as_commit:
 LD A,($F068)
 CP 150
 SBC A,A
 CPL
 LD C,A
 LD A,($DA08)
 CP C
 JR Z,.return
 LD A,C
 LD ($DA08),A
 LD HL,as_patterns
 OR A
 JR Z,.patterns
 LD HL,as_coarse
.patterns:
 LD DE,$5000+134*8
 LD B,80
 CALL vdp_write
 LD DE,$5000+250*8
 LD B,32
 CALL vdp_write
 LD A,($F068)
 CP 150
 LD C,$F1
 JR C,.colors
 LD C,$F4
.colors:
 LD DE,$7000+134*8+2
 LD B,7
.color:
 LD A,E
 OUT ($99),A
 LD A,D
 OUT ($99),A
 LD A,C
 OUT ($98),A
 LD A,E
 ADD A,8
 LD E,A
 DJNZ .color
.return:
 POP AF
 JP t_mapper
as_coarse:
 INCBIN "aligned-credit-coarse.bin"
as_boot_end:
 ASSERT $ <= $C000
 ORG aq_credit+3
as_bridge:
 LD HL,SAT
 CALL presentation_commit+3
 LD A,(t_bank)
 PUSH AF
 LD A,65
 CALL t_mapper
 JP as_commit
as_bridge_end:
 ASSERT $ <= aq_names_padded_end
 DS aq_names_padded_end-$,0
