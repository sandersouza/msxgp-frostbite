; Specialized traversal, exact original capture/history/dirty union.
    INCLUDE "symbols.inc"
    INCLUDE "floe-spans.inc"
    ORG $EFC1
aj_entry:
    CALL p_dirty_capture
    LD A,113
    CALL t_mapper
    CALL aj_body
    LD A,2
    JP t_mapper
aj_ram_end:
    ASSERT $ <= $F000
    ORG $B800
aj_body:
    LD HL,$C540
    LD A,(PAGE)
    OR A
    JR Z,.history
    LD L,$A0
.history:
    LD (p_fd_history),HL
    PUSH HL
    POP IX
    LD IY,p_fd_state
    XOR A
    LD (p_fd_rows),A
    LD (p_fd_rows+1),A
    LD (p_fd_rows+2),A
    LD A,(IX)
    CP 1
    JP NZ,.full
    LD A,(p_fd_state+50)
    CP (IX+50)
    JP NZ,.full
    LD A,(p_fd_state+51)
    CP (IX+51)
    JP NZ,.full
    LD A,(IX+1)
    CP 32
    JR NZ,.old_not_blank
    LD A,(IY+1)
    CP 32
    JP Z,.save
    JP .full
.old_not_blank:
    LD A,(IY+1)
    CP 32
    JP Z,.full
    XOR (IX+1)
    BIT 1,A
    JP NZ,.full
    LD C,A
    BIT 0,C
    JR Z,.gradient
    LD A,255
    LD (p_fd_rows),A
    LD A,1
    LD (p_fd_rows+1),A
.gradient:
    LD A,C
    AND 28
    JR Z,.header
    LD A,(p_fd_rows)
    OR 8
    LD (p_fd_rows),A
.header:
    LD A,(p_fd_state+3)
    CP (IX+3)
    JP NZ,.changed2
    LD A,(p_fd_state+4)
    CP (IX+4)
    JP NZ,.changed2
    LD A,(p_fd_state+5)
    CP (IX+5)
    JP NZ,.changed2
    LD A,(p_fd_state+6)
    CP (IX+6)
    JP NZ,.changed2
    LD A,(p_fd_state+7)
    CP (IX+7)
    JP NZ,.changed2
    LD A,(p_fd_state+8)
    CP (IX+8)
    JP NZ,.changed2
    LD A,(p_fd_state+9)
    CP (IX+9)
    JP NZ,.changed2
    LD A,(p_fd_state+10)
    CP (IX+10)
    JP NZ,.changed2
    JP .igloo5
.changed2:
    LD A,(p_fd_rows)
    OR 7
    LD (p_fd_rows),A
.igloo5:
    LD A,(p_fd_state+11)
    CP (IX+11)
    JP NZ,.changed3
    LD A,(p_fd_state+12)
    CP (IX+12)
    JP NZ,.changed3
    JP .igloo4
.changed3:
    LD A,(p_fd_rows)
    OR 32
    LD (p_fd_rows),A
.igloo4:
    LD A,(p_fd_state+13)
    CP (IX+13)
    JP NZ,.changed4
    LD A,(p_fd_state+14)
    CP (IX+14)
    JP NZ,.changed4
    JP .igloo3
.changed4:
    LD A,(p_fd_rows)
    OR 16
    LD (p_fd_rows),A
.igloo3:
    LD A,(IX+15)
    CP (IY+15)
    JP Z,.bear
    LD A,(p_fd_rows)
    OR 8
    LD (p_fd_rows),A
.bear:
    LD A,(p_fd_state+16)
    CP (IX+16)
    JP NZ,.changed5
    LD A,(p_fd_state+17)
    CP (IX+17)
    JP NZ,.changed5
    LD A,(p_fd_state+18)
    CP (IX+18)
    JP NZ,.changed5
    LD A,(p_fd_state+19)
    CP (IX+19)
    JP NZ,.changed5
    JP .objects
.changed5:
    LD A,(p_fd_rows)
    OR 192
    LD (p_fd_rows),A
    LD A,(p_fd_rows+1)
    OR 1
    LD (p_fd_rows+1),A
.objects:
    LD A,0
    LD (p_w_row),A
    LD A,(p_fd_state+20)
    CP (IX+20)
    JP NZ,.object_changed0
    LD A,(p_fd_state+21)
    CP (IX+21)
    JP NZ,.object_changed0
    LD A,(p_fd_state+22)
    CP (IX+22)
    JP NZ,.object_changed0
    LD A,(p_fd_state+23)
    CP (IX+23)
    JP NZ,.object_changed0
    LD A,(p_fd_state+24)
    CP (IX+24)
    JP NZ,.object_changed0
    JP .object_next0
.object_changed0:
    CALL x_actor_dirty_gate
