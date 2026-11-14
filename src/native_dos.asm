; Actual DOS1 executable. All DOS calls precede RAM takeover; RESET exits.
 INCLUDE "native-loader.inc"
 ORG $0100
nd_entry:
 LD HL,($0006)
 LD DE,nd_end+128
 OR A
 SBC HL,DE
 JR NC,.ready
 LD DE,nd_memory_error
 LD C,9
 CALL 5
 RET
.ready:
 DI
 LD SP,$F380
 CALL nl_save_slots
 LD A,$82
 OUT ($99),A
 LD A,$81
 OUT ($99),A
 LD HL,nd_gfx
 LD DE,$E100
 LD BC,GFX_SIZE
 LDIR
 LD HL,nd_helper_data
 LD DE,$E000
 LD BC,nd_helper_end-$E000
 LDIR
 LD HL,nd_decoder_data
 LD DE,$F312
 LD BC,nd_decoder_end-$F312
 LDIR
 LD HL,nd_relocate_data
 LD DE,$F303
 LD BC,nd_relocate_end-$F303
 LDIR
 JP $E000
 INCLUDE "native_loader_slots.asm"
nd_memory_error:
 DB "Frostbite requires64 KiB RAM and enough DOS TPA.",13,10,"$"
nd_helper_data:
 PHASE $E000
 DEFINE NATIVE_MAIN_SOURCE nd_main
 INCLUDE "native_loader_ram.asm"
nd_helper_end:
 ASSERT $ <= $E100
 DEPHASE
nd_decoder_data:
 PHASE $F312
 INCLUDE "third_party/zx0/dzx0_standard_back.asm"
nd_decoder_end:
 ASSERT $ <= $F360
 DEPHASE
nd_relocate_data:
 PHASE $F303
 INCLUDE "native_loader_reloc.asm"
nd_relocate_end:
 ASSERT $ <= $F312
 DEPHASE
nd_gfx:
 INCBIN "cold-gfx-high.zx0"
nd_main:
 INCBIN "cold-low.zx0"
nd_end:
 ASSERT nd_end+128 < $C000
