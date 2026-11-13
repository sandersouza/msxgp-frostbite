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
 LD E,$EF
 LD A,141
 LD (DE),A
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
 DB 142,143,250,251,252,253,254
as_names_end:
 ASSERT $ <= $66FA
 DS $66FA-$,0
 ORG aq_boot
as_boot:
 CALL t_fill
 LD HL,as_patterns
 LD DE,$5000+134*8
 LD B,80
 CALL vdp_write
 LD HL,as_patterns+80
 LD DE,$5000+250*8
 LD B,40
 CALL vdp_write
 LD HL,as_colors
 LD DE,$7000+134*8
 LD B,80
 CALL vdp_write
 LD HL,as_colors+80
 LD DE,$7000+250*8
 LD B,40
 JP vdp_write
as_patterns:
 INCBIN "aligned-credit-patterns.bin"
as_colors:
 INCBIN "aligned-credit-colors.bin"
as_boot_end:
 ASSERT $ <= $C000
