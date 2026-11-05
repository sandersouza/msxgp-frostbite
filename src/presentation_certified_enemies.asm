; Certified native enemy eligibility reuse, AB diagnostic.
; Current-picture preflight proves previous SAT lanes safe; reconstruct only
; disposable lane scratch and preserve the exact full fallback. No new RAM.
; External entrypoints A50D, AA00 and AA03 and the A50D..AA25 allocation remain.
; The independent ready-picture admission change is made by the maintained builder.
    INCLUDE "symbols.inc"
    INCLUDE "world-addresses.inc"
    ORG $A50D
; All state derives from the sealed picture snapshot. Carry accepts sprites.
x_hybrid:
    LD A,(p_w_mode)
    LD B,A
    LD A,(p_w_base)
    OR B
    SCF
    RET Z
    ; A previous lane whose current-picture preflight stayed valid needs
    ; no second SAT-capacity/edge/P0-rectangle eligibility scan. The preflight
    ; base is at most19 slots; four three-copy lanes total at most31 slots.
    LD A,(p_w_row)
    LD L,A
    LD H,0
    LD DE,x_lane_bits
    ADD HL,DE
    LD B,(HL)
    LD A,(x_invalid)
    CPL
    AND B
    LD B,A
    LD A,(x_prev_sat)
    AND B
    JR Z,.full_eligibility
    CALL ab_certified_setup
    JP x_accepted
.full_eligibility:
    CALL x_eligible
    RET NC
    LD A,(p_w_row)
    LD L,A
    LD H,0
    LD DE,x_lane_bits
    ADD HL,DE
    LD A,(x_prev_sat)
    AND (HL)
    JP NZ,x_accepted
    ; Hardware path only after both NAME rows were replaced this transaction.
    ; No retained tile underneath the new sprite, no semantic-key assumption.
    LD A,(p_w_y)
    DUP 3
    SRL A
    EDUP
    CALL x_row_dirty
    RET Z
    LD A,(p_w_y)
    ADD A,7
    DUP 3
    SRL A
    EDUP
    CALL x_row_dirty
    RET Z
    JP x_accepted
x_eligible:
    LD A,(p_w_mode)
    LD E,A
    LD D,0
    LD HL,x_counts
    ADD HL,DE
    LD A,(HL)
    LD (x_n),A
    LD B,A
    LD A,(p_sat_bytes)
    DEC A
    DUP 2
    SRL A
    EDUP
    ADD A,B
    CP 32
    RET NC
    XOR A
    LD (x_clip),A
    ; Multi-copy edge lanes retain the exact tile path; mode0 gets a mask.
    LD A,(p_w_mode)
    ADD A,A
    ADD A,A
    LD E,A
    LD D,0
    LD HL,p_world_copies
    ADD HL,DE
    LD (x_offsets),HL
    LD A,(x_n)
    LD B,A
.edges:
    LD A,(p_w_base)
    ADD A,(HL)
    CALL normalize_x
    CP 8
    JR C,.edge
    CP 153
    JR C,.edge_ready
.edge:
    LD C,A
    LD A,(p_w_mode)
    OR A
    JR NZ,.reject
    LD A,C
    LD (x_clip),A
.edge_ready:
    INC HL
    DJNZ .edges
    ; Every hardware16-row rectangle counts, including transparent rows.
    ; HMOVE has exactly one covering rectangle on all world scanlines.
    LD A,(x_n)
    INC A
    LD C,A
    ; Only P0 rectangles can intersect75..169. Door32..47 and logo>=181
    ; are disjoint; previous enemy lanes have26-row pitch; HMOVE counted above.
    LD A,(p_s_static_start)
    LD B,A
    OR A
    JR Z,.accept
    LD HL,SAT
.scan:
    LD A,(HL)
    INC A
    LD E,A
    LD A,(p_w_y)
    SUB E
    JR NC,.after
    NEG
.after:
    CP 16
    JR NC,.next
    INC C
    LD A,C
    CP 5
    JR NC,.reject
