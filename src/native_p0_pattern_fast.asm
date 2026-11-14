; Exact normal P0 SGT0..69. Absolute source pointers below8000 retain phase
; in bit15. DE walks original source rows; C is the expansion page base. The
; unrolled absolute output stores preserve IX/IY and permit the source IRQ.
np0_build:
 LD L,A
 LD H,0
 ADD HL,HL
 LD DE,np0_directory
 ADD HL,DE
 LD E,(HL)
 INC HL
 LD D,(HL)
 LD A,D
 RLCA
 AND 1
 ADD A,A
 ADD A,HIGH np0_expansion
 LD C,A
 RES 7,D
 DUP 16,row
 LD A,(DE)
 INC DE
 ADD A,A
 LD L,A
 LD A,C
 ADC A,0
 LD H,A
 LD A,(HL)
 LD ($C500+row),A
 INC HL
 LD A,(HL)
 LD ($C510+row),A
 EDUP
 LD HL,$C500
 RET
np0_end:
