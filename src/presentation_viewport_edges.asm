; All helpers fit the existing header alignment padding, before its palette.
 INCLUDE "symbols.inc"
 ORG $ECC0
ar_pattern:
 CALL p_player_sprite_pattern
 LD A,($F066)
 CP 6
 RET NC
 LD L,A
 LD H,0
 LD DE,ar_left_masks
 ADD HL,DE
 LD C,(HL)
 LD HL,$C500
 LD B,16
.row:
 LD A,(HL)
 AND C
 LD (HL),A
 INC L
 DJNZ .row
 RET
ar_left_masks:
 DB $00,$01,$07,$0F,$3F,$7F
; Distinguish all partial positions from full, right-clipped and shore keys.
ar_edge_key:
 LD B,A
 LD A,($F066)
 CP 8
 JR C,.partial
 LD A,B
 JR .store
.partial:
 ADD A,160
.store:
 LD (p_pc_key+5),A
 RET
ar_end:
 ASSERT $ <= $ED00
 DS $ED00-$,0
ar_padded_end:
