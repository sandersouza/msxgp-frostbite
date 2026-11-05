"""Independent physical-reference checks for shared ice allocations."""


def constructor(build):
    from functools import lru_cache
    import hashlib
    import json
    from environment import ROOT
    from presentation_constructors import construct
    from presentation_fast_model import prepare
    from presentation_palette import audit_palette
    meta = json.loads((build/'build.json').read_text())
    rom = (build/meta['rom']['filename']).read_bytes()
    if hashlib.sha256(rom).hexdigest() != meta['rom']['sha256']:
        raise ValueError('constructor ROM identity changed')
    original = (ROOT/'references/roms/frostbite.bin').read_bytes()
    if hashlib.sha256(original).hexdigest() != meta['profile']['source_sha256']:
        raise ValueError('original authority changed')
    config = json.loads((ROOT/'references/presentation-assets-config.json').read_text())
    tables = prepare(original,audit_palette(ROOT/config['palette']),build/'geometry')
    packed = meta['template_assets']
    asset_data = b''
    for bank in packed['physical_banks']:
        data = rom[bank*16384:(bank+1)*16384]
        if hashlib.sha256(data).hexdigest() != packed['files'][f'assets-{bank:03d}.bin']:
            raise ValueError('template bank identity changed')
        asset_data += data
    section = packed['sections']['floe_patterns']
    data = asset_data[section['offset']:section['offset']+section['size']]
    if hashlib.sha256(data).hexdigest() != packed['floe_patterns_sha256']:
        raise ValueError('floe namespace changed')
    floes = [data[i:i+8] for i in range(0,len(data),8)]
    backgrounds = [{128+i:tables['background']['patterns'][b][i*8:i*8+8]+tables['background']['colors'][b][i*8:i*8+8]
                    for i in range(tables['background']['tiles_per_bank'][b])} for b in range(3)]
    @lru_cache(None)
    def tile(bank,key):
        return construct(key,patterns=tables['patterns'],floe_patterns=floes,
                         backgrounds=backgrounds[bank],header=tables['header'],footer=tables['footer']['tiles'])
    return tile


def audit_active_references(before, prepared, registers):
    if len(before) != 16384 or len(prepared) != 16384 or len(registers) != 8 or registers[2] not in (6, 7):
        raise ValueError('complete VRAM and valid NAME registers required')
    names = registers[2] * 1024
    spans = [(names, 768), (0x1b00, 128)]
    for position, identifier in enumerate(before[names:names+768]):
        bank = position // 256
        address = bank * 2048 + identifier * 8
        spans.extend(((address, 8), (0x2000 + address, 8)))
    for offset in range(0x1b00, 0x1b80, 4):
        if before[offset] == 208:
            break
        spans.append((0x3800 + (before[offset+2] & 252) * 8, 32))
    if any(before[a:a+n] != prepared[a:a+n] for a,n in spans):
        raise ValueError('displayed NAME/tile/SAT/SGT changed during preparation')


def physical(slot):
    bank = 1 + (slot >> 6)
    identifier = (19 if bank == 1 else 9) + (slot & 31) + ((slot & 32) << 1)
    return bank, identifier


def audit_pool(pool, caches, keys):
    if len(pool) != 2624 or len(caches) != 512 or len(keys) != 2304:
        raise ValueError('complete residency, decoded cache and physical metadata required')
    links, refs, colors, rows = pool[2048:2176], pool[2176:2304], pool[2304:2432], pool[2432:2560]
    expected = [0] * 128
    found = set()
    for raw_id, head in enumerate(bytes([pool[2562]])+pool[:2048]):
        chain = set()
        while head != 255:
            if head >= 128 or head in chain or head in found or not 1 <= colors[head] <= 15:
                raise ValueError('unpublished, repeated or cyclic slot in raw-ID chain')
            chain.add(head); found.add(head)
            bank, identifier = physical(head)
            group = bank + (3 if identifier & 64 else 0)
            at = (group * 64 + (identifier & 63)) * 6
            key = keys[at:at+6]
            if int.from_bytes(key[:2], 'little') != raw_id or key[4] != colors[head] or key[5] != 9:
                raise ValueError('direct head membership differs from physical metadata')
            head = links[head]
    if found != {i for i,c in enumerate(colors) if c}:
        raise ValueError('published slot absent from direct head chains')
    for owner in range(8):
        count = rows[owner*16]
        if count > 14:
            raise ValueError('row owner exceeds finite mask capacity')
        slots = list(rows[owner*16+1:owner*16+1+count])
        bank = 2 if owner % 4 < 2 else 1
        if len(set(slots)) != count or any(s not in found or physical(s)[0] != bank for s in slots):
            raise ValueError('invalid or duplicate row reference')
        for slot in slots:
            expected[slot] += 1
        if count:
            decoded = set(caches[owner*64:owner*64+60])
            dynamic = {identifier for identifier in decoded if identifier < 128}
            if dynamic != {physical(s)[1] for s in slots}:
                raise ValueError('decoded row cache differs from conservative row owners')
    if bytes(expected) != refs:
        raise ValueError('physical refcounts differ from all page/row owners')
    return dict(resident=len(found), pinned=sum(bool(n) for n in refs), references=sum(refs))
