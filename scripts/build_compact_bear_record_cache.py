"""Use packed bear records with one persistent original-record RAM cache."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from build_compact_packet_experiment import digest
from compact_bear_records import pack, unpack
from environment import ROOT, verified_tool
from reference_traces import private_output
from render_build import symbols


def build(base, out):
    base, out = base.resolve(), private_output(out)
    if out.exists():
        raise ValueError('fresh output required')
    m = json.loads((base/'build.json').read_bytes())
    parent = (base/m['rom']['filename']).read_bytes()
    if not m.get('compact_enemy_resident') or digest(parent) != m['rom']['sha256']:
        raise ValueError('bound resident-enemy base required')
    if any(digest((ROOT/n).read_bytes()) != h for n, h in m['source_files'].items()):
        raise ValueError('parent source changed')
    for mode in ('ntsc', 'pal', 'bear-ntsc', 'bear-pal', 'matrix'):
        d = json.loads((base.parent/mode/'enemy-ram-check.json').read_bytes())
        if not d['complete'] or d['rom_sha256'] != m['rom']['sha256']:
            raise ValueError('all five original game gates required')
    proof = json.loads((ROOT/'outputs/compact/issue44-bear-record-native-02/component-result.json').read_bytes())
    if not proof['complete'] or proof['cases'] != 96 or proof['input_rom_sha256'] != m['rom']['sha256']:
        raise ValueError('complete bound native record miss/hit proof required')
    for n, h in proof['sources'].items():
        if digest((ROOT/n).read_bytes()) != h:
            raise ValueError('record producer changed')
    original = b''.join(parent[b*16384+0x3800:(b+1)*16384] for b in range(67, 70))
    data = pack(original)
    if unpack(data) != original or digest(original) != proof['files']['expected.bin']:
        raise ValueError('all original record bytes must match native proof')
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.is_file():
            shutil.copyfile(p, out/p.name)
        elif p.is_dir():
            (out/p.name).symlink_to(p.resolve(), target_is_directory=True)
    s = symbols(base/'presentation.sym')
    for n, blob in data.items():
        (out/('br-'+n+'.bin')).write_bytes(blob)
    (out/'br-original.bin').write_bytes(original)

    def assemble(name, text):
        p = out/(name+'.asm')
        p.write_text(text)
        r = subprocess.run([str(verified_tool('sjasmplus')), '--nologo', f'--inc={ROOT/"src"}',
            f'--raw={out/(name+".bin")}', f'--sym={out/(name+".sym")}', str(p)], capture_output=True, text=True)
        (out/(name+'.log')).write_text(r.stdout+r.stderr)
        if r.returncode:
            raise ValueError('assembly failed: '+(r.stdout+r.stderr)[-1400:])
        return (out/(name+'.bin')).read_bytes(), symbols(out/(name+'.sym'))

    payload, q = assemble('br-bank', '\n'.join([' ORG $A800', 'br_records:',
        f' INCBIN "{out/"br-records.bin"}"', ' DS $B500-$,$FF', 'br_raw:',
        f' INCBIN "{out/"br-raw.bin"}"', ' DS $BB00-$,$FF',
        ' INCLUDE "compact_bear_records.asm"', ' ASSERT $ <= $C000'])+'\n')
    gate, _ = assemble('br-gate', f' ORG $5008\n PUSH AF\n LD A,67\n CALL ${s["t_mapper"]:04X}\n POP AF\n CALL ${q["br_record"]:04X}\n LD A,2\n JP ${s["t_mapper"]:04X}\n ASSERT $ <= $502C\n')
    first, end = s['ai_body']-0x4000, s['ai_body.row']-0x4000
    needle = bytes((0x3A, s['p_tf_cache']&255, s['p_tf_cache']>>8, 0x47))
    call = bytes((0xCD, s['p_fast_clear_memo']&255, s['p_fast_clear_memo']>>8))
    if parent[first:end].count(needle) != 1 or parent[first:end].count(call) != 1:
        raise ValueError('unique original record-index and completed-dimensions boundaries required')
    at = first+parent[first:end].index(needle)
    stop = first+parent[first:end].index(call)
    prefix, _ = assemble('br-body-prefix', '\n'.join([f' ORG ${at+0x4000:04X}',
        f' LD A,(${s["p_tf_cache"]:04X})', ' CALL $5008', f' LD (${s["p_tf_cache"]:04X}),HL',
        ' LD DE,48', ' ADD HL,DE', f' LD DE,${s["p_geo_columns"]:04X}', ' LD BC,3', ' LDIR',
        ' LD A,2', f' LD (${s["p_tf_column"]:04X}),A', f' JP ${stop+0x4000:04X}',
        f' ASSERT $ <= ${stop+0x4000:04X}', f' DS ${stop+0x4000:04X}-$,$FF'])+'\n')
    loader_source = (base/'sr-loader.asm').read_text()
    old_loader = (base/'sr-loader.bin').read_bytes()
    if loader_source.count(' RET\n') != 1 or parent[64*16384+0x3F00:64*16384+0x3F00+len(old_loader)] != old_loader:
        raise ValueError('exact current startup RAM loader required')
    loader_source = loader_source.replace(' RET\n', ' XOR A\n LD ($DFBE),A\n LD ($DFBF),A\n RET\n')
    loader, _ = assemble('br-init', loader_source)
    target = bytearray(parent)
    patches = []
    def patch(offset, blob, reason):
        patches.append(dict(offset=offset, size=len(blob), before_sha256=digest(parent[offset:offset+len(blob)]),
            after_sha256=digest(blob), reason=reason))
        target[offset:offset+len(blob)] = blob
    if parent[0x1008:0x1008+len(gate)] != bytes([255])*len(gate):
        raise ValueError('reclaimed generic-address bridge required')
    patch(0x1008, gate, 'native original-record cache bridge')
    patch(at, prefix, 'same native bear body consumes one reconstructed original64-byte record')
    patch(64*16384+0x3F00, loader, 'invalidate record cache after platform initialization')
    if parent[67*16384+0x2800:67*16384+0x3800] != bytes([255])*4096:
        raise ValueError('erased old contact prefix required')
    patch(67*16384+0x2800, payload, 'nine-bit dense IDs plus original raw key/predicate map')
    for bank in (68, 69):
        patch(bank*16384+0x3800, bytes([255])*2048, 'retired original expanded native records')
    resident = m['compact_retired_resident']
    row = next(r for r in resident['ranges'] if r['address'] == 0x5008)
    row['address'] += len(gate)
    row['size'] -= len(gate)
    resident['reused_for_resident_code_bytes'] += len(gate)
    row = next(r for r in m['compact_retired_pools']['ranges'] if r['bank'] == 67)
    if row['size'] != 0x3800:
        raise ValueError('complete retired native record prefix required')
    row['size'] = 0x2800
    m['compact_retired_pools']['retired_physical_bytes'] -= 4096
    graphics = m['compact_retired_graphics']
    row = next(r for r in graphics['ranges'] if r['bank'] == 64 and r['address'] == 0xBF00+len(old_loader))
    delta = len(loader)-len(old_loader)
    row['address'] += delta
    row['size'] -= delta
    graphics['retired_physical_bytes'] -= delta
    for bank, start, finish in ((67, 0xB460, 0xB500), (67, 0xBAAC, 0xBB00),
                                (67, 0xA800+len(payload), 0xC000), (68, 0xB800, 0xC000), (69, 0xB800, 0xC000)):
        graphics['ranges'].append(dict(bank=bank, address=start, size=finish-start,
            kind='unused packed bear record allocation / retired expanded records'))
        graphics['retired_physical_bytes'] += finish-start
    for row in m['contact14']['arena']:
        bank = row['bank']
        row['packed_sha256'] = digest(target[bank*16384:(bank+1)*16384])
    for n in tuple(proof['sources'])+('scripts/build_compact_bear_record_cache.py', 'tests/test_compact_bear_records.py', 'scripts/compact_enemy_ram_check.py'):
        m['source_files'][n] = digest((ROOT/n).read_bytes())
    m['compact_bear_record_cache'] = dict(parent_rom_sha256=digest(parent), patches=patches,
        packed_record_bytes=3168, raw_ID_map_bytes=940, original_record_bytes=6144,
        original_records_file='br-original.bin', original_records_sha256=digest(original),
        RAM_cache_address=0xDFC0, RAM_cache_bytes=64, published_id_plus_one=0xDFBE,
        reserved_zero_byte=0xDFBF, complete_native_records=96, claims_former_unused_suffix_bytes=66,
        exact_record_ABI_retained=True, mapperless=False, human_test_candidate=False)
    filename = 'frostbite-compact-bear-record-cache-internal.rom'
    (out/filename).write_bytes(target)
    m['rom'].update(filename=filename, sha256=digest(target))
    (out/'build.json').write_text(json.dumps(m, indent=2)+'\n')
    print(dict(rom_sha256=digest(target), packed_data_bytes=4108, decoder_bytes=q['br_end']-q['br_record'],
               persistent_RAM_cache_bytes=66, bridge_bytes=len(gate)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    build(args.base, args.out)
