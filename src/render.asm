; Fresh synthetic SCREEN2 backend. Canonical C000-C07F and INPUT are read-only.
INPUT       EQU $C100
PAGE        EQU $C200
BAND        EQU $C201
SRCLO       EQU $C202
SRCHI       EQU $C203
COLORPTR    EQU $C204
DESCPTR     EQU $C206
YPOS        EQU $C208
TILE        EQU $C209
ROOTX       EQU $C20A
ROW         EQU $C20B
COPIES      EQU $C20C
GAP         EQU $C20D
NAMEPTR     EQU $C20E
SAVEDSP     EQU $C210
PHASE       EQU $C212
DELTA       EQU $C214
STEPS       EQU $C216
TICKS       EQU $C218
PREVFIRE    EQU $C21A
PALFLAG     EQU $C21B
KIND        EQU $C21C
COLORINDEX  EQU $C21D
COLUMN      EQU $C21E
ROWCOUNT    EQU $C21F
READY       EQU $C2FE
SAT         EQU $C400
NAMES       EQU $C800

; DE includes the VRAM write bit; B=0 means256, otherwise1..255.
vdp_write:
    LD A,E
    OUT ($99),A
    LD A,D
    OUT ($99),A
    LD C,$98
vdp_stream:
.byte:
    OUTI
    JP NZ,.byte              ;29 standard MSX cycles between data writes
    RET

prepare:
    LD A,(PAGE)
    XOR 1
    LD (PAGE),A
    CALL clear_dynamic_names
    CALL stage_igloo
    LD A,(INPUT+24)
    RRCA
    RRCA
    RRCA
    RRCA
    AND 15
    CALL digit_tile
    LD (NAMES+32+27),A
    LD A,(INPUT+24)
    AND 15
    CALL digit_tile
    LD (NAMES+32+28),A
    LD A,(INPUT+28)
    ADD A,42
    LD (NAMES+32+30),A
    LD A,(INPUT+31)
    ADD A,A
    LD E,A
    LD A,(PAGE)
    OR E
    ADD A,A
    LD E,A
    LD D,0
    LD HL,fast_prepare_functions
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    EX DE,HL
    CALL call_hl
    CALL upload_names
    JP stage_sprites
call_hl:
    JP (HL)

clear_dynamic_names:
    LD (SAVEDSP),SP
    LD SP,NAMES+22*32
    LD DE,0
    DUP 192
    PUSH DE
    EDUP
    LD SP,(SAVEDSP)
    RET

digit_tile:
    CP 10
    JR C,.number
    ADD A,6                  ;A-F: tile16..21
    RET
.number:
    ADD A,42
    RET

stage_igloo:
    LD A,(INPUT+29)
    LD L,A
    LD H,0
    ADD HL,HL
    ADD HL,HL
    ADD HL,HL
    ADD HL,HL
    ADD HL,HL
    LD DE,igloo_data
    ADD HL,DE
    LD DE,NAMES+3*32+22
    DUP 4
    LD BC,8
    LDIR
    EX DE,HL
    LD BC,24
    ADD HL,BC
    EX DE,HL
    EDUP
    RET

prepare_band:
    LD A,(BAND)
    SRL A
    LD (ROW),A
    LD E,A
    LD D,0
    LD A,(BAND)
    AND 1
    JR NZ,.ice
    LD HL,INPUT+4
    ADD HL,DE
    LD A,(HL)
    LD (ROOTX),A
    LD HL,INPUT+12
    ADD HL,DE
    LD A,(HL)
    ADD A,2
    LD (KIND),A
    LD (COLORINDEX),A
    LD HL,INPUT+16
    ADD HL,DE
    LD A,(HL)
    LD (COPIES),A
    LD HL,INPUT+20
    ADD HL,DE
    LD A,(HL)
    INC A
    RLCA
    RLCA
    RLCA
    RLCA
    LD (GAP),A
    JR .position
.ice:
    LD HL,INPUT
    ADD HL,DE
    LD A,(HL)
    LD (ROOTX),A
    LD A,(INPUT+30)
    LD (KIND),A
    LD HL,INPUT+8
    ADD HL,DE
    LD A,(HL)
    LD (COLORINDEX),A
    LD A,3
    LD (COPIES),A
    LD A,32
    LD (GAP),A
