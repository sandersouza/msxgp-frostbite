"""Finite geometry tables for native dirty-band rendering, never frame playback."""
import hashlib
import json
from pathlib import Path

from graphics_mapping import palette_map
from original_graphics import catalog, view
from presentation_model import background_rows
from reference_traces import private_output

GEOMETRY_BANKS = tuple(range(3, 14)) + (253, 254, 255)


class BankImage:
    """Pack small records within bank windows; streams use logical bank order."""
    def __init__(self, banks):
        if not banks or len(set(banks)) != len(banks) or any(type(bank) is not int or not 0 <= bank <= 255 for bank in banks):
            raise ValueError('nonempty unique physical bank list required')
        self.banks = list(banks); self.data = bytearray()

    @property
    def used_bytes(self): return len(self.data)

    def store(self, data, *, record=True, alignment=1):
        if (not isinstance(data, (bytes, bytearray)) or not data or type(alignment) is not int
                or not 1 <= alignment <= 16384 or alignment & (alignment - 1)
                or record and len(data) > 16384):
            raise ValueError('bounded nonempty binary record and power-of-two alignment required')
        start = (len(self.data) + alignment - 1) & -alignment
        if record and start % 16384 + len(data) > 16384: start = (start + 16383) & -16384
        if start + len(data) > len(self.banks) * 16384: raise ValueError('finite geometry exceeds available cartridge banks')
        pointer = (0x8000 + start % 16384).to_bytes(2, 'little') + bytes((self.banks[start // 16384],))
        self.data.extend(bytes([255]) * (start - len(self.data))); self.data.extend(data)
        return pointer

    def images(self):
        return [bytes(self.data[start:start + 16384]).ljust(16384, b'\xff') for start in range(0, len(self.data), 16384)]


def mask_tiles(bitmap, width, height, phase_x, phase_y):
    """Expand a source mask into reusable eight-row SCREEN2 pattern fragments."""
    if (type(width) is not int or type(height) is not int or not 1 <= width <= 32 or not 1 <= height <= 32
            or type(phase_x) is not int or not 0 <= phase_x < 16 or type(phase_y) is not int or not 0 <= phase_y < 8
            or len(bitmap) != width * height or any(value not in (0, 1) for value in bitmap)):
        raise ValueError('bounded binary source mask and explicit horizontal/vertical phase required')
    start = 8 + phase_x * 3 // 2; origin = start & ~7
    columns = (8 + (phase_x + width) * 3 // 2 - origin + 7) // 8
    rows = (phase_y + height + 7) // 8; patterns = [bytearray(8) for _ in range(columns * rows)]
    for y in range(height):
        target_y = phase_y + y
        for x in range(width):
            if bitmap[y * width + x]:
                for target_x in range(8 + (phase_x + x) * 3 // 2 - origin, 8 + (phase_x + x + 1) * 3 // 2 - origin):
                    patterns[(target_y // 8) * columns + target_x // 8][target_y % 8] |= 128 >> (target_x % 8)
    return {'columns': columns, 'rows': rows, 'patterns': [bytes(pattern) for pattern in patterns]}


def pack_descriptors(records, image):
    """Lossless fixed-grid classes:4-bit class plus12-bit record index.

    Pattern-ID arrays have fixed strides within each class, eliminating an
    address/bank pointer for every horizontal/vertical variant. Large classes
    split at4096 records. Individual uint16 pattern IDs stay word-aligned.
    """
    by_grid = {}
    for record in records:
        columns, rows = record['columns'], record['rows']; patterns = tuple(record['patterns'])
        if (type(columns) is not int or type(rows) is not int or not 1 <= columns <= 8 or not 1 <= rows <= 5
                or len(patterns) != columns * rows or any(type(value) is not int or not 0 <= value <= 65535 for value in patterns)):
            raise ValueError('bounded descriptor grid and uint16 pattern IDs required')
        by_grid.setdefault((columns, rows), set()).add(patterns)
    plans = []
    for grid in sorted(by_grid):
        ordered = sorted(by_grid[grid])
        for start in range(0, len(ordered), 4096): plans.append((grid, ordered[start:start + 4096]))
    if len(plans) > 16: raise ValueError('descriptor domain exceeds16 fixed-grid classes')
    classes = []; codes = {}
    for kind, ((columns, rows), block) in enumerate(plans):
        offset = (image.used_bytes + 1) & ~1
        raw = b''.join(value.to_bytes(2, 'little') for record in block for value in record)
        pointer = image.store(raw, record=False, alignment=2)
        classes.append({'columns': columns, 'rows': rows, 'stride': columns * rows * 2,
                        'count': len(block), 'offset': offset, 'pointer': list(pointer)})
        for index, pattern_ids in enumerate(block): codes[(columns, rows, pattern_ids)] = (kind << 12) | index
    return {'classes': classes, 'ids': [codes[(record['columns'], record['rows'], tuple(record['patterns']))] for record in records]}


def compile_geometry(rom, out):
    """Compile every declared primitive phase and reopen/decode all records."""
    source = catalog(rom); out = private_output(out); out.mkdir(parents=True, exist_ok=False)
    patterns = [bytes(8), bytes([255]) * 8]; indices = {value: index for index, value in enumerate(patterns)}
    records = []; groups = {'row': [], 'floe': [], 'bear': []}
    def add(bitmap, width, height, x, y):
        compiled = mask_tiles(bitmap, width, height, x, y); ids = []
        for pattern in compiled['patterns']:
            if pattern not in indices: indices[pattern] = len(patterns); patterns.append(pattern)
            ids.append(indices[pattern])
        index = len(records); records.append({'columns': compiled['columns'], 'rows': compiled['rows'], 'patterns': tuple(ids)})
        return index
    pointers = sorted({0} | {item['range'][0] - 0xFD00 for name, item in source['assets'].items() if name.startswith('row-')})
    for pointer in pointers:
        for reflect in (False, True):
            glyph = view(rom, 0xFD00 + pointer, 8, reflect)
            groups['row'].append([add(glyph['pixels'], 8, 8, x, y) for x in range(16) for y in range(8)])
    shifts = [0]
    for y in range(1, 7):
        nibble = rom[0xDD2 + 7 - y] >> 4; signed = nibble if nibble < 8 else nibble - 16
        shifts.append(shifts[-1] - signed)
    if min(shifts) != -8 or max(shifts) != 0: raise ValueError('original floe geometry outside reviewed displacement domain')
    for width in range(8, 17):
        bitmap = bytearray((width + 8) * 7)
        for y, delta in enumerate(shifts): bitmap[y * (width + 8) + 8 + delta:y * (width + 8) + 8 + delta + width] = bytes([1]) * width
        groups['floe'].append([add(bitmap, width + 8, 7, x, y) for x in range(16) for y in range(8)])
    for pose in range(8):
        for reflect in (False, True):
            glyph = view(rom, 0xFD00 + rom[0xEE7 + pose], 19, reflect, 2)
            bitmap = glyph['pixels'] + glyph['pixels'][-16:]
            groups['bear'].append([add(bitmap, 16, 20, x, y) for x in range(16) for y in (3, 4)])
    image = BankImage(GEOMETRY_BANKS); image.store(b''.join(patterns), record=False, alignment=8)
    encoded = pack_descriptors(records, image); directories = {}; roots = {}
    for family, cases in groups.items():
        roots[family] = []
        for group in cases:
            raw = b''.join(encoded['ids'][index].to_bytes(2, 'little') for index in group)
            if raw not in directories: directories[raw] = image.store(raw, alignment=2)
            roots[family].append(list(directories[raw]))
    files = {}
    for bank, data in zip(GEOMETRY_BANKS, image.images()):
        path = out / f'geometry-{bank:03d}.bin'; path.write_bytes(data); files[path.name] = hashlib.sha256(data).hexdigest()
    actual = bytearray()
    for bank in GEOMETRY_BANKS[:len(image.images())]:
        path = out / f'geometry-{bank:03d}.bin'; raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != files[path.name]: raise ValueError('changed generated geometry bank')
        actual.extend(raw)
    if actual[:len(patterns) * 8] != b''.join(patterns): raise ValueError('persisted pattern atlas differs')
    verified = 0
    for family, cases in groups.items():
        for root, group in zip(roots[family], cases):
            position = GEOMETRY_BANKS.index(root[2]) * 16384 + int.from_bytes(bytes(root[:2]), 'little') - 0x8000
            if position % 16384 + len(group) * 2 > 16384: raise ValueError('geometry directory crosses mapper window')
            for number, index in enumerate(group):
                code = int.from_bytes(actual[position + number * 2:position + number * 2 + 2], 'little'); kind, local = code >> 12, code & 4095
                if kind >= len(encoded['classes']): raise ValueError('invalid persisted geometry class')
                cls = encoded['classes'][kind]
                if local >= cls['count']: raise ValueError('invalid persisted geometry record')
                start = cls['offset'] + local * cls['stride']; raw = actual[start:start + cls['stride']]
                recovered = tuple(int.from_bytes(raw[n:n + 2], 'little') for n in range(0, len(raw), 2))
                expected = records[index]
                if (cls['columns'], cls['rows'], recovered) != (expected['columns'], expected['rows'], expected['patterns']):
                    raise ValueError('persisted geometry differs from finite primitive constructor')
                verified += 1
    pointer_map = bytes(pointers.index(value) if value in pointers else 255 for value in range(256))
    (out / 'row-pointer-map.bin').write_bytes(pointer_map)
    result = {'schema_version': 1, 'source_sha256': hashlib.sha256(rom).hexdigest(), 'patterns': len(patterns),
              'pattern_bytes': len(patterns) * 8, 'descriptor_count': len(records), 'verified_descriptors': verified,
              'classes': encoded['classes'], 'used_bytes': image.used_bytes, 'banks_used': len(image.images()),
              'physical_banks': list(GEOMETRY_BANKS[:len(image.images())]), 'roots': roots, 'files': files,
              'row_pointer_map_sha256': hashlib.sha256(pointer_map).hexdigest(),
              'scope': 'Finite source primitive geometry and record readback only; not live target pixels or timing'}
    (out / 'geometry.json').write_text(json.dumps(result, indent=2) + '\n'); return result


def background_tables(rom, measured_palette):
    """Static background tiles and compact row programs, outside dynamic IDs.

    Seven SAT entries share one four-pixel black mask. This restores the exact
    source HMOVE border after background primitives use two-color edge tiles.
    The extra coarse scanline at source57 lies outside those rectangles.
    """
    if len(rom) != 4096 or set(measured_palette) != set(range(0, 256, 2)):
        raise ValueError('complete ROM and measured128-code palette required')
    colors = palette_map(measured_palette); gradients = []; representatives = {}
    for rng in range(256):
        ram = [0] * 128; ram[2] = rng
        gradient = tuple(colors[value] for value in background_rows(rom, ram)[33:42])
        gradients.append(gradient); representatives.setdefault(gradient, rng)
    options = sorted(representatives); indices = {gradient: index for index, gradient in enumerate(options)}
    patterns = [[bytes([255]) * 8] for _ in range(3)]; palettes = [[bytes([17]) * 8] for _ in range(3)]
    keys = [{(patterns[bank][0], palettes[bank][0]): 128} for bank in range(3)]
    def intern(bank, pattern, color):
        key = (bytes(pattern), bytes(color))
        if key not in keys[bank]:
            if len(patterns[bank]) >= 128: raise ValueError('static background exceeds128 reserved tile IDs per bank')
            keys[bank][key] = 128 + len(patterns[bank]); patterns[bank].append(key[0]); palettes[bank].append(key[1])
        return keys[bank][key]
    records = []
    for gradient in options:
        for coarse in (0, 1):
            for night in (0, 1):
                ram = [0] * 128; ram[2] = representatives[gradient]; ram[0x4B] = 7 if night else 3
                raw = background_rows(rom, ram)
                if coarse: raw[57:] = raw[56:209]
                rows = [colors[raw[y + (7 if y < 179 else 10)]] for y in range(192)]
                record = bytearray()
                for tile_row in range(24):
                    bank = tile_row // 8; values = rows[tile_row * 8:tile_row * 8 + 8]
                    first = [rows[y] if coarse and y == 50 else 1 for y in range(tile_row * 8, tile_row * 8 + 8)]
                    edge_pattern = [255 if 64 <= y < 176 or coarse and y == 50 or rows[y] == 1 else 15 for y in range(tile_row * 8, tile_row * 8 + 8)]
                    record.extend((intern(bank, bytes([255]) * 8, bytes(value * 17 for value in first)),
                                   intern(bank, edge_pattern, bytes(value * 17 if mask == 255 else value * 16 + 1 for value, mask in zip(values, edge_pattern))),
                                   intern(bank, bytes([255]) * 8, bytes(value * 17 for value in values))))
                records.append(bytes(record))
    gradient_rows = b''.join(records[index * 4 + night][10:12] for index in range(len(options)) for night in (0, 1))
    return {'patterns': [b''.join(bank) for bank in patterns], 'colors': [b''.join(bank) for bank in palettes],
            'tiles_per_bank': [len(bank) for bank in patterns], 'base_rows': b''.join(records[:4]),
            'gradient_rows': gradient_rows, 'rng_index': bytes(indices[gradient] for gradient in gradients),
            'profiles': records, 'gradient_profiles': len(options), 'black_sprite': bytes([240]) * 16 + bytes(16)}


def pack_background(primitive_bank, used_bytes, tables,*,black_sprite_address=0x3C00):
    """Append small background programs into unused space of the primitive bank."""
    if len(primitive_bank) != 16384 or type(used_bytes) is not int or not 0 < used_bytes <= 16384:
        raise ValueError('complete primitive bank and bounded used prefix required')
    if type(black_sprite_address)is not int or black_sprite_address not in (0x3C00,0x3FE0):raise ValueError('declared immutable sprite slot required')
    bank = bytearray(primitive_bank); position = used_bytes; sections = {}
    def add(name, data, alignment=1):
        nonlocal position
        start = (position + alignment - 1) & -alignment; end = start + len(data)
        if end > 16384 or any(value != 255 for value in bank[position:end]): raise ValueError('background does not fit unused primitive bank tail')
        bank[start:end] = data; sections[name] = {'offset': start, 'size': len(data)}; position = end
    add('rng', tables['rng_index'], 256); add('rows', tables['base_rows']); add('gradient', tables['gradient_rows'])
    for index in range(3):
        add(f'patterns{index}', tables['patterns'][index]); add(f'colors{index}', tables['colors'][index])
    add('black_sprite', tables['black_sprite'])
    assembly = ''.join(f'p_bg_{name}_data EQU ${0x8000 + section["offset"]:04X}\n' for name, section in sections.items())
    initializers = ['p_bg_upload_static:']
    for name, destination in [(f'patterns{i}', 0x4400 + i * 2048) for i in range(3)] + [(f'colors{i}', 0x6400 + i * 2048) for i in range(3)] + [('black_sprite', 0x4000+black_sprite_address)]:
        length = sections[name]['size']; initializers += [f'    LD HL,p_bg_{name}_data', f'    LD DE,${destination:04X}']
        first = True
        while length:
            amount = min(256, length); initializers += [f'    LD B,{amount % 256}', '    CALL vdp_write' if first else '    CALL vdp_stream']
            first = False; length -= amount
    initializers += ['    RET']
    return {'bank': bytes(bank), 'used_bytes': position, 'sections': sections, 'assembly': assembly, 'initializers': '\n'.join(initializers) + '\n'}


def background_vram(tables, ram):
    """Host expectation for the background component, not full-source acceptance."""
    if len(ram) != 128 or any(type(value) is not int or not 0 <= value <= 255 for value in ram): raise ValueError('complete uint8 canonical RAM required')
    vram = bytearray(16384)
    for bank in range(3):
        data = tables['patterns'][bank]; vram[bank * 2048 + 1024:bank * 2048 + 1024 + len(data)] = data
        data = tables['colors'][bank]; vram[0x2400 + bank * 2048:0x2400 + bank * 2048 + len(data)] = data
    if ram[0x3F] & 128:
        vram[0x1800:0x1B00] = bytes([128]) * 768; vram[0x1B00] = 208
    else:
        night = int(bool(ram[0x45] & 128 or ram[0x4B] & 4)); coarse = int(ram[0x68] >= 150)
        rows = bytearray(tables['base_rows'][(coarse * 2 + night) * 72:(coarse * 2 + night + 1) * 72])
        offset = (tables['rng_index'][ram[2]] * 2 + night) * 2
        rows[10:12] = tables['gradient_rows'][offset:offset + 2]
        for row in range(24):
            first, edge, middle = rows[row * 3:row * 3 + 3]
            vram[0x1800 + row * 32:0x1820 + row * 32] = bytes((128, first, edge)) + bytes([middle]) * 28 + bytes((128,))
        vram[0x3C00:0x3C20] = tables['black_sprite']
        for index, y in enumerate(range(64, 176, 16)): vram[0x1B00 + index * 4:0x1B04 + index * 4] = bytes((y - 1, 16, 128, 1))
        vram[0x1B1C] = 208
    return bytes(vram)


def pack_geometry_metadata(boot, geometry, pointer_map):
    """Append relocated lookup roots to the unused boot bank, without overlap."""
    if len(boot['bank']) != 16384 or len(pointer_map) != 256:
        raise ValueError('complete boot bank and256-byte pointer map required')
    position = (boot['used_bytes'] + 255) & -256
    data = bytearray(pointer_map); sections = {'row_map':position}
    for family in ('row', 'floe', 'bear'):
        sections[f'{family}_roots'] = position + len(data)
        data.extend(bytes(byte for root in geometry['roots'][family] for byte in root))
    sections['classes'] = position + len(data)
    for cls in geometry['classes']:
        data.extend(bytes((cls['columns'],cls['rows'],cls['stride'])) + cls['count'].to_bytes(2,'little') + cls['offset'].to_bytes(3,'little'))
    end = position + len(data)
    if end > 16384 or any(value != 255 for value in boot['bank'][boot['used_bytes']:end]):
        raise ValueError('geometry metadata exceeds unused boot bank tail')
    bank = bytearray(boot['bank']); bank[position:end] = data
    assembly = ''.join(f'p_geo_{name}_data EQU ${0x8000+offset:04X}\n' for name,offset in sections.items())
    assembly += f'p_geo_class_count EQU {len(geometry["classes"])}\np_geo_pattern_count EQU {geometry["patterns"]}\n'
    return {'bank':bytes(bank),'used_bytes':end,'sections':sections,'assembly':assembly}
