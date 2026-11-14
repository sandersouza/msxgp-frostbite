; Normal32K cart. Shared native payload, no mapper and no captured RAM input.
; First stage uses VRAM as temporary compressed-input storage. The second
; ROM window stays visible while lower RAM is installed; final takeover is
; performed entirely from upper RAM. No BIOS/DOS return after game takeover.
 INCLUDE "native-loader.inc"
 ORG $4000
 DB "AB"
 DW rom_init,0,0,0
 DS 6,0
rom_init:
 DI
 LD SP,$F380
 ; Expose this same Normal cartridge in page2 using the BIOS slot API.
 CALL $0138
 RRCA
 RRCA
 AND 3
 LD C,A
 LD B,0
 LD HL,$FCC1
 ADD HL,BC
 LD A,(HL)
 AND $80
 OR C
 LD C,A
 LD DE,4
 ADD HL,DE
 LD A,(HL)
 AND $0C
 OR C
 LD H,$80
 CALL $0024
 DI
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
 CALL rom_replicate
 LD ($F360),A
 LD A,($FFFF)
 CPL
 RLCA
 RLCA
 AND 3
 CALL rom_replicate
 LD ($F361),A
 LD A,$82
 OUT ($99),A
 LD A,$81
 OUT ($99),A
 IN A,($99)
 LD HL,main_data
 LD DE,$4000
 LD BC,$4000
 CALL rom_write_vram
 LD HL,main_data+$4000
 LD DE,$C000
 LD BC,MAIN_SIZE-$4000
 LDIR
 JP rom_stage2
rom_replicate:
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
rom_write_vram:
 LD A,E
 OUT ($99),A
 LD A,D
 OUT ($99),A
.byte:
 LD A,(HL)
 OUT ($98),A
 INC HL
 DEC BC
 LD A,B
 OR C
 JR NZ,.byte
 RET
rom_header_end:
 ASSERT $ <= $4100
 DS $4100-$,$FF
main_data:
 INCBIN "cold-low.zx0"
gfx_data:
 INCBIN "cold-gfx-high.zx0"
 ASSERT $ <= $BEE0
 DS $BEE0-$,$FF
rom_stage2:
 ; Replicate page3 RAM only into pages0/1; preserve the visible ROM in page2.
 LD A,($F362)
 OR A
 JR Z,.primary
 LD A,($FFFF)
 CPL
 AND $F0
 LD B,A
 LD A,($F361)
 AND $0F
 OR B
 LD ($FFFF),A
.primary:
 IN A,($A8)
 AND $F0
 LD B,A
 LD A,($F360)
 AND $0F
 OR B
 OUT ($A8),A
 LD HL,$C000
 LD DE,$4000
 LD BC,MAIN_SIZE-$4000
 LDIR
 XOR A
 OUT ($99),A
 OUT ($99),A
 LD HL,0
 LD BC,$4000
.read:
 IN A,($98)
 LD (HL),A
 INC HL
 DEC BC
 LD A,B
 OR C
 JR NZ,.read
 LD HL,rom_helper_data
 LD DE,$E000
 LD BC,rom_helper_end-$E000
 LDIR
 LD HL,gfx_data
 LD DE,$E100
 LD BC,GFX_SIZE
 LDIR
 LD HL,rom_decoder_data
 LD DE,$F312
 LD BC,rom_decoder_end-$F312
 LDIR
 LD HL,rom_relocate_data
 LD DE,$F303
 LD BC,rom_relocate_end-$F303
 LDIR
 JP $E000
rom_helper_data:
 PHASE $E000
rom_takeover:
 INCLUDE "native_loader_ram.asm"
rom_helper_end:
 ASSERT $ <= $E100
 DEPHASE
rom_relocate_data:
 PHASE $F303
 INCLUDE "native_loader_reloc.asm"
rom_relocate_end:
 ASSERT $ <= $F312
 DEPHASE
rom_decoder_data:
 PHASE $F312
 INCLUDE "third_party/zx0/dzx0_standard_back.asm"
rom_decoder_end:
 ASSERT $ <= $F360
 DEPHASE
rom_end:
 ASSERT $ <= $C000
 DS $C000-$,$FF
