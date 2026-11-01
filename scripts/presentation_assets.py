"""Finite source fragments and allocation checks, not a runtime renderer.

All original-derived bytes are emitted only to the caller's local output tree.
The bank contains primitive tables, never route or full-frame playback data.
"""
import hashlib
import json
from pathlib import Path

from environment import ROOT
from graphics_mapping import map_x, palette_map


def _byte(value):
    if type(value) is not int or not 0 <= value <= 255: raise ValueError('uint8 required')
    return value


def reverse(mask):
    return int(f'{_byte(mask):08b}'[::-1], 2)


def clip_mask(x):
    if type(x) is not int or not 0 <= x < 160: raise ValueError('source X outside0..159')
    return sum(128 >> bit for bit in range(8) if 8 <= (x + bit) % 160 < 160)


def expand(mask, x):
    """Three screen-tile bytes for an eight-pixel source mask at any phase."""
    _byte(mask)
    if type(x) is not int or not 0 <= x < 160: raise ValueError('source X outside0..159')
    phase = x % 16; start = map_x(phase) & ~7; result = bytearray(3)
    for bit in range(8):
        if mask & (128 >> bit):
            for pixel in range(map_x(phase + bit) - start, map_x(phase + bit + 1) - start):
                result[pixel // 8] |= 128 >> (pixel % 8)
    return bytes(result)


def check_rectangles(rectangles):
    """TMS9918 evaluates complete 16x16 rectangles, including empty rows."""
    if len(rectangles) > 32: raise ValueError('sprite repair exceeds32 hardware slots')
    occupancy = [0] * 192
    for rectangle in rectangles:
        x, y = rectangle['x'], rectangle['y']
        if (type(x) is not int or type(y) is not int or not -32 <= x <= 255 or not 0 <= y < 192
                or rectangle['width'] != 16 or rectangle['height'] != 16):
            raise ValueError('invalid visible16x16 sprite rectangle')
        # Early-clock or fully clipped X does not remove the Y comparator slot.
        for line in range(y, min(192, y + 16)): occupancy[line] += 1
    peak = max(occupancy)
    if peak > 4: raise ValueError('sprite repair exceeds4 scanline slots')
    return {'max_per_line': peak, 'slots': len(rectangles), 'spt_bytes': len(rectangles) * 32}


def compile_assets(rom: bytes, out: Path, *, measured_palette: dict) -> dict:
    """Emit one bank of lossless fragments; require explicit measured RGB input.

    This resource manifest reserves two generations of128 tile IDs per bank.
    It does not assert that native work/caches or VBlank transfer budgets fit.
    """
    out = Path(out).resolve()
    if out.is_relative_to(ROOT) and not out.is_relative_to(ROOT / 'outputs'):
        raise ValueError('original-derived assets inside repository must stay under ignored outputs')
    if not isinstance(rom, bytes) or len(rom) != 4096: raise ValueError('complete original ROM required')
    if set(measured_palette) != set(range(0, 256, 2)): raise ValueError('all128 even source palette codes required')
    colors = palette_map(measured_palette)
    sections = {}; bank = bytearray()
    def add(name, data):
        sections[name] = {'offset': len(bank), 'size': len(data)}; bank.extend(data)
    add('expansion', b''.join(expand(mask, x) for x in range(16) for mask in range(256)))
    add('glyphs', rom[0xC00:])
    add('reverse', bytes(reverse(mask) for mask in range(256)))
    add('clip', bytes(clip_mask(x) for x in range(160)))
    add('colors', bytes(colors[code & 254] for code in range(256)))
    used = len(bank)
    if used > 16384: raise ValueError('fragment bank capacity exceeded')
    bank.extend(bytes([255]) * (16384 - used))
    vram = [('patterns', 0, 0x1800), ('names_a', 0x1800, 0x1B00), ('sat', 0x1B00, 0x1B80),
            ('names_b', 0x1C00, 0x1F00), ('colors', 0x2000, 0x3800), ('sprite_patterns', 0x3800, 0x3C00)]
    manifest = {'schema_version': 1, 'source_sha256': hashlib.sha256(rom).hexdigest(),
                'sha256': hashlib.sha256(bank).hexdigest(), 'used_bytes': used, 'bank_bytes': len(bank),
                'sections': sections, 'tile_generations': {'slots_each': 128, 'count': 2, 'banks': 3},
                'vram_regions': [{'name': name, 'start': start, 'end': end} for name, start, end in vram],
                'runtime_qualified': False,
                'pending': ['native RAM allocation', 'dirty-band/cache implementation', 'worst-case timing and transfer checks']}
    out = Path(out); out.mkdir(parents=True, exist_ok=False)
    (out / 'fragments.bin').write_bytes(bank)
    (out / 'fragments.inc').write_text('; Generated source primitive offsets, not frame playback.\n' +
        ''.join(f'PRESENTATION_{name.upper()}_OFFSET EQU ${section["offset"]:04X}\n' for name, section in sections.items()))
    (out / 'fragments.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest
