"""Immutable seven-pixel wordmark aligned to the original Activision baseline."""
from presentation_viewport_edges import expected_frame as previous_frame

FONT = {
    'R': (30, 17, 17, 30, 20, 18, 17),
    'E': (31, 16, 16, 30, 16, 16, 31),
    'T': (31, 4, 4, 4, 4, 4, 4),
    'O': (14, 17, 17, 17, 17, 17, 14),
    'W': (17, 17, 17, 21, 21, 27, 17),
    'K': (17, 18, 20, 24, 20, 18, 17),
    'S': (15, 16, 16, 14, 1, 1, 30),
}

def pixels(coarse=False):
    shift = int(coarse)
    points = set()
    for i, letter in enumerate('RETROWORKS'):
        for y, bits in enumerate(FONT[letter]):
            for x in range(5):
                if bits & (16 >> x):
                    points.add((197 + i * 5 + x + int(y < 3), 182 + y + shift))
    return points

def compile_tiles(coarse=False):
    points = pixels(coarse)
    pool, cells = [], []
    for row, columns in ((22, range(24, 31)), (23, range(24, 31))):
        for col in columns:
            pattern = bytes(sum((int((col * 8 + x, row * 8 + y) in points)
                                 << (7 - x)) for x in range(8)) for y in range(8))
            pool.append(pattern)
            cells.append((row, col, len(pool) - 1))
    ids = (*range(134, 144), *range(250, 256))
    if len(pool) > len(ids):
        raise ValueError('Credit exceeds the verified free bank2 tile IDs')
    return {ids[i]: p for i, p in enumerate(pool)}, [(r, c, ids[i]) for r, c, i in cells]

def audit_credit(vram):
    if len(vram) != 16384:
        raise ValueError('Complete VRAM required')
    for coarse in (False, True):
        tiles, _ = compile_tiles(coarse)
        if all(vram[4096 + i*8:4104 + i*8] == p and
               vram[12288 + i*8:12296 + i*8] == tile_colors(i, coarse)
               for i, p in tiles.items()):
            return
    raise ValueError('Credit is not one complete qualified vertical phase')

def tile_colors(identifier, coarse=False):
    return bytes([244] * (2 + int(coarse)) + [241] * (6 - int(coarse))) if 134 <= identifier <= 140 else bytes([241]) * 8

def shadow_credit(raw, vram):
    audit_credit(vram)
    if len(raw) != 4110:
        raise ValueError('Complete ownership snapshot required')
    tiles, cells = compile_tiles()
    expected = {(r, c): i for r, c, i in cells}
    names, video = bytearray(raw), bytearray(vram)
    for offset, identifier in enumerate(raw[:1536]):
        page, cell = divmod(offset, 768)
        row, col = divmod(cell, 32)
        if row < 16 or identifier not in tiles:
            continue
        if expected.get((row, col)) != identifier:
            raise ValueError('Credit outside exact aligned cells')
        at = 6144 + page * 1024 + cell
        if video[at] != identifier:
            raise ValueError('Credit physical NAME differs')
        names[offset] = video[at] = 128
    return bytes(names), bytes(video)

def expected_frame(meta, original, description, ram, raw, palette):
    result = bytearray(previous_frame(meta, original, description, ram, raw, palette))
    if description['hud']['blanked']:
        return bytes(result)
    for y in range(184, 192):
        result[y * 256 + 120:y * 256 + 192] = bytes([1]) * 72
    for x, y in pixels(description['coarse_shift']):
        result[y * 256 + x] = 15
    return bytes(result)
