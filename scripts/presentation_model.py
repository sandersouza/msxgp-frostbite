"""Read-only original presentation commands; no native gameplay replacement."""
from original_graphics import view as glyph


def _ram(ram):
    if not isinstance(ram, (list, bytes)) or len(ram) != 128 or any(type(v) is not int or not 0 <= v <= 255 for v in ram):
        raise ValueError('complete original uint8 RAM required')
    return lambda address: ram[address - 128]


def palette(ram):
    """Original visible-prefix selectors, computed without touching source state."""
    get = _ram(ram); level = get(0xCB); bonus = bool(get(0xC5) & 128)
    night = bonus or bool(level & 4); shore = 2 if night else 10
    door = shore
    if get(0xCD) == 15:
        door = 56 if night and not (get(0x81) ^ get(0x82)) & 8 else 0
    return {'sky': 128 if night else 132, 'shore': shore,
            'bear': shore if level < 3 else 12 if night else 4, 'door': door,
            'igloo': 6, 'water': 144}


def hud(rom, ram):
    get = _ram(ram)
    if not isinstance(rom, bytes) or len(rom) != 4096 or get(0xC7) > 6:
        raise ValueError('complete ROM and bounded original header-color table index required')
    score = [nibble * 8 for address in (0xC8, 0xC9, 0xCA) for nibble in (get(address) >> 4, get(address) & 15)]
    for index in range(5):
        if score[index]: break
        score[index] = 0x50
    temperature = get(0xE5)
    status = [(temperature & 240) >> 1 if temperature & 240 else 0x50, (temperature & 15) * 8,
              0x53, 0x50, 0x50, (get(0xCC) << 3) & 255 if get(0xCC) else 0x50]
    score_color = rom[0xFF9 + get(0xC7)] & 254
    status_color = palette(ram)['sky'] if status[0] == 0x50 and not get(0xF1) and not get(0x81) & 8 else score_color
    def commands(offsets, y, color):
        return [{'x': 22 + 8 * n, 'y': y, 'address': 0xFF00 + offset, 'width': 8, 'height': 8, 'color': color}
                for n, offset in enumerate(offsets)]
    lower = commands(status, 22, status_color)
    if get(0xCB) >= 20: lower[3]['address'] = 0xFD6D
    return {'score': commands(score, 10, score_color), 'status': lower, 'blanked': bool(get(0xBF) & 128)}


def footer(rom, ram):
    get = _ram(ram)
    if not isinstance(rom, bytes) or len(rom) != 4096: raise ValueError('complete original ROM required')
    phase = min(7, max(0, (get(0xC6) & 31) - 12)); shift = int(get(0xE8) >= 150)
    prefix = [{'x': 22 + n * 8, 'y': 189 + shift, 'width': 8, 'height': phase + 1,
               'address': 0xFF90 + n * 8, 'color': 12} for n in range(6)]
    logo = [{'x': 30 + n * 8, 'y': 191 + phase + shift, 'width': 8, 'height': 8 - phase,
             'address': 0xFF68 + n * 8 + phase, 'color': 12} for n in range(5)]
    field = [{'x': 20, 'y': 191 + phase + n + shift, 'width': 16, 'height': 1,
              'color': rom[0xFC0 + 7 - n] & 254} for n in range(8 - phase)]
    ball = [{**row, 'x': 33 - n, 'width': 8} for n, row in enumerate(field)]
    return {'phase': phase, 'prefix': prefix, 'logo': logo, 'playfield': field, 'ball': ball}


def _read(rom, address):
    if not 0xF000 <= address <= 0xFFFF: raise ValueError('source graphics read outside original ROM')
    return rom[address - 0xF000]


