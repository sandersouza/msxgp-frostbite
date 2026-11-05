"""Compile direct header column masks; generated original assets stay local.

The section order is the ROM ABI used by presentation_direct_header.asm.
Every compiled record is checked against a separate source-pixel projection.
"""
from itertools import product

from presentation_constructors import HEADER_PARTS
from presentation_static_assets import header_fragments


def project_pair(source, a, b, kind):
    starts = ((1,), (-7, 5), (-3,), (-11, 1), (-11,))[kind]
    result = bytearray(8)
    for glyph, start in zip((a, b), starts):
        at = 0xF00 + glyph * 8 if glyph < 32 else 0xF53 if glyph == 32 else 0xD6D
        for y, row in enumerate(source[at:at + 8][::-1]):
            for x in range(8):
                if row & (128 >> x):
                    for target in range(start + 3*x//2, start + 3*(x+1)//2):
                        if 0 <= target < 8:
                            result[y] |= 128 >> target
    return bytes(result)


def compile_dictionary(source):
    if len(source) != 4096:
        raise ValueError('header dictionary requires the 4 KiB source image')
    fragments = header_fragments(source)
    payload = bytearray()
    sections = []

    def add(name, cases):
        start = len(payload)
        for a, b, kind in cases:
            first, second = HEADER_PARTS[kind]
            compiled = fragments[a*40 + first*8:a*40 + first*8 + 8]
            if second is not None:
                other = fragments[b*40 + second*8:b*40 + second*8 + 8]
                compiled = bytes(x | y for x, y in zip(compiled, other))
            if compiled != project_pair(source, a, b, kind):
                raise ValueError(('header projection mismatch', name, a, b, kind))
            payload.extend(compiled)
        sections.append(dict(name=name, offset=start, size=len(payload)-start))

    add('regular_pair_1', ((a, b, 1) for a, b in product(range(16), repeat=2)))
    add('regular_pair_3', ((a, b, 3) for a, b in product(range(16), repeat=2)))
    for kind in (0, 2, 4):
        add('single_' + str(kind), ((a, 0, kind) for a in range(34)))
    add('lower_temp_icon', ((a, 32, 3) for a in range(16)))
    add('lower_icon_level', ((32, b, 1) for b in (10, 33)))
    add('lower_level_blank', ((a, 10, 3) for a in (10, 33)))
    add('lower_blank_lives', ((10, b, 1) for b in range(32)))
    assert len(payload) == 5328
    return bytes(payload), sections