.position:
    LD A,(INPUT+31)
    RLCA
    RLCA
    RLCA
    LD E,A
    LD A,(BAND)
    OR E
    LD E,A
    LD D,0
    LD HL,band_y_data
    ADD HL,DE
    LD A,(HL)
    LD (YPOS),A
    AND 6
    RRCA
    RRCA
    RRCA
    LD (SRCLO),A
    LD A,(KIND)
    RLCA
    RLCA
    RLCA
    RLCA
    LD E,A
    LD A,(ROOTX)
    AND 15
    ADD A,E
    ADD A,phase_data/256
    LD (SRCHI),A
    LD A,(COLORINDEX)
    ADD A,A
    LD E,A
    LD D,0
    LD HL,color_pointers
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    LD (COLORPTR),DE
    LD A,(INPUT+31)
    ADD A,A
    LD E,A
    LD A,(PAGE)
    OR E
    RLCA
    RLCA
    RLCA
    LD E,A
    LD A,(BAND)
    OR E
    ADD A,A
    LD E,A
    LD D,0
    LD HL,segment_lists
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    EX DE,HL
    LD A,(YPOS)
    AND 7
    JR NZ,.segment
    LD E,(HL)
    INC HL
    LD D,(HL)
    LD A,(SRCLO)
    LD L,A
    LD A,(SRCHI)
    LD H,A
    LD B,32
    CALL vdp_write
    LD A,D
    XOR $20
    LD D,A
    LD HL,(COLORPTR)
    LD B,32
    CALL vdp_write
    JP .names
.segment:
    LD E,(HL)
    INC HL
    LD D,(HL)
    INC HL
    LD B,(HL)
    INC HL
    LD C,(HL)
    INC HL
    LD (DESCPTR),HL
    LD A,B
    OR A
    JR Z,.names
    EX AF,AF'                ;count retained; DE is preserved by vdp_write
    LD A,(SRCLO)
    ADD A,C
    LD L,A
    LD A,(SRCHI)
    LD H,A
    CALL vdp_write
    EX AF,AF'
    LD B,A
    LD A,D
    XOR $20                  ;same fragment in SCREEN2 color table
    LD D,A
    LD HL,(COLORPTR)
    CALL vdp_write
    LD HL,(DESCPTR)
    JR .segment
.names:
stage_band_names:
    LD A,(BAND)
    AND 3
    RLCA
    RLCA
    RLCA
    RLCA
    RLCA
    ADD A,64
    LD E,A
    LD A,(INPUT+31)
    RLCA
    RLCA
    RLCA
    RLCA
    OR E
    LD E,A
    LD A,(PAGE)
    RLCA
    RLCA
    RLCA
    OR E
    LD (TILE),A
    LD A,(YPOS)
    AND $F8
    LD L,A
    LD H,0
    ADD HL,HL
    ADD HL,HL
    LD DE,NAMES
    ADD HL,DE
    LD (NAMEPTR),HL
    CALL .one_row
    LD A,(YPOS)
    AND 7
    RET Z
    LD HL,(NAMEPTR)
    LD DE,32
    ADD HL,DE
    LD (NAMEPTR),HL
    LD A,(TILE)
    ADD A,4
    LD (TILE),A
.one_row:
    LD A,(ROOTX)
    LD E,A
    LD D,0
    LD HL,x_columns_data
    ADD HL,DE
    LD A,(HL)
    LD C,A
    LD HL,(NAMEPTR)
    LD A,L
    OR C
    LD L,A
    LD A,(TILE)
    LD D,A
    LD A,(COPIES)
    LD B,A
    LD A,(GAP)
    RRCA
    RRCA
    RRCA
    RRCA
    LD E,A
    ADD A,A
    ADD A,E
    LD E,A
    JP stage_fixed_row

; HL=first cell,C=column,D=tile base,E=column spacing,B=copy count.
stage_fixed_row:
    LD A,B
    OR A
    RET Z
.copy:
    LD A,C
    CP 28
    JR NC,.clipped
    LD A,D
    DUP 4
    LD (HL),A
    INC HL
    INC A
    EDUP
    JR .next
.clipped:
    PUSH BC
    PUSH DE
    LD E,D
    CALL put_four
    POP DE
    POP BC
.next:
    LD A,C
    ADD A,E
    CP 31
    JR C,.column
    SUB 30