def player(rom, ram):
    get = _ram(ram); pose = get(0xEE)
    if pose >= 6: raise ValueError('source player pose outside proven0..5 domain')
    pattern_address = 0xFC00 | ((_read(rom, 0xFCAA + pose) + get(0xEB)) & 255)
    partial = _read(rom, 0xFCB0 + pose) + get(0xEB)
    color_address = 0xFC00 | (((partial & 255) + get(0xF0) + int(partial > 255)) & 255)
    holds = {57} | {base + n for base in (78, 90, 104, 116, 130, 142, 156, 168) for n in (2, 3)}
    rows = []; pattern = color = 0
    for y in range(47, 182):
        source_y = (get(0xE4) + 46 - y) & 255; active = source_y < 19; old = pattern; old_color = color
        if active:
            pattern = _read(rom, pattern_address + source_y); color = _read(rom, color_address + source_y) & 254
        elif y not in holds: pattern = 0
        if y == 56 and not active: color = 0
        crossings = int((pattern_address & 255) + source_y > 255) + int((color_address & 255) + source_y > 255) if active else 0
        rows.append({'y': y, 'pattern': pattern, 'color': color,
                     'prefix_pattern': old if active and y <= 54 else pattern,
                     'update_x': 16 + crossings * 3 if active and y <= 54 else 0,
                     'prefix_color': old_color if active and y == 57 else color,
                     'color_update_x': 16 + crossings * 3 if active and y == 57 else 0,
                     'suffix_x': 160, 'suffix_color': color})
    by_y = {row['y']: row for row in rows}
    tails = {77: 91, **{y: 118 for y in (78, 89, 104, 115, 130, 141, 156, 167)},
             **{y: 109 for y in (90, 116, 142, 168)}, **{y: 130 for y in (103, 129, 155)}}
    for y, cutoff in tails.items():
        source_y = (get(0xE4) + 46 - y) & 255; next_y = (source_y - 1) & 255
        if source_y < 19 and next_y < 19:
            crossings = sum(int((address & 255) + index > 255)
                            for address, index in ((pattern_address, source_y), (color_address, source_y), (color_address, next_y)))
            by_y[y]['suffix_x'] = cutoff + crossings * 3; by_y[y]['suffix_color'] = by_y[y + 1]['color']
    return {'x': get(0xE6), 'reflect': bool(get(0xEC) & 8), 'pattern_address': pattern_address,
            'color_address': color_address, 'rows': rows}


def objects(rom, ram):
    get = _ram(ram); result = []; offsets = ((0,), (0, 16), (0, 32), (0, 16, 32))
    for row in range(4):
        mode = get(0xD8 + row)
        if mode >= 4: raise ValueError('source object copy mode outside proven0..3 domain')
        for offset in offsets[mode]:
            result.append({'row': row, 'x': (get(0xD4 + row) + offset) % 160, 'y': 160 - row * 26,
                           'address': 0xFD00 + get(0xA3 + row), 'width': 8, 'height': 8,
                           'reflect': bool(get(0x91 + row) & 128), 'color': get(0xA7 + row) & 254})
    return result


def _signed_nibble(value):
    value = (value >> 4) & 15
    return value if value < 8 else value - 16


def floes(rom, ram):
    get = _ram(ram); result = []; motion = 0
    if get(0x9D) & 2: raise ValueError('locked missile outside observed floe-control domain')
    displacements = [0]
    for y in range(1, 7):
        motion -= _signed_nibble(_read(rom, 0xFDD2 + 7 - y)); displacements.append(motion)
    for row in range(4):
        for dy, displacement in enumerate(displacements):
            for copy in (0, 32, 64):
                for plane in (-_signed_nibble(get(0x9C)), 4 - _signed_nibble(get(0x9D))):
                    result.append({'row': row, 'x': (get(0x9F + row) + copy + plane + displacement) % 160,
                                   'y': 174 - 26 * row + dy, 'width': 8, 'height': 1, 'color': get(0xAB + row) & 254})
    return result


def background_rows(rom, ram):
    get = _ram(ram); colors = palette(ram); result = [0] * 210
    result[7:33] = [colors['sky']] * 26; result[42:77] = [colors['shore']] * 35; result[78:185] = [colors['water']] * 107
    rng = get(0x82)
    for row in range(9):
        result[33 + row] = (_read(rom, 0xFCBF - row) ^ (rng & 2)) & 254
        rng = ((rng << 1) | (rng >> 7)) & 255
    return result


def igloo(ram):
    get = _ram(ram)
    return [{'x': 112 + 4 * bit, 'y': 51 - level * 4, 'width': 4, 'height': 4, 'color': 6}
            for level in range(5) for bit in range(8) if get(0xC0 + level) & (1 << bit)]


