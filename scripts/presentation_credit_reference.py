"""Separated lowercase pixel lettering matching the owner's supplied reference."""
from presentation_credit import expected_frame as previous_frame

FONT = {
    'r': (0, 0, 11, 12, 8, 8, 8),
    'e': (0, 0, 6, 9, 15, 8, 7),
    't': (4, 4, 14, 4, 4, 5, 2),
    'o': (0, 0, 6, 9, 9, 9, 6),
    'w': (0, 0, 9, 9, 9, 15, 6),
    'k': (8, 8, 9, 10, 12, 10, 9),
    's': (0, 0, 7, 8, 6, 1, 14),
}

def pixels(coarse=False):
    points = set()
    for i, letter in enumerate('retroworks'):
        for y, bits in enumerate(FONT[letter]):
            for x in range(4):
                if bits & (8 >> x):
                    points.add((199 + i * 5 + x, 182 + y + int(coarse)))
    return points

def compile_tiles(coarse=False):
    points = pixels(coarse)
    ids = (*range(134, 144), *range(250, 254))
    tiles, cells = {}, []
    for row in (22, 23):
        for col in range(24, 31):
            identifier = ids[len(cells)]
            tiles[identifier] = bytes(sum(int((col*8+x,row*8+y)in points)<<(7-x) for x in range(8)) for y in range(8))
            cells.append((row,col,identifier))
    return tiles, cells

def tile_colors(identifier, coarse=False):
    return bytes([244] * (2 + int(coarse)) + [241] * (6 - int(coarse))) if 134 <= identifier <= 140 else bytes([241])*8

def audit_credit(vram):
    if len(vram) != 16384:
        raise ValueError('Complete VRAM required')
    for coarse in (False, True):
        tiles, _ = compile_tiles(coarse)
        if all(vram[4096+i*8:4104+i*8]==p and vram[12288+i*8:12296+i*8]==tile_colors(i,coarse) for i,p in tiles.items()):
            return
    raise ValueError('Credit is not one complete qualified reference-font phase')

def shadow_credit(raw,vram):
    audit_credit(vram)
    if len(raw)!=4110:
        raise ValueError('Complete ownership snapshot required')
    tiles,cells = compile_tiles()
    expected = {(r,c):i for r,c,i in cells}
    names,video = bytearray(raw),bytearray(vram)
    for offset,identifier in enumerate(raw[:1536]):
        page,cell=divmod(offset,768)
        row,col=divmod(cell,32)
        if row<16 or identifier not in tiles: continue
        if expected.get((row,col))!=identifier: raise ValueError('Reference credit outside exact cells')
        at=6144+page*1024+cell
        if video[at]!=identifier: raise ValueError('Reference credit physical NAME differs')
        names[offset]=video[at]=128
    return bytes(names),bytes(video)

def expected_frame(meta,original,description,ram,raw,palette):
    result=bytearray(previous_frame(meta,original,description,ram,raw,palette))
    if description['hud']['blanked']: return bytes(result)
    shift=description['coarse_shift']
    for x,y in __import__('presentation_credit').pixels(shift): result[y*256+x]=1
    for x,y in pixels(shift): result[y*256+x]=15
    return bytes(result)