.column:
    LD C,A
    LD A,L
    AND $E0
    OR C
    LD L,A
    DJNZ .copy
    RET

put_four:
    LD A,C
    CP 28
    JR NC,.clipped
    DUP 4
    LD (HL),E
    INC HL
    INC E
    EDUP
    RET
.clipped:
    LD B,4
.tile:
    LD A,C
    CP 31
    RET NC
    LD (HL),E
    INC HL
    INC E
    INC C
    DJNZ .tile
    RET

upload_names:
    LD A,(PAGE)
    RLCA
    RLCA
    ADD A,$58
    LD D,A
    LD E,32
    LD HL,NAMES+32
    LD B,32
    CALL vdp_write
    INC D
    LD E,$40                 ;rows10-11
    LD HL,NAMES+10*32
    LD B,64
    CALL vdp_write
    LD E,$A0                 ;rows13-18, includes cleared transition rows15/16
    LD HL,NAMES+13*32
    LD B,192
    CALL vdp_write
    INC D
    LD E,$80                 ;rows20-21
    LD HL,NAMES+20*32
    LD B,64
    CALL vdp_write
    LD A,(PAGE)
    RLCA
    RLCA
    ADD A,$58
    LD D,A
    LD E,3*32+22
    LD HL,NAMES+3*32+22
    LD A,4
    LD (ROWCOUNT),A
.igloo:
    LD B,8
    CALL vdp_write
    LD A,E
    ADD A,32
    LD E,A
    LD BC,24
    ADD HL,BC
    LD A,(ROWCOUNT)
    DEC A
    LD (ROWCOUNT),A
    JR NZ,.igloo
    RET

stage_sprites:
    LD HL,SAT
    LD A,(INPUT+24)
    CP 152
    JR NC,.clipped
    AND 1
    JR .variant
.clipped:
    SUB 150
.variant:
    LD E,A
    ADD A,A
    ADD A,E
    ADD A,A                  ;six16x16patterns per variant
    ADD A,A
    ADD A,A                  ;hardware pattern number multiplies4
    LD D,A
    LD A,(INPUT+24)
    LD E,A
    PUSH HL
    LD HL,x_positions_data
    LD B,0
    LD C,E
    ADD HL,BC
    LD E,(HL)
    POP HL
    LD A,(INPUT+25)
    DEC A
    LD C,A
    DUP 2
    LD (HL),C
    INC HL
    LD (HL),E
    INC HL
    LD (HL),D
    INC HL
    LD (HL),6
    INC HL
    LD A,D
    ADD A,4
    LD D,A
    LD (HL),C
    INC HL
    LD (HL),E
    INC HL
    LD (HL),D
    INC HL
    LD (HL),7
    INC HL
    LD A,D
    ADD A,4
    LD D,A
    LD (HL),C
    INC HL
    LD (HL),E
    INC HL
    LD (HL),D
    INC HL
    LD (HL),15
    INC HL
    LD A,D
    ADD A,4
    LD D,A
    LD A,C
    ADD A,16
    LD C,A
    EDUP
    LD A,(INPUT+26)
    AND 1
    ADD A,A
    ADD A,60
    ADD A,A
    ADD A,A
    LD D,A
    LD A,(INPUT+26)
    LD E,A
    PUSH HL
    LD HL,x_positions_data
    LD B,0
    LD C,E
    ADD HL,BC
    LD E,(HL)
    POP HL
    LD A,(INPUT+27)
    DEC A
    LD C,A
    DUP 2
    LD (HL),C
    INC HL
    LD (HL),E
    INC HL
    LD (HL),D
    INC HL
    LD (HL),15
    INC HL
    LD A,D
    ADD A,4
    LD D,A
    LD A,C
    ADD A,16
    LD C,A
    EDUP
    LD (HL),208
    RET

commit:
commit_begin:
    LD HL,SAT
    LD DE,$5B00
    LD B,33
    CALL vdp_write
    LD A,(PAGE)
    ADD A,6
    OUT ($99),A
    LD A,$82
    OUT ($99),A
    LD A,(INPUT+28)
    OR A
    LD A,4
    JR Z,.backdrop
    LD A,1
.backdrop:
    OUT ($99),A
    LD A,$87
    OUT ($99),A
commit_end:
    RET