def describe(rom, state, layout=0, width=0):
    if not isinstance(rom, bytes) or len(rom) != 4096 or layout not in (0, 1) or width not in (0, 1):
        raise ValueError('complete original ROM and declared diagnostic view required')
    ram = state['ram']; get = _ram(ram)
    if get(0xEF) >= 8 or any(get(address) >= 160 for address in (0xE6, 0xE8, *range(0x9F, 0xA3), *range(0xD4, 0xD8))):
        raise ValueError('source actor coordinates/pose outside observed domain')
    colors = palette(ram)
    bear = {'x': (get(0xE8) + (6 if get(0xE8) < 15 else 1)) % 160, 'y': 58,
            'address': 0xFD00 + _read(rom, 0xFEE7 + get(0xEF)), 'height': 19,
            'width': 16, 'scale': 2, 'reflect': bool(get(0xEC) & 16), 'color': colors['bear']}
    door = [] if get(0xCD) != 15 else [{'x': 123, 'y': 43, 'address': 0xFEF3, 'height': 12,
                                      'width': 8, 'reflect': bool(get(0xEC) & 16), 'color': colors['door']}]
    return {'target_view': {'layout': layout, 'width': width}, 'hud': hud(rom, ram),
            'background': background_rows(rom, ram), 'igloo': igloo(ram), 'door': door,
            'bear': bear, 'objects': objects(rom, ram), 'floes': floes(rom, ram),
            'player': player(rom, ram), 'coarse_shift': int(get(0xE8) >= 150), 'footer': footer(rom, ram)}


def pixels(rom, description):
    """General original-space compositor. Target adaptation is a separate stage."""
    result = bytearray(160 * 210)
    if description['hud']['blanked']: return bytes(result)
    for y, color in enumerate(description['background']): result[y * 160 + 8:(y + 1) * 160] = bytes([color]) * 152
    def pixel(x, y, color):
        x %= 160
        if 8 <= x < 160 and 0 <= y < 210: result[y * 160 + x] = color
    def solid(rect):
        for dy in range(rect['height']):
            for dx in range(rect['width']): pixel(rect['x'] + dx, rect['y'] + dy, rect['color'])
    def draw(command):
        image = glyph(rom, command['address'], command['height'], command.get('reflect', False), command.get('scale', 1))
        for i, bit in enumerate(image['pixels']):
            if bit: pixel(command['x'] + i % image['width'], command['y'] + i // image['width'], command['color'])
    for command in description['hud']['score'] + description['hud']['status']: draw(command)
    for rect in description['igloo']: solid(rect)
    for command in description['door']: draw(command)
    draw(description['bear'])
    # VDELP1 retains the final bear byte through the separator scanline.
    draw({**description['bear'], 'y': 77, 'height': 1})
    for command in description['objects']: draw(command)
    for rect in description['floes']: solid(rect)
    person = description['player']
    for row in person['rows']:
        for dx in range(8):
            x = (person['x'] + dx) % 160; bit = dx if person['reflect'] else 7 - dx
            pattern = row['prefix_pattern'] if x < row['update_x'] else row['pattern']
            color = row['prefix_color'] if x < row['color_update_x'] else row['color']
            if x >= row['suffix_x']: color = row['suffix_color']
            if pattern & (1 << bit): pixel(x, row['y'], color)
    if description['coarse_shift']:
        result[57 * 160:] = result[56 * 160:209 * 160]
        # The overrun has no HMOVE strobe, so its first8 pixels are not blanked.
        result[57 * 160:57 * 160 + 8] = bytes([description['background'][56]]) * 8
        held = next(row for row in person['rows'] if row['y'] == 56)
        for dx in range(8):
            x = (person['x'] + dx) % 160; bit = dx if person['reflect'] else 7 - dx
            if x < 8 and held['pattern'] & (1 << bit): result[57 * 160 + x] = held['color']
    decoration = description['footer']
    for command in decoration['prefix']: draw(command)
    for rect in decoration['playfield'] + decoration['ball']: solid(rect)
    for command in decoration['logo']: draw(command)
    return bytes(result)
