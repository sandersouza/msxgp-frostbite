"""Finite declared fixtures for source scoring and complete game-phase probes.

These are controlled boundaries, never natural-play evidence. Expected score
bytes express valid BCD arithmetic; exact CPU flags/temporary RAM come from the
independent original CPU and are compared separately with the actual Z80.
"""


def bcd_score(value):
    if type(value) is not int or not 0 <= value < 1000000:
        raise ValueError('six-digit nonnegative score required')
    digits = f'{value:06d}'
    return [int(digits[i:i + 2], 16) for i in (0, 2, 4)]


def primitive_cases():
    cases = []
    saved = dict(zip(('CE', 'CF', 'D0', 'D1', 'D2', 'D3'), ('12', '34', '50', '07', '08', '0A')))
    for score in (0, 10, 90, 990, 4990, 5000, 9990, 10000, 14990, 999990):
        for reserve in (0, 1, 8, 9):
            for attract in (False, True):
                for award in (0, 1, 9, 10, 20, 90, 99):
                    updated = score if attract else (score + award) % 1000000
                    carry = score % 100 + award >= 100
                    bonus = not attract and carry and updated // 100 % 100 in (0, 50) and reserve < 9
                    before = dict(zip(('C8', 'C9', 'CA'), (f'{v:02X}' for v in bcd_score(score))))
                    after = dict(zip(('C8', 'C9', 'CA'), (f'{v:02X}' for v in bcd_score(updated))))
                    suffix = '' if award == 10 else f'-award{award}'
                    cases.append({'id': f'score-{score}-reserve{reserve}-{"attract" if attract else "active"}{suffix}',
                        'start': 'FB95', 'stops': ['FBC0'], 'limit': 10000,
                        'registers': {'a': int(f'{award:02d}', 16), 'p': 0x30},
                        'ram': {**saved, **before, 'CC': f'{reserve:02X}', 'C5': '80' if attract else '00'},
                        'expect': {'ram': {**saved, **after, 'CC': f'{reserve + int(bonus):02X}'}}})
    for level in range(256):
        cases.append({'id': f'block-level-{level:02x}', 'start': 'F5D1', 'stops': ['F5E0'],
            'registers': {}, 'ram': {'CB': f'{level:02X}', 'CD': 'FF'}, 'limit': 10000,
            'expect': {'ram': {'95': f'{min(level + 1, 9) << 4:02X}'}}})
    return cases


def validate_primitive(case, result):
    if len(result.get('ram', ())) != 128:
        raise ValueError('complete source RAM required')
    for address, value in case['expect']['ram'].items():
        if result['ram'][int(address, 16) - 128] != int(value, 16):
            raise ValueError(f'{case["id"]}: independent invariant RAM {address} differs')
    if case['start'] == 'FB95' and result['registers']['p'] & 8:
        raise ValueError('source score return must clear decimal mode')


def phase_cases(base):
    if len(base) != 128:
        raise ValueError('complete128byte base RAM required')
    result = []
    defaults = {0x80: 0, 0x81: 1, 0x82: 1, 0xC5: 0, 0xC6: 0, 0xC7: 0,
                0xCB: 0, 0xCC: 3, 0xCD: 255, 0xD2: 4, 0xE4: 27,
                0xE5: 0x45, 0xE6: 64, 0xE7: 0, 0xEA: 0, 0xF1: 0, 0xF2: 255}

    def add(name, patch):
        ram = bytearray(base)
        for address, value in {**defaults, **patch}.items():
            ram[address - 128] = value
        result.append((name, bytes(ram)))

    for level in range(256):
        for player in (0, 1):
            add(f'level-{level:02x}-p{player}', {0x80: 3, 0xC7: player, 0xCB: level, 0xF1: 8})
    for flag in (8, 16, 32, 64, 128, 24, 48, 96, 192, 255):
        add(f'dispatch-{flag:02x}', {0xF1: flag, 0xCD: 0, 0xE5: 1, 0xEB: 17, 0xF0: 17})
    for variation in range(4):
        for player in (0, 1):
            for own in (0, 1, 8, 9):
                for other in (0, 1, 8, 9):
                    add(f'recover-v{variation}-p{player}-{own}-{other}', {
                        0x80: variation, 0xC7: player, 0xCC: own, 0xD2: other, 0xF1: 32,
                        0xC8: 0x12, 0xC9: 0x34, 0xCA: 0x50, 0xCB: 2, 0xCD: 5,
                        0xCE: 0x67, 0xCF: 0x89, 0xD0: 0x10, 0xD1: 7, 0xD3: 10})
    for delay in (0, 1, 2, 127, 128, 255):
        for envelope in (0, 1, 2, 3, 4, 63, 64, 65, 91):
            add(f'bonus-delay{delay}-envelope{envelope}', {
                0xF1: 64, 0xE7: delay, 0xF4: envelope, 0xCD: 0,
                0xC8: 0x99, 0xC9: 0x99, 0xCA: 0x90, 0xCC: 8, 0xE5: 1})
    for switches in (0, 8, 64, 128, 192, 200):
        for console in range(4):
            pins = (63 ^ switches) & ~console
            add(f'console-{pins:02x}', {0x80: 3, 0x83: 0, 0xC7: 1})
    return result


def validate_phase(name, before, after):
    if len(before) != 128 or len(after) != 128:
        raise ValueError('complete before/after RAM required')
    if name.startswith('level-'):
        if after[0x4B] != (before[0x4B] + 1) % 256 or after[0x71] != 0:
            raise ValueError('uncapped byte level increment required')
        if after[0x65] != 0x45 or after[0x4D] != 255:
            raise ValueError('next level must reinitialize temperature and igloo')
    if name.startswith('recover-'):
        own, other = before[0x4C], before[0x52]
        if own == other == 0:
            if after[0x46] != 255 or after[0x71] != 0 or before[0x48:0x54] != after[0x48:0x54]:
                raise ValueError('both-empty terminal must preserve both records')
        else:
            current = bytearray(before[0x4E:0x54] if other else before[0x48:0x4E])
            current[4] -= 1
            saved = before[0x48:0x4E] if other else before[0x4E:0x54]
            if (after[0x47] != (before[0x47] ^ int(bool(other)))
                    or after[0x48:0x4E] != current or after[0x4E:0x54] != saved or after[0x71] != 0):
                raise ValueError('exact six-byte swap, living-record skip and reserve consumption required')
