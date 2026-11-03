; Bank1 is already mapped. A=SCREEN2 row -> CF iff a visible floe will define
; ALL32 CPU NAME bytes before objects/HUD. Read-only predicate; no mapper writes.
p_template_background_covered:
    CP 24
    RET NC
    LD E,A
    LD D,0
    LD A,(p_bg_profile)
    CP 32
    JR Z,.uncovered
    LD A,(p_w_coarse)
    OR A
    LD HL,p_template_cover_normal
    JR Z,.lookup
    CP 1
    JR NZ,.uncovered
    LD HL,p_template_cover_coarse
.lookup:
    ADD HL,DE
    LD A,(HL)
    CP 4
    JR NC,.uncovered
    ADD A,$2B
    LD L,A
    LD H,$C0
    LD E,(HL)
    LD HL,p_world_color_data
    ADD HL,DE
    LD A,(HL)
    CP 4
    RET Z
    SCF
    RET
.uncovered:
    OR A                    ;clear carry even when A retains a nonzero selector
    RET
p_template_cover_normal:
    DB 255,255,255,255,255,255,255,255,255,255,255,3
    DB 255,255,2,2,255,1,1,255,0,0,255,255
p_template_cover_coarse:
    DB 255,255,255,255,255,255,255,255,255,255,255,3
    DB 3,255,2,2,255,1,1,255,255,0,255,255
