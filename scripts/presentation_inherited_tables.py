"""Generate I ready packets from canonical F and audit all reclaimed storage.

No ROM-derived tables are source inputs. Live-domain bytes, phase.inc and packet
images are generated only inside the caller's fresh ignored output directory.
Allocation order is part of the sealed I binary contract, including bank150's
last partial contact-block bank.
"""
import json

from presentation_static_assets import expand_pair
from render_build import symbols


def generate(base, out, original):
    s = symbols(base / 'presentation.sym')
    def rd(bank, address, size):
        at = bank * 16384 + address - 0x8000
        return original[at:at+size]
    def logical(address, size):
        bank = address // 16384
        return rd(bank+3 if bank < 11 else bank+242, 0x8000+address % 16384, size)
    patterns, families, halves = set(), {}, set()
    for family, count, variants in [('row', 66, 128), ('bear', 16, 32)]:
        ids = set()
        roots = rd(1, s['p_geo_'+family+'_roots_data'], count*3)
        for g in range(count):
            address = int.from_bytes(roots[g*3:g*3+2], 'little')
            bank = roots[g*3+2]
            table = rd(bank, address, variants*2)
            for v in range(variants):
                code = int.from_bytes(table[v*2:v*2+2], 'little')
                cl = rd(1, s['p_geo_classes_data']+(code >> 12)*8, 8)
                stride = cl[2]
                offset = int.from_bytes(cl[5:8], 'little')+(code & 4095)*stride
                data = logical(offset, stride)
                ids.update(int.from_bytes(data[i:i+2], 'little') for i in range(0, stride, 2))
        patterns |= ids
        families[family] = len(ids)
    for pattern in patterns:
        data = logical(pattern*4, 4)
        halves.update(int.from_bytes(data[j:j+2], 'little') for j in (0, 2))
    unused = []
    for offset, used, total in [(0, patterns, s['p_template_pattern_count']),
                               (s['p_template_pattern_halves_offset'], halves, s['p_template_half_count'])]:
        for index in range(total):
            if index in used:
                continue
            address = offset+index*4
            bank = address // 16384
            physical = bank+3 if bank < 11 else bank+242
            cpu = 0x8000+address % 16384
            if unused and unused[-1][0] == physical and unused[-1][2] == cpu:
                unused[-1][2] += 4
            else:
                unused.append([physical, cpu, cpu+4])
    live_meta = dict(live_patterns=sorted(patterns), live_halves=sorted(halves), families=families,
                     unused_regions=unused, unused_bytes=sum(b-a for _, a, b in unused),
                     live_pattern_bytes_preserved={str(i): logical(i*4, 4).hex() for i in sorted(patterns)})
    (out / 'live-domain.json').write_text(json.dumps(live_meta, indent=2)+'\n')

    tables = json.loads((base / 'tables/tables.json').read_text())
    codec = tables['codec']
    live, ends = set(), {}
    def read(pointer, size):
        address = int.from_bytes(pointer[:2], 'little')
        bank = pointer[2]
        if not (14 <= bank <= 252 and 0x8000 <= address and address+size <= 0xC000):
            raise ValueError('contact pointer outside certified arena')
        ends[bank] = max(ends.get(bank, 0x8000), address+size)
        return rd(bank, address, size)
    def row(pointer):
        if pointer in live:
            return
        live.add(pointer)
        prefix = read(pointer, 5)
        count = sum(bool(x >> shift & 15) for x in prefix for shift in (0, 4))
        read(pointer, 5+2*count)
    def profile(pointer, ys):
        data = read(pointer, ys*3)
        for index in range(0, len(data), 3):
            row(data[index:index+3])
    for kind in ('edge', 'ordinary', 'shore'):
        roots = (base / f'tables/{kind}-modes.bin').read_bytes()
        players = len(tables['banked_player_directories'][kind])
        ys = len(tables['profile_ys'][kind])
        for index in range(0, len(roots), 3):
            data = read(roots[index:index+3], players*3)
            for j in range(0, len(data), 3):
                profile(data[j:j+3], ys)
    for name, ys in (('ordinary-common', len(tables['profile_ys']['ordinary'])),
                     ('floe-roots', len(tables['profile_ys']['floe']))):
        roots = (base / f'tables/{name}.bin').read_bytes()
        for index in range(0, len(roots), 3):
            profile(roots[index:index+3], ys)
    if len(live) != tables['unique_rows']:
        raise ValueError('incomplete contact graph traversal')
    regions = [(252, ends[252], 0xC000),
               (150, 0x8000+(codec['block_count'] % 512)*32, 0xC000),
               (34, 0x8000+(codec['record_count'] % 512)*32, 0xC000),
               (2, 0xC000-518, 0xC000)]
    for bank, start, end in regions:
        if set(rd(bank, start, end-start)) != {255}:
            raise ValueError('certified ROM padding is not blank')
    regions.extend(tuple(x) for x in unused)
    positions = [a for _, a, _ in regions]
    allocations = []
    rom = bytearray(original)
    def put(data):
        for index, (bank, start, end) in enumerate(regions):
            position = positions[index]
            if position+len(data) > end:
                continue
            at = bank*16384+position-0x8000
            rom[at:at+len(data)] = data
            positions[index] += len(data)
            allocations.append([bank, position, len(data)])
            return bank, position
        raise ValueError('ROM padding exhausted')
    index_location = put(bytes(66*16*3))
    mapping = rd(1, s['p_geo_row_map_data'], 256)
    roots = {value: key for key, value in enumerate(mapping) if value < 33}
    indices, packets = bytearray(), {}
    for group in range(33):
        pointer = roots[group]
        for reverse in range(2):
            for phase in range(16):
                data = bytearray(24)
                for y, mask in enumerate(rd(2, 0xA500+pointer, 8)[::-1]):
                    if reverse:
                        mask = int(f'{mask:08b}'[::-1], 2)
                    bits = (int.from_bytes(expand_pair(mask, phase & 1), 'big') << 8) >> ((phase*3//2) & 7)
                    for col in range(3):
                        data[col*8+y] = (bits >> (16-col*8)) & 255
                if not any(data[16:]):
                    data = data[:16]
                data = bytes(data)
                if data not in packets:
                    packets[data] = put(data)
                bank, address = packets[data]
                if address & 1:
                    raise ValueError('unaligned ready packet')
                indices.extend((address | int(len(data) == 16)).to_bytes(2, 'little')+bytes([bank]))
    bank, address = index_location
    at = bank*16384+address-0x8000
    rom[at:at+len(indices)] = indices
    (out / 'phase.inc').write_text(f'i_packets_bank EQU {bank}\ni_packets EQU ${address:04X}\n')
    allocation = dict(packet_index=index_location, allocations=allocations, regions=regions,
                      contact_nodes_checked=len(live), used_bytes=sum(x[2] for x in allocations),
                      reclaimed_pattern_slots=len(unused), unique_packets=len(packets),
                      packet_payload_bytes=sum(map(len, packets)))
    (out / 'tables.json').write_text(json.dumps(allocation, indent=2)+'\n')
    (out / 'tables.rom').write_bytes(rom)
    return rom, allocation