.next:
    LD DE,4
    ADD HL,DE
    DJNZ .scan
    JR .accept
.reject:
    OR A
    RET
.accept:
    SCF
    RET
x_accepted:
    LD A,(p_w_row)
    LD L,A
    LD H,0
    LD DE,x_lane_bits
    ADD HL,DE
    LD B,(HL)
    LD A,(PAGE)
    ADD A,$A8
    LD L,A
    LD H,$E8
    LD A,(HL)
    OR B
    LD (HL),A
    LD A,(PAGE)
    ADD A,A
    ADD A,A
    LD B,A
    LD A,(p_w_row)
    ADD A,B
    LD L,A
    LD H,0
    LD DE,$E8A0
    ADD HL,DE
    LD A,(p_w_base)
    AND 1
    LD B,A
    LD A,(p_w_group)
    ADD A,A
    OR B
    INC A                 ;zero cache value is invalid after bootstrap
    CP (HL)
    LD (HL),A
    PUSH AF
    LD A,L
    ADD A,16
    LD L,A
    LD A,(x_clip)
    LD B,A
    LD A,(HL)
    LD (HL),B
    CP B
    JR NZ,.clip_changed
    POP AF
    JR Z,.cached
    JR .upload
.clip_changed:
    POP AF
.upload:
    DEC A
    LD L,A
    LD H,0
    DUP 5
    ADD HL,HL
    EDUP
    LD DE,$9400
    ADD HL,DE
    PUSH HL
    LD A,(p_w_row)
    LD L,A
    LD H,0
    DUP 5
    ADD HL,HL
    EDUP
    LD A,(PAGE)
    LD B,A
    ADD A,A
    ADD A,B
    ADD A,$7A
    LD D,A
    LD E,$40
    ADD HL,DE
    EX DE,HL
    POP HL
    LD A,(x_clip)
    OR A
    JR NZ,.clipped_upload
    CALL x_sgt_upload
    JR .cached
.clipped_upload:
    CALL x_pattern_read
    CALL x_clip_pattern
    LD HL,$C500
    LD B,32
    CALL vdp_write
.cached:
    LD A,(p_w_row)
    ADD A,18
    LD B,A
    LD A,(PAGE)
    OR A
    LD A,B
    JR Z,.slot
    ADD A,24
.slot:
    ADD A,A
    ADD A,A
    LD (x_pattern),A
    LD HL,(x_offsets)
    LD A,(x_n)
    LD B,A
    LD DE,(p_s_sat)
.emit:
    PUSH BC
    PUSH HL
    LD A,(p_w_base)
    ADD A,(HL)
    CALL normalize_x
    SRL A
    LD C,A
    ADD A,A
    ADD A,C
    ADD A,8
    LD C,A
    LD A,(p_w_y)
    DEC A
    LD (DE),A
    INC DE
    LD A,C
    LD (DE),A
    INC DE
    LD A,(x_pattern)
    LD (DE),A
    INC DE
    LD A,(p_w_color)
    LD (DE),A
    INC DE
    POP HL
    INC HL
    POP BC
    DJNZ .emit
    LD (p_s_sat),DE
    LD A,208
    LD (DE),A
    LD A,E
    INC A
    LD (p_sat_bytes),A
    SCF
    RET
x_counts: DB 1,2,2,3
; Existing disposable world scratch, no persistence across helper calls.
x_n EQU p_w_copy
x_offsets EQU p_w_name
x_pattern EQU p_w_origin
x_clip EQU p_w_line
x_clip_pattern:
    PUSH DE
    LD A,(x_clip)
    LD B,A
    AND 7
    ADD A,A
    LD L,A
    LD H,0
    LD DE,x_left_masks
    LD A,B
    CP 8
    JR C,.table
    LD DE,x_right_masks
.table:
    ADD HL,DE
    LD D,(HL)
    INC HL
    LD E,(HL)
    LD HL,$C500
    LD B,8
