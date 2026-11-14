; Shared RAM-only takeover after all OS/ROM services have finished.
nl_takeover:
 LD A,($F362)
 OR A
 JR Z,.map_primary
 LD A,($F361)
 LD ($FFFF),A
.map_primary:
 LD A,($F360)
 OUT ($A8),A
 IFDEF NATIVE_MAIN_SOURCE
 LD HL,NATIVE_MAIN_SOURCE
 LD DE,0
 LD BC,MAIN_SIZE
 LDIR
 ENDIF
 LD HL,$E100+GFX_SIZE-1
 LD DE,$CC73
 CALL $F312
 ; First16K are the complete source-declared VRAM image; following3188 bytes
 ; are the high native RAM segment. Main decompression replaces this staging.
 LD A,0
 OUT ($99),A
 LD A,$40
 OUT ($99),A
 LD HL,$8000
 LD BC,$4000
.write:
 LD A,(HL)
 OUT ($98),A
 INC HL
 DEC BC
 LD A,B
 OR C
 JR NZ,.write
 LD HL,$C000
 LD DE,$F380
 LD BC,$0C74
 LDIR
 LD HL,MAIN_SIZE-1
 ; ZX0's measured3-byte backwards in-place overlap slack is required.
 ; Decode three bytes above the final low image, then move it down once from
 ; an entry outside the destination. The decoder/slot flags remain untouched.
 LD DE,$F302
 LD BC,$F303
 PUSH BC
 JP $F312
