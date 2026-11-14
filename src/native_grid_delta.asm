; A=source Y0..255, C=coarse0/1. Exact displacement; no scratch, IX/IY intact.
; Start thresholds avoid an unrepresentable end-exclusive256 byte.
ngd_lookup:
 LD E,A
 LD HL,ngd_rows0
 LD B,ngd_count0
 LD A,C
 OR A
 JR Z,.ready
 LD HL,ngd_rows1
 LD B,ngd_count1
.ready:
 LD D,0
.next:
 LD A,E
 CP (HL)
 JR C,.done
 INC HL
 LD D,(HL)
 INC HL
 DJNZ .next
.done:
 LD A,D
 RET
ngd_end:
