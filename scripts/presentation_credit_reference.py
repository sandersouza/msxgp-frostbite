"""Separated lowercase pixel lettering matching the owner's supplied reference."""

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

