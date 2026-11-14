; Three-byte overlap slack is removed from outside the final destination.
nl_relocate:
 LD HL,3
 LD DE,0
 LD BC,$F300
 LDIR
 JP $C400
