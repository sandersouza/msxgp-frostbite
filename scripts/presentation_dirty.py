"""Visible-state dependencies for offscreen SCREEN2 row transactions.

Only the presentation depends on this shadow. Canonical gameplay never reads it.
"""


def scene(ram,rng_index,*,layout=0,width=0):
    if len(ram)!=128 or len(rng_index)!=256 or any(v>7 for v in rng_index) or layout not in (0,1) or width not in (0,1):
        raise ValueError('whole source RAM, calibrated8-profile RNG map and binary view flags required')
    result=bytearray(64);result[0]=1
    night=int(bool(ram[0x45]&128 or ram[0x4B]&4));coarse=int(ram[0x68]>=150)
    result[1]=32 if ram[0x3F]&128 else rng_index[ram[2]]*4+coarse*2+night
    result[3:6]=bytes(ram[0x48:0x4B]);result[6]=ram[0x65];result[7]=ram[0x4C];result[8]=ram[0x47]
    result[9]=int(ram[0x4B]>=20)
    result[10]=int(not ram[0x65]&240 and not ram[0x71] and not ram[1]&8)
    result[11:16]=bytes(ram[0x40:0x45])
    result[16:20]=bytes((ram[0x68],ram[0x6F],ram[0x6C]&16,int(ram[0x4B]>=3)))
    signed=lambda v:(v>>4)-16 if v&128 else v>>4
    first,second=signed(ram[0x1C]),signed(ram[0x1D])
    for row in range(4):
        at=20+row*5
        result[at:at+5]=bytes((ram[0x23+row],ram[0x11+row]&128,ram[0x27+row]&254,ram[0x58+row],ram[0x54+row]))
        result[40+row*2:42+row*2]=bytes(((ram[0x1F+row]-first)%160,ram[0x2B+row]&254))
    result[48]=(4+first-second)&255
    result[49]=max(0,min(7,(ram[0x46]&31)-12))
    result[50]=layout;result[51]=width
    return bytes(result)


def dirty_rows(previous,current):
    if len(current)!=64 or current[0]!=1 or previous is not None and len(previous)!=64:
        raise ValueError('complete64-byte normalized visual histories required')
    all_rows=set(range(24))
    if previous is None or not previous[0]:return all_rows
    old,new=previous[1],current[1]
    if (old==32)!=(new==32) or (old^new)&2 or previous[50:52]!=current[50:52]:return all_rows
    if new==32:return set()
    rows=set()
    if (old^new)&1:rows.update(range(9))
    if (old^new)&28:rows.add(3)
    if previous[3:11]!=current[3:11]:rows.update(range(3))
    if previous[11:13]!=current[11:13]:rows.add(5)
    if previous[13:15]!=current[13:15]:rows.add(4)
    if previous[15]!=current[15]:rows.add(3)
    coarse=(new>>1)&1
    def span(y,height):rows.update(range(y//8,(y+height-1)//8+1))
    if previous[16:20]!=current[16:20]:span(51+coarse,20)
    for row in range(4):
        at=20+row*5
        if previous[at:at+5]!=current[at:at+5]:span(153-row*26+coarse,8)
        at=40+row*2
        if previous[at:at+2]!=current[at:at+2] or previous[48]!=current[48]:span(167-row*26+coarse,7)
    if previous[49]!=current[49]:rows.update((22,23))
    return rows
