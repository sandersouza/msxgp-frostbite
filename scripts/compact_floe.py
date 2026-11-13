"""Exact interior floe geometry and independent v30 electrical-table oracle.

This component is not yet connected to the game. Player X outside9..153,
enemy contacts and shore contacts still require separate implementations.
"""
from functools import lru_cache
import hashlib

from original_graphics import SOURCE_SHA256
from presentation_contact14 import read_field
from stella_floe import control_pairs
from hazard_domain import shapes


def signed_nibble(value):
    value >>= 4
    return value if value < 8 else value - 16


def compile_footprints(controls, motion):
    if (not controls or len(motion) != 7 or any(type(x) is not int for x in motion)
            or any(len(pair) != 2 or any(type(x) is not int or not 0 <= x <= 255
                   or x & 15 for x in pair) for pair in controls)):
        raise ValueError('complete controls and seven integer row displacements required')
    groups = {bytes(7): 0}
    directory = bytearray()
    px = 80
    for pair in controls:
        for dx in range(160):
            rows = bytearray()
            for displacement in motion:
                mask = 0
                for copy in (0, 32, 64):
                    for plane in (-signed_nibble(pair[0]), 4 - signed_nibble(pair[1])):
                        left = (px + dx + copy + plane + displacement) % 160 - px
                        for bit in range(max(0, left), min(8, left + 8)):
                            mask |= 128 >> bit
                rows.append(mask)
            ident = groups.setdefault(bytes(rows), len(groups))
            if ident > 255:
                raise ValueError('footprints exceed byte-sized directory')
            directory.append(ident)
    return bytes(directory), tuple(groups)


def convolve(glyph, footprint, y, *, reflect=False):
    if len(glyph) != 19 or len(footprint) != 7 or type(y) is not int:
        raise ValueError('complete 19-byte glyph, seven-row footprint and source Y required')
    if y == 0:
        return False
    for dy, mask in enumerate(footprint):
        tag = y - 50 - dy
        if 0 <= tag < 19:
            pattern = glyph[tag]
            if reflect:
                pattern = int(f'{pattern:08b}'[::-1], 2)
            if pattern & mask:
                return True
    return False


def shadow_channel(control, y, absolute_x):
    """Finite v30 control-domain rule, checked against every emitted floe cell."""
    if control == 0:
        return 64
    if control not in (4, 5) or 50 <= y <= 68 or absolute_x < 94:
        return 0
    return 64 if absolute_x % 32 == 30 or control == 5 and absolute_x % 32 == 31 else 0


def enemy_mask(value, distance):
    if type(value) is not int or not 0 <= value <= 255 or type(distance) is not int or not -7 <= distance <= 7:
        raise ValueError('byte pattern and signed distance -7..7 required')
    return (value << distance) & 255 if distance >= 0 else value >> -distance


def ordinary_convolve(player, enemy, y, distance, *, player_reflect=False, enemy_reflect=False):
    if len(player) != 19 or len(enemy) != 8:
        raise ValueError('complete source player and enemy glyphs required')
    footprint = []
    for dy in range(7):
        value = enemy[7 - dy]
        if enemy_reflect:
            value = int(f'{value:08b}'[::-1], 2)
        footprint.append(enemy_mask(value, distance))
    # Both seven-row contact windows use the same glyph convolution, with
    # different source-Y origins: enemy36, ice50. Visual enemy height stays8.
    return convolve(player, bytes(footprint), y + 14, reflect=player_reflect) if y else False


def literal_atoms(glyph_pages, bases):
    atoms = [[0] * 8 for _ in range(19)]
    for pose, base in enumerate(bases):
        for shift in range(19):
            for reflect in range(2):
                view = pose * 38 + shift * 2 + reflect
                for row in range(19):
                    value = glyph_pages[reflect * 256 + base + shift + row]
                    for bit in range(8):
                        if value & (128 >> bit):
                            atoms[row][bit] |= 1 << view
    return atoms


