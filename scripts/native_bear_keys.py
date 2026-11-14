"""Original-glyph reference for the explicit native kind10 bear key grammar."""
from functools import lru_cache

from original_graphics import view
from presentation_fragments import mask_tiles


def bounded(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError('native bear field outside its declared domain')
    return value


def make_key(group, phase, coarse, row, column, background, color):
    group = bounded(group, 0, 15)
    phase = bounded(phase, 0, 15)
    coarse = bounded(coarse, 0, 1)
    row = bounded(row, 0, 2)
    column = bounded(column, 0, 3)
    index = (group << 9) | (phase << 5) | (coarse << 4) | (row << 2) | column
    return index.to_bytes(2, 'little')+bytes((bounded(background, 128, 255), 0,
                                           bounded(color, 1, 15), 10))


def fields(key):
    if len(key) != 6 or key[5] != 10 or key[3] or key[2] < 128 or not 1 <= key[4] <= 15:
        raise ValueError('complete unclipped native kind10 bear key required')
    index = int.from_bytes(key[:2], 'little')
    cell = index & 15
    if index >= 8192 or cell >= 12:
        raise ValueError('native bear key has reserved bits or an invalid cell')
    return index >> 9, (index >> 5) & 15, (index >> 4) & 1, cell >> 2, cell & 3


def validate_role(bank, identifier, key):
    _, _, _, row, column = fields(key)
    bounded(bank, 0, 1)
    bounded(identifier, 0, 127)
    if bank != int(row == 2) or identifier & 63 != (row*4+column if bank == 0 else column):
        raise ValueError('native bear key escaped its exact physical row/column role')
    return True


@lru_cache(None)
def masks(original, group, phase, coarse):
    if len(original) != 4096:
        raise ValueError('complete original4KiB glyph authority required')
    group = bounded(group, 0, 15)
    phase = bounded(phase, 0, 15)
    coarse = bounded(coarse, 0, 1)
    image = view(original, 0xFD00+original[0xEE7+group//2], 19, bool(group&1), 2)
    bitmap = image['pixels']+image['pixels'][-16:]
    result = mask_tiles(bitmap, 16, 20, phase, 3+coarse)
    if result['columns'] not in (3, 4) or result['rows'] != 3:
        raise ValueError('original bear escaped its declared fixed grid')
    return tuple(result['patterns'][row*result['columns']+column]
                 if column < result['columns'] else bytes(8)
                 for row in range(3) for column in range(4))


def construct(original, bank, key, backgrounds):
    group, phase, coarse, row, column = fields(key)
    if bank != int(row == 2):
        raise ValueError('native bear source mask belongs to another SCREEN2 bank')
    background = backgrounds.get(key[2])
    if (background is None or len(background) != 16 or background[:8] != bytes([255])*8
            or any(value >> 4 != value & 15 for value in background[8:])):
        raise ValueError('native bear requires a certified solid background in every row')
    mask = masks(original, group, phase, coarse)[row*4+column]
    return mask+bytes((key[4] << 4) | (value & 15) for value in background[8:])