.row:
    LD A,(HL)
    AND D
    LD (HL),A
    LD A,L
    ADD A,16
    LD L,A
    LD A,(HL)
    AND E
    LD (HL),A
    LD A,L
    SUB 15
    LD L,A
    DJNZ .row
    POP DE
    RET
x_left_masks:
    DB 0,0,0,15,0,127,0,127,3,255,3,255,31,255,31,255
x_right_masks:
    DB 0,0,255,240,255,128,255,128,252,0,252,0,224,0,224,0
x_lane_bits: DB 1,2,4,8
; Rebuild disposable lane scratch; previous preflight scratch belongs
; to its last visited lane and cannot be reused. No persistent state is added.
ab_certified_setup:
    LD A,(p_w_mode)
    LD E,A
    LD D,0
    LD HL,x_counts
    ADD HL,DE
    LD A,(HL)
    LD (x_n),A
    LD A,E
    ADD A,A
    ADD A,A
    LD E,A
    LD HL,p_world_copies
    ADD HL,DE
    LD (x_offsets),HL
    XOR A
    LD (x_clip),A
    LD A,(p_w_mode)
    OR A
    RET NZ
    LD A,(p_w_base)
    CALL normalize_x
    CP 8
    JR C,.clip
    CP 153
    RET C
.clip:
    LD (x_clip),A
    RET
ab_certified_setup_end:

x_prev_sat EQU p_s_column
x_invalid EQU p_s_reflect
x_preflight:
    LD A,(PAGE)
    ADD A,$A8
    LD L,A
    LD H,$E8
    LD A,(HL)
    LD (HL),0
    LD (x_prev_sat),A
    XOR A
    LD (x_invalid),A
    LD (p_w_row),A
    LD A,($F03F)
    BIT 7,A
    RET NZ
.lane:
    LD A,(p_w_row)
    LD L,A
    LD H,0
    LD DE,x_lane_bits
    ADD HL,DE
    LD A,(x_prev_sat)
    AND (HL)
    JR Z,.next
    LD A,(p_sat_bytes)
    CP 81
    JR NC,.invalidate
    LD A,(p_w_row)
    LD E,A
    LD D,0
    LD HL,$F058
    ADD HL,DE
    LD A,(HL)
    LD (p_w_mode),A
    LD HL,$F054
    ADD HL,DE
    LD A,(HL)
    LD (p_w_base),A
    CALL p_world_row_y
    ADD A,153
    LD (p_w_y),A
    CALL x_eligible
    JR C,.next
.invalidate:
    LD A,(p_w_row)
    LD L,A
    LD H,0
    LD DE,x_lane_bits
    ADD HL,DE
    LD A,(x_invalid)
    OR (HL)
    LD (x_invalid),A
.next:
    LD HL,p_w_row
    INC (HL)
    LD A,(HL)
    CP 4
    JR NZ,.lane
    RET
x_apply_invalid:
    LD A,(x_invalid)
    ADD A,A
    LD L,A
    LD H,0
    LD DE,x_dirty_masks
    ADD HL,DE
    LD A,(p_fd_rows+1)
    OR (HL)
    LD (p_fd_rows+1),A
    INC HL
    LD A,(p_fd_rows+2)
    OR (HL)
    LD (p_fd_rows+2),A
    RET
    ASSERT $ <= $AA00
    DS $AA00-$,0
x_force_previous:
    JP x_preflight
x_force_apply:
    JP x_apply_invalid
x_dirty_masks:
    DB $00,$00
    DB $00,$18
    DB $80,$01
    DB $80,$19
    DB $30,$00
    DB $30,$18
    DB $B0,$01
    DB $B0,$19
    DB $06,$00
    DB $06,$18
    DB $86,$01
    DB $86,$19
    DB $36,$00
    DB $36,$18
    DB $B6,$01
    DB $B6,$19
x_hybrid_end:
    ASSERT $ <= $AA68
