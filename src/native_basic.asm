; Disk BASIC: graphics/high segment and loader helpers arrive through BLOAD,S
; in VRAM, then this genuine executable carries the complete low RAM payload.
; Lower RAM is mapped before moving the payload; all BASIC services are done.
 INCLUDE "native-loader.inc"
 ORG $8800
nb_entry:
 DI
 LD SP,$F380
 CALL nl_save_slots
 CALL nl_map_slots
 LD A,$82
 OUT ($99),A
 LD A,$81
 OUT ($99),A
 LD HL,nb_main
 LD DE,$2000
 LD BC,MAIN_SIZE-$2000
 LDIR
 LD HL,0
 LD DE,0
 LD BC,$2000
 CALL nb_read_vram
 LD HL,$2C00
 LD DE,$E000
 LD BC,BASIC_HELPER_SIZE
 CALL nb_read_vram
 LD HL,$2D00
 LD DE,$F312
 LD BC,69
 CALL nb_read_vram
 LD HL,$2E00
 LD DE,$F303
 LD BC,14
 CALL nb_read_vram
 LD HL,$2000
 LD DE,$E100
 LD BC,GFX_SIZE
 CALL nb_read_vram
 JP $E000
 INCLUDE "native_loader_slots.asm"
nb_read_vram:
 LD A,L
 OUT ($99),A
 LD A,H
 OUT ($99),A
 NOP
 NOP
.byte:
 IN A,($98)
 LD (DE),A
 INC DE
 DEC BC
 LD A,B
 OR C
 JR NZ,.byte
 RET
nb_header_end:
 ASSERT $ <= $88C0
 DS $88C0-$,0
nb_main:
 INCBIN "basic-low-tail.zx0"
nb_end:
 ASSERT $ <= $F300