class FloeOracle:
    """Read emitted electrical bytes without consulting geometry/compiler data."""
    def __init__(self, rom, meta):
        if len(rom) != 4194304 or hashlib.sha256(rom).hexdigest() != meta['rom']['sha256']:
            raise ValueError('complete hash-bound v30 image required')
        if 'contact14' not in meta or meta['tables']['codec']['row_format'] != 'nibble':
            raise ValueError('packed uint14/nibble contact representation required')
        self.rom, self.meta = rom, meta
        self.codec = meta['tables']['codec']
        self.records = tuple(self.read_record(i) for i in range(self.codec['record_count']))

    def read(self, bank, address, size):
        if not 0 <= bank < 256 or not 0x8000 <= address < address + size <= 0xC000:
            raise ValueError('bank-local physical contact read required')
        at = bank * 16384 + address - 0x8000
        return self.rom[at:at + size]

    def pointer(self, bank, address):
        data = self.read(bank, address, 3)
        return data[2], int.from_bytes(data[:2], 'little')

    def read_record(self, ident):
        if not 0 <= ident < self.codec['record_count']:
            raise ValueError('record outside emitted pool')
        data = self.read(self.codec['record_bank'] + ident // 512,
                         0x8000 + ident % 512 * 32, 30)
        if data[28] & 240 or data[29] not in (0, 64):
            raise ValueError('invalid literal-view mask or uniform channel')
        return int.from_bytes(data[:29], 'little'), data[29]

    @lru_cache(None)
    def block(self, ident):
        if not 0 <= ident < self.codec['block_count']:
            raise ValueError('block outside emitted pool')
        data = self.read(self.codec['block_bank'] + ident // 512,
                         0x8000 + ident % 512 * 28, 28)
        values = tuple(read_field(data, i) for i in range(16))
        if any(i >= len(self.records) for i in values):
            raise ValueError('block references invalid record')
        return values

    @lru_cache(None)
    def row_at(self, bank, address):
        prefix = self.read(bank, address, 5)
        ranks = [(prefix[i // 2] >> (i % 2 * 4)) & 15 for i in range(10)]
        nonzero = [i for i in ranks if i]
        if nonzero != list(range(1, len(nonzero) + 1)):
            raise ValueError('invalid ordered nibble directory')
        refs = self.read(bank, address, 5 + len(nonzero) * 2)
        result = []
        for rank in ranks:
            if rank:
                ident = int.from_bytes(refs[5 + (rank - 1) * 2:7 + (rank - 1) * 2], 'little')
                result.extend(self.block(ident))
            else:
                result.extend([0] * 16)
        return tuple(result)

    def row(self, control, px, yi):
        if not 0 <= control < 10 or not 0 <= px < 160 or not 0 <= yi < 34:
            raise ValueError('complete emitted floe domain coordinates required')
        shadow = self.meta['contact_shadow']
        bank, address = self.pointer(shadow['bank'], shadow['root_address'] + (control * 160 + px) * 3)
        return self.row_at(*self.pointer(bank, address + yi * 3))

    def sample(self, control, px, yi, dx, view):
        if not 0 <= dx < 160 or not 0 <= view < 228:
            raise ValueError('complete relative coordinate and literal view required')
        mask, shadow = self.records[self.row(control, px, yi)[dx]]
        return 7 | shadow | (128 if mask & (1 << view) else 0)

    @lru_cache(None)
    def ordinary_row(self, directory, mode, yi):
        if not 0 <= mode < 66 or not 0 <= yi < 26 or not 0x4000 <= directory <= 0x8000 - 66 * 3:
            raise ValueError('complete resident ordinary common-profile directory required')
        at = directory - 0x4000 + mode * 3
        pointer = self.rom[at:at+3]
        bank, address = pointer[2], int.from_bytes(pointer[:2], 'little')
        return self.row_at(*self.pointer(bank, address + yi * 3))

    def ordinary_sample(self, directory, mode, yi, distance_index, view):
        if not 0 <= distance_index < 15 or not 0 <= view < 228:
            raise ValueError('ordinary signed-distance index and literal view required')
        mask, shadow = self.records[self.ordinary_row(directory, mode, yi)[distance_index]]
        return 7 | shadow | (128 if mask & (1 << view) else 0)


def build_assets(original, oracle):
    if len(original) != 4096 or hashlib.sha256(original).hexdigest() != SOURCE_SHA256:
        raise ValueError('canonical original ROM required')
    controls = control_pairs(original)
    motion = [0]
    for y in range(1, 7):
        motion.append(motion[-1] - signed_nibble(original[0xDD2 + 7 - y]))
    directory, groups = compile_footprints(controls, motion)
    glyphs = original[0xC00:0xD00]
    bases = original[0xCAA:0xCB0]
    if any(base + 36 >= 256 for base in bases):
        raise ValueError('literal glyph views cross their source page')
    reverse = bytes(int(f'{byte:08b}'[::-1], 2) for byte in glyphs)
    atoms = literal_atoms(glyphs + reverse, bases)
    shadow_directory = bytearray()
    shadow_maps = {}
    cells, interior = 0, 0
    for control in range(10):
        for yi, y in enumerate((0, *range(45, 78))):
            row0 = oracle.row(control, 0, yi)
            bitmap = bytes(sum((oracle.records[row0[n * 8 + bit]][1] >> 6) << bit
                               for bit in range(8)) for n in range(20))
            shadow_directory.append(shadow_maps.setdefault(bitmap, len(shadow_maps)))
            reference = tuple(oracle.records[i][0] for i in oracle.row(control, 80, yi))
            for dx in range(160):
                predicted = 0
                for dy, mask in enumerate(groups[directory[control * 160 + dx]]):
                    tag = y - 50 - dy
                    if 0 <= tag < 19:
                        for bit in range(8):
                            if mask & (128 >> bit):
                                predicted |= atoms[tag][bit]
                if predicted != reference[dx]:
                    raise ValueError(f'geometric contact differs at {control}/{yi}/{dx}')
            for px in range(160):
                ids = oracle.row(control, px, yi)
                for dx, ident in enumerate(ids):
                    mask, actual = oracle.records[ident]
                    fx = (px + dx) % 160
                    expected = (bitmap[fx // 8] >> (fx % 8) & 1) * 64
                    if actual != expected:
                        raise ValueError(f'non-independent shadow at {control}/{yi}/{px}/{dx}')
                    if actual != shadow_channel(control, y, fx):
                        raise ValueError(f'scalar shadow differs at {control}/{yi}/{px}/{dx}')
                    cells += 1
                    if 9 <= px <= 153:
                        if mask != reference[dx]:
                            raise ValueError(f'interior bit7 differs at {control}/{yi}/{px}/{dx}')
                        interior += 1
    assets = dict(directory=directory, footprints=b''.join(groups), glyphs=glyphs + reverse,
                  bases=bases)
    return assets, dict(complete=True, shadow_cells=cells, interior_cells=interior,
        literal_views=228, geometric_cells=10 * 34 * 160, footprint_groups=len(groups),
        scalar_shadow_cells=cells, scalar_shadow_table_bytes=0,
        reference_shadow_dictionary_bytes=len(shadow_directory) + len(shadow_maps) * 20,
        player_x_domain=[9, 153], sizes={k:len(v) for k,v in assets.items()},
        scope='Exact finite floe component only; no edge/enemy/shore, target timing or whole-game equivalence claim.')


def build_enemy_assets(original, oracle, directory):
    if len(original) != 4096 or hashlib.sha256(original).hexdigest() != SOURCE_SHA256:
        raise ValueError('canonical original ROM required')
    domain = shapes(original)
    if len(domain) != 33 or oracle.meta['tables']['profile_ys']['ordinary'] != list(range(36, 62)):
        raise ValueError('qualified ordinary shape/Y domain differs')
    glyph = original[0xC00:0xD00]
    enemy = original[0xD00:0xE00]
    reverse = lambda data: bytes(int(f'{value:08b}'[::-1], 2) for value in data)
    bases = original[0xCAA:0xCB0]
    atoms = literal_atoms(glyph + reverse(glyph), bases)
    cells = 0
    for index, shape in enumerate(domain):
        for reflect in range(2):
            page = reverse(enemy) if reflect else enemy
            mode = index * 2 + reflect
            for yi, y in enumerate(range(36, 62)):
                row = oracle.ordinary_row(directory, mode, yi)
                for xi, distance in enumerate(range(-7, 8)):
                    predicted = 0
                    for dy in range(7):
                        tag = y - 36 - dy
                        if 0 <= tag < 19:
                            mask = enemy_mask(page[shape + 7 - dy], distance)
                            for bit in range(8):
                                if mask & (128 >> bit):
                                    predicted |= atoms[tag][bit]
                    actual, shadow = oracle.records[row[xi]]
                    if predicted != actual or shadow:
                        raise ValueError(f'ordinary geometric contact differs at {mode}/{yi}/{xi}')
                    cells += 1
    assets = dict(glyphs=glyph + reverse(glyph), bases=bases,
                  enemy_glyphs=enemy + reverse(enemy), enemy_shapes=bytes(domain),
                  enemy_clip_masks=bytes(enemy_mask(255, distance) for distance in range(-7, 8)))
    return assets, dict(complete=True, geometric_cells=cells, literal_views=228,
        shape_count=33, enemy_reflections=2, source_y=[36, 61], collision_rows=7,
        visual_rows=8, player_x_domain=[25, 151],
        sizes={k:len(v) for k,v in assets.items()},
        scope='Ordinary common-profile source cells only; no edge, copy union, shore, native timing or game-integration proof.')
