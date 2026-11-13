"""Declared grid24 view. Canonical gameplay is never transformed."""
from copy import deepcopy

def anchor(kind,lane):
    if kind not in ('enemy','floe')or type(lane)is not int or lane not in range(4):
        raise ValueError('declared band and lane0..3 required')
    return (152 if kind=='enemy'else 168)-24*lane

def contact_y(y,coarse):
    if type(y)is not int or not 0<=y<=255 or coarse not in(0,1):raise ValueError('byte contact and coarse0/1 required')
    old=[63+coarse,89+coarse,115+coarse,141+coarse,167+coarse,185+coarse]
    new=[63+coarse,96,120,144,168,185+coarse]
    if y<=old[0]or y>=old[-1]:return y
    for a,b,c,d in zip(old,old[1:],new,new[1:]):
        if y<=b:return c+(y-a)*(d-c)//(b-a)
    raise AssertionError('bounded contact segment missing')

def player_delta(origin,coarse):
    if type(origin)is not int or not 0<=origin<=255 or coarse not in(0,1):raise ValueError('byte player origin and coarse0/1 required')
    contact=origin+36+coarse
    return contact_y(contact,coarse)-contact if contact<256 else 0

def delta_table():return bytes(player_delta(y,c)for c in range(2)for y in range(256))

def names(raw,lane,page,rotation):
    if len(raw)!=30 or page not in(0,1)or type(rotation)is not int or rotation not in range(0,30,3):raise ValueError('whole30-cell program, page and tile rotation required')
    base=(25,9,35,19)[lane]if type(lane)is int and lane in range(4)else None
    if base is None or any(x!=129 and not 25+64*page<=x<=38+64*page for x in raw):raise ValueError('phase0 lane0 program contains invalid physical role')
    ordered=raw[-rotation:]+raw[:-rotation]if rotation else raw
    return bytes((129 if lane<2 else 130)if x==129 else x-25+base for x in ordered)

def span(kind,lane):
    row=anchor(kind,lane)//8
    return bytes((1<<(row%8))if bank==row//8 else 0 for bank in range(3))

def actor_segments(page,lane):
    if page not in(0,1)or lane not in range(4):raise ValueError('valid page/lane required')
    pairs=(((2,3),(2,6)),((2,0),(1,16)),((1,10),(1,13)),((1,4),(1,7)))
    return tuple((bank,slot+64*page)for bank,slot in pairs[lane])

def dirty_rows(previous,current):
    if len(current)!=64 or previous is not None and len(previous)!=64:raise ValueError('whole visual histories required')
    if previous is None or not previous[0]:return set(range(24))
    old,new=previous[1],current[1]
    if (old==32)!=(new==32)or(old^new)&2 or previous[50:52]!=current[50:52]:return set(range(24))
    if new==32:return set()
    rows=set()
    if(old^new)&1:rows.update(range(9))
    if(old^new)&28:rows.add(3)
    if previous[3:11]!=current[3:11]:rows.update(range(3))
    if previous[11:13]!=current[11:13]:rows.add(5)
    if previous[13:15]!=current[13:15]:rows.add(4)
    if previous[15]!=current[15]:rows.add(3)
    coarse=(new>>1)&1
    if previous[16:20]!=current[16:20]:rows.update(range((51+coarse)//8,(70+coarse)//8+1))
    for lane in range(4):
        at=20+lane*5
        if previous[at:at+5]!=current[at:at+5]:rows.add(anchor('enemy',lane)//8)
        at=40+lane*2
        if previous[at:at+2]!=current[at:at+2]or previous[48]!=current[48]:rows.add(anchor('floe',lane)//8)
    if previous[49]!=current[49]:rows.update((22,23))
    return rows

def expected_frame(meta,original,description,ram,raw,palette):
    """Independent role-aware pixel view; reads no generated target assets."""
    from graphics_mapping import map_frame,map_x,map_y,palette_map
    from original_graphics import view
    from presentation_model import pixels
    from presentation_player_palette import player_color,adapted_frame
    if not meta.get('grid24'):return adapted_frame(meta,original,description,ram,raw,palette)
    if meta['grid24'].get('view')!='grid24-v1':raise ValueError('unknown layout adaptation')
    colors=palette_map(palette)
    base=deepcopy(description);base['objects']=[];base['floes']=[]
    for r in base['player']['rows']:r['pattern']=r['prefix_pattern']=0
    result=bytearray(map_frame(pixels(original,base),palette))
    if description['hud']['blanked']:return bytes(result)
    def put(x,y,color):
        x%=160
        if 8<=x<160 and 0<=y<192:
            first=y*256+map_x(x);result[first:first+map_x(x+1)-map_x(x)]=bytes([color])*(map_x(x+1)-map_x(x))
    for obj in description['objects']:
        image=view(original,obj['address'],8,obj['reflect'])
        for i,bit in enumerate(image['pixels']):
            if bit:put(obj['x']+i%8,anchor('enemy',obj['row'])+i//8,colors[obj['color']])
    for rect in description['floes']:
        y=anchor('floe',rect['row'])+rect['y']-(174-26*rect['row'])
        for dx in range(rect['width']):put(rect['x']+dx,y,colors[rect['color']])
    tagged=deepcopy(description)
    for r in tagged['player']['rows']:
        for key in('color','prefix_color','suffix_color'):r[key]|=1
    image=pixels(original,tagged);delta=player_delta(ram[0x64],int(ram[0x68]>=150))
    normal=bool(meta.get('player_palette'))and not ram[0x6b]and not ram[0x70]
    for at,code in enumerate(image):
        if not code&1:continue
        sy,x=divmod(at,160);y=map_y(sy)
        if y is None or not 0<=y+delta<192:continue
        color=player_color(code&254,colors[code&254])if normal else colors[code&254]
        first=(y+delta)*256+map_x(x);width=map_x(x+1)-map_x(x)
        result[first:first+width]=bytes([color])*width
    return bytes(result)
