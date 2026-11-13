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
; Old clipped recipes and cache identities cannot describe the new edge.
ar_player_x:
 LD A,($F066)
 CP 8
 RET NC
 LD A,255
 RET
ar_cache_gate:
 LD A,($F066)
 CP 8
 JR NC,.original
 OR A
 RET
.original:
 JP $B256                   ;unchanged inherited-L eligibility after its load
ar_end:
 ASSERT $ <= $ED00
 DS $ED00-$,0
ar_padded_end:
