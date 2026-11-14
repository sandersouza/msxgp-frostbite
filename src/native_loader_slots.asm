; Preserve the actual page3 RAM primary/secondary identity before takeover.
nl_save_slots:
 IN A,($A8)
 RLCA
 RLCA
 AND 3
 LD E,A
 LD L,A
 LD H,0
 LD BC,$FCC1
 ADD HL,BC
 LD A,(HL)
 AND $80
 LD ($F362),A
 LD A,E
 CALL nl_replicate
 LD ($F360),A
 LD A,($FFFF)
 CPL
 RLCA
 RLCA
 AND 3
 CALL nl_replicate
 LD ($F361),A
 RET
nl_replicate:
 LD B,A
 RLCA
 RLCA
 OR B
 LD B,A
 RLCA
 RLCA
 RLCA
 RLCA
 OR B
 RET
nl_map_slots:
 LD A,($F362)
 OR A
 JR Z,.primary
 LD A,($F361)
 LD ($FFFF),A
.primary:
 LD A,($F360)
 OUT ($A8),A
 RET
