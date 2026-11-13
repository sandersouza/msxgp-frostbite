; Standalone row evaluator, unlinked from the game. C790..C798 inputs:
; signed source tag, pose0..5, shift0..18, reflection0/1, then five masks:
; old, old-if-equal, new-if-different, exit, visible. Tags-1 and0..18 are
; meaningful; every other byte is a miss. Return A7/135, preserve IX/IY/SP/IFF.
; No writes except bounded stack. Player pages/pose bases supplied by fixture.
ce_test_row:
    LD A,($C790)
    CP 255
    JR Z,.exiting
    CP 19
    JR NC,.miss
    LD C,A
    CALL cer_glyph
    LD B,(HL)
    LD A,C
    CP 18
    LD C,0
    JR Z,.old_ready
    INC HL
    LD C,(HL)
.old_ready:
    LD A,($C798)
    AND B
    JR NZ,.hit
    LD A,($C794)
    AND C
    JR NZ,.hit
    LD A,C
    CP B
    JR Z,.equal
    LD A,($C796)
    AND B
    JR NZ,.hit
    JR .miss
.equal:
    LD A,($C795)
    AND C
    JR NZ,.hit
.miss:
    LD A,7
    RET
.hit:
    LD A,135
    RET
.exiting:
    LD C,0
    CALL cer_glyph
    LD A,($C797)
    AND (HL)
    JR NZ,.hit
    JR .miss

cer_glyph:
    LD A,($C791)
    LD L,A
    LD H,0
    LD DE,ce_bases
    ADD HL,DE
    LD A,(HL)
    LD L,A
    LD A,($C792)
    ADD A,L
    ADD A,C
    LD L,A
    LD A,($C793)
    AND 1
    ADD A,ce_glyphs/256
    LD H,A
    RET
cer_end:
    ASSERT (ce_glyphs & 255) == 0
