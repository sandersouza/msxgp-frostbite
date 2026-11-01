"""Guarded finite lowering of pure ROM-indexed RAM-write loops.

Recognize instructions, never game rules or a hard-coded source address. Only
X=0 and a bounded positive loop count use the summary. Every indexed read must
remain in approved source ROM data; every store must be canonical RAM and must
not overwrite the loop bound. Other entries execute the unchanged native body.
Generated effect tables are original-derived and remain local/ignored.
"""
import hashlib

from native_analysis import analyze
from native_codegen import mapped, reachable
from native_shifts import generate as generate_base


def find_loops(instructions):
    wanted = (('LDY', 'abx'), ('LDA', 'abx'), ('STA', 'aby'), ('CPX', 'zpg'),
              ('BCS', 'rel'), ('INX', 'imp'), ('BPL', 'rel'))
    result = []
    for start in sorted(instructions):
        pc = start; chain = []
        for op, mode in wanted:
            item = instructions.get(pc)
            if item is None or (item['mnemonic'], item['mode']) != (op, mode): break
            chain.append(item); pc += item['size']
        if (len(chain) == 7 and chain[4]['target'] == pc and chain[6]['target'] == start):
            result.append({'start': start, 'end': pc, 'load_y': chain[0]['value'],
                           'load_a': chain[1]['value'], 'destination': chain[2]['value'], 'bound': chain[3]['value']})
    return result


def ram_offset(address):
    try: address = mapped(address & 65535, True)
    except ValueError: return None
    if address.startswith('$'):
        value = int(address[1:], 16)
        if 0xC000 <= value < 0xC080: return value - 0xC000
    return None


def rom_byte(rom, address):
    if not 0 <= address <= 65535: return None
    try: target = mapped(address)
    except ValueError: return None
    return rom[address & 4095] if target.startswith('original_data+') else None


def summarize(rom, loop):
    bound = ram_offset(loop['bound'])
    if len(rom) != 4096 or bound is None: return None
    rows, writes, destinations = [], {}, set()
    for index in range(128):
        y = rom_byte(rom, loop['load_y'] + index); a = rom_byte(rom, loop['load_a'] + index)
        if y is None or a is None: break
        destination = ram_offset(loop['destination'] + y)
        if destination is None or destination == bound or len(destinations | {destination}) > 8: break
        destinations.add(destination); writes[destination] = a
        rows.append({'a': a, 'y': y, 'writes': dict(writes)})
    if not rows: return None
    return {**loop, 'bound_offset': bound, 'limit': len(rows), 'destinations': sorted(destinations), 'rows': rows}


def table_columns(summary):
    rows = summary['rows']; addresses = summary['destinations']
    result = {'mask': [sum(1 << i for i, a in enumerate(addresses) if a in row['writes']) for row in rows],
              'a': [row['a'] for row in rows], 'y': [row['y'] for row in rows]}
    result.update({f'cell{i}': [row['writes'].get(a, 0) for row in rows] for i, a in enumerate(addresses)})
    return {name: bytes(values) + bytes(256 - len(values)) for name, values in result.items()}


def emit_summary(summary, prefix, end_label, slow_label):
    # Balanced native AF save also makes every rejected guard leave the old
    # source A/N/Z and all other canonical CPU/RAM values untouched.
    lines = ['push af', 'ld a,b', 'or a', f'jp nz,{slow_label}',
             f'ld a,(${0xC000 + summary["bound_offset"]:04X})',
             f'cp {summary["limit"]}', f'jp nc,{slow_label}']
    lines += ['ld b,a', 'ld l,a', 'pop af', f'ld h,{prefix}_mask/256', 'ld d,(hl)']
    for i, address in enumerate(summary['destinations']):
        lines += [f'bit {i},d', f'jr z,{prefix}_skip{i}_{slow_label}',
                  f'ld h,{prefix}_cell{i}/256', 'ld a,(hl)', f'ld (${0xC000 + address:04X}),a',
                  f'{prefix}_skip{i}_{slow_label}:']
    lines += [f'ld h,{prefix}_y/256', 'ld c,(hl)', f'ld h,{prefix}_a/256', 'ld a,(hl)',
              'ld l,b', 'ld h,$C0', 'push hl', 'pop iy', 'ld e,1', 'cp a', f'jp {end_label}',
              slow_label + ':', 'pop af']
    return lines


def emit_tables(summary, prefix):
    result = []
    for name, values in table_columns(summary).items():
        result += ['    ALIGN 256', f'{prefix}_{name}:']
        for offset in range(0, 256, 16):
            result.append('    DB ' + ','.join(f'${v:02X}' for v in values[offset:offset + 16]))
    return '\n'.join(result) + '\n'


def summaries(rom):
    return [s for loop in find_loops(reachable(rom)) if (s := summarize(rom, loop)) is not None]


def manifest(rom):
    return [{'start': f'{s["start"]:04X}', 'end': f'{s["end"]:04X}', 'entry_x': 0,
             'bound': f'{s["bound"]:02X}', 'fast_bound_values': [0, s['limit'] - 1],
             'ram_destinations': [f'{a + 128:02X}' for a in s['destinations']],
             'table_sha256': {k: hashlib.sha256(v).hexdigest() for k, v in table_columns(s).items()},
             'fallback': 'Every other entry uses the original native instruction body'} for s in summaries(rom)]


def generate(rom, carry_fusion=True):
    code = generate_base(rom, carry_fusion=carry_fusion)
    instructions = reachable(rom); facts = analyze(instructions, contexts=True)
    selected = summaries(rom)
    if not selected: raise ValueError('no eligible pure indexed-write loop')
    for summary in selected:
        prefix = f'write_loop_{summary["start"]:04X}'
        for pc, returns in sorted(facts):
            if pc != summary['start']: continue
            suffix = ''.join(f'_r{v:04X}' for v in returns)
            label = f'core_{pc:04X}' + suffix; end = f'core_{summary["end"]:04X}' + suffix
            if code.count(label + ':\n') != 1 or end + ':\n' not in code:
                raise ValueError('pure-loop native context boundary missing')
            stub = emit_summary(summary, prefix, end, label + '_slow')
            replacement = label + ':\n' + '\n'.join(line if line.endswith(':') else '    ' + line for line in stub) + '\n'
            code = code.replace(label + ':\n', replacement, 1)
        code += emit_tables(summary, prefix)
    return code