.object_next0:
    LD A,1
    LD (p_w_row),A
    LD A,(p_fd_state+25)
    CP (IX+25)
    JP NZ,.object_changed1
    LD A,(p_fd_state+26)
    CP (IX+26)
    JP NZ,.object_changed1
    LD A,(p_fd_state+27)
    CP (IX+27)
    JP NZ,.object_changed1
    LD A,(p_fd_state+28)
    CP (IX+28)
    JP NZ,.object_changed1
    LD A,(p_fd_state+29)
    CP (IX+29)
    JP NZ,.object_changed1
    JP .object_next1
.object_changed1:
    CALL x_actor_dirty_gate
.object_next1:
    LD A,2
    LD (p_w_row),A
    LD A,(p_fd_state+30)
    CP (IX+30)
    JP NZ,.object_changed2
    LD A,(p_fd_state+31)
    CP (IX+31)
    JP NZ,.object_changed2
    LD A,(p_fd_state+32)
    CP (IX+32)
    JP NZ,.object_changed2
    LD A,(p_fd_state+33)
    CP (IX+33)
    JP NZ,.object_changed2
    LD A,(p_fd_state+34)
    CP (IX+34)
    JP NZ,.object_changed2
    JP .object_next2
.object_changed2:
    CALL x_actor_dirty_gate
.object_next2:
    LD A,3
    LD (p_w_row),A
    LD A,(p_fd_state+35)
    CP (IX+35)
    JP NZ,.object_changed3
    LD A,(p_fd_state+36)
    CP (IX+36)
    JP NZ,.object_changed3
    LD A,(p_fd_state+37)
    CP (IX+37)
    JP NZ,.object_changed3
    LD A,(p_fd_state+38)
    CP (IX+38)
    JP NZ,.object_changed3
    LD A,(p_fd_state+39)
    CP (IX+39)
    JP NZ,.object_changed3
    JP .object_next3
.object_changed3:
    CALL x_actor_dirty_gate
.object_next3:
    LD A,4
    LD (p_w_row),A
    LD A,(IX+48)
    CP (IY+48)
    LD A,0
    JR Z,.delta
    INC A
.delta:
    LD (p_fd_delta),A
    LD A,0
    LD (p_w_row),A
    LD A,(p_fd_delta)
    OR A
    JR NZ,.floe_changed0
    LD A,(p_fd_state+40)
    CP (IX+40)
    JR NZ,.floe_changed0
    LD A,(p_fd_state+41)
    CP (IX+41)
    JR NZ,.floe_changed0
    JR .floe_next0
.floe_changed0:
    LD A,(p_fd_rows+aj_floe_offset0)
    OR aj_floe_mask0
    LD (p_fd_rows+aj_floe_offset0),A
.floe_next0:
    LD A,1
    LD (p_w_row),A
    LD A,(p_fd_delta)
    OR A
    JR NZ,.floe_changed1
    LD A,(p_fd_state+42)
    CP (IX+42)
    JR NZ,.floe_changed1
    LD A,(p_fd_state+43)
    CP (IX+43)
    JR NZ,.floe_changed1
    JR .floe_next1
.floe_changed1:
    LD A,(p_fd_rows+aj_floe_offset1)
    OR aj_floe_mask1
    LD (p_fd_rows+aj_floe_offset1),A
.floe_next1:
    LD A,2
    LD (p_w_row),A
    LD A,(p_fd_delta)
    OR A
    JR NZ,.floe_changed2
    LD A,(p_fd_state+44)
    CP (IX+44)
    JR NZ,.floe_changed2
    LD A,(p_fd_state+45)
    CP (IX+45)
    JR NZ,.floe_changed2
    JR .floe_next2
.floe_changed2:
    LD A,(p_fd_rows+aj_floe_offset2)
    OR aj_floe_mask2
    LD (p_fd_rows+aj_floe_offset2),A
.floe_next2:
    LD A,3
    LD (p_w_row),A
    LD A,(p_fd_delta)
    OR A
    JR NZ,.floe_changed3
    LD A,(p_fd_state+46)
    CP (IX+46)
    JR NZ,.floe_changed3
    LD A,(p_fd_state+47)
    CP (IX+47)
    JR NZ,.floe_changed3
    JR .floe_next3
.floe_changed3:
    LD A,(p_fd_rows+aj_floe_offset3)
    OR aj_floe_mask3
    LD (p_fd_rows+aj_floe_offset3),A
.floe_next3:
    LD A,4
    LD (p_w_row),A
    LD A,(IX+49)
    CP (IY+49)
    JP Z,.save
    LD A,(p_fd_rows+2)
    OR 192
    LD (p_fd_rows+2),A
    JP .save
.full:
    LD A,255
    LD (p_fd_rows),A
    LD (p_fd_rows+1),A
    LD (p_fd_rows+2),A
.save:
    LD HL,p_fd_state
    LD DE,(p_fd_history)
    LD BC,64
    DUP 64
    LDI
    EDUP
    RET
aj_body_end:
    ASSERT $ <= $C000

