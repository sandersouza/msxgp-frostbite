"""Replace enemy SGT runtime source with exact shared literal planes."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from build_compact_packet_experiment import digest
from compact_enemy_windows_probe import assets
from compact_live_probe import CONTROL_SHA
from environment import ROOT, verified_tool
from reference_traces import private_output
from render_build import symbols


def build(base, out):
    base = base.resolve()
    out = private_output(out)
    if out.exists():
        raise ValueError('fresh output required')
    m = json.loads((base/'build.json').read_bytes())
    parent = (base/m['rom']['filename']).read_bytes()
    if not m.get('compact_grid_window') or digest(parent) != m['rom']['sha256']:
        raise ValueError('bound literal-grid stage required')
    if any(digest((ROOT/n).read_bytes()) != h for n, h in m['source_files'].items()):
        raise ValueError('parent source changed')
    proof = json.loads((ROOT/'outputs/compact/issue44-enemy-windows-native-01/component-result.json').read_bytes())
    if not proof['complete'] or proof['cases'] != 132 or proof['oracle_rom_sha256'] != CONTROL_SHA:
        raise ValueError('all132 SGTs and real VDP proof required')
    for n, h in proof['sources'].items():
        if digest((ROOT/n).read_bytes()) != h:
            raise ValueError('component producer changed')
    data, atlas = assets(ROOT/'outputs/presentation/credit-reference-at/build-final')
    if parent[255*16384+0x1400:255*16384+0x2480] != atlas:
        raise ValueError('original atlas changed')
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.is_file():
            shutil.copyfile(p, out/p.name)
        elif p.is_dir():
            (out/p.name).symlink_to(p.resolve(), target_is_directory=True)
    s = symbols(base/'presentation.sym')

    def assemble(name, lines):
        p = out/(name+'.asm')
        p.write_text('\n'.join(lines)+'\n')
        r = subprocess.run([str(verified_tool('sjasmplus')), '--nologo',
            f'--inc={ROOT/"src"}', f'--raw={out/(name+".bin")}',
            f'--sym={out/(name+".sym")}', str(p)], capture_output=True, text=True)
        (out/(name+'.log')).write_text(r.stdout+r.stderr)
        if r.returncode:
            raise ValueError('assembly failed: '+(r.stdout+r.stderr)[-1400:])
        return (out/(name+'.bin')).read_bytes(), symbols(out/(name+'.sym'))

    for n in ('offsets', 'pool'):
        (out/('sw-'+n+'.bin')).write_bytes(data[n])
    payload, q = assemble('sw-bank', [
        ' ORG $A800', 'sw_directory:', f' INCBIN "{out/"sw-offsets.bin"}"',
        'sw_pool:', f' INCBIN "{out/"sw-pool.bin"}"', ' DS $AD00-$,$FF',
        f'vdp_stream EQU ${s["vdp_stream"]:04X}',
        ' INCLUDE "compact_enemy_windows.asm"', ' ASSERT $ <= $B800'])
    bridge = [' ORG $566B', f't_mapper EQU ${s["t_mapper"]:04X}']
    for mode in ('upload', 'read'):
        bridge += [f'sw_gate_{mode}:', ' PUSH HL', ' PUSH DE',
                   ' LD A,H', ' SUB $94', ' RLCA', ' RLCA', ' RLCA', ' LD C,A',
                   ' LD A,L', ' RRCA', ' RRCA', ' RRCA', ' RRCA', ' RRCA',
                   ' AND 7', ' OR C', ' PUSH AF', ' LD A,64', ' CALL t_mapper',
                   ' POP AF', f' CALL ${q["sw_"+mode]:04X}',
                   ' LD A,7', ' CALL t_mapper', ' POP DE', ' POP HL',
                   ' LD BC,32', ' ADD HL,BC', f' LD BC,{152 if mode=="upload" else 0}', ' RET']
    bridge += [' ASSERT $ <= $5790']
    gate, g = assemble('sw-resident', bridge)
    target = bytearray(parent)
    patches = []

    def patch(at, blob, reason):
        patches.append(dict(offset=at, size=len(blob), before_sha256=digest(parent[at:at+len(blob)]),
                            after_sha256=digest(blob), reason=reason))
        target[at:at+len(blob)] = blob

    if parent[0x166B:0x166B+len(gate)] != bytes([255])*len(gate):
        raise ValueError('exact free resident range required')
    if parent[64*16384+0x2800:64*16384+0x2800+len(payload)] != bytes([255])*len(payload):
        raise ValueError('erased old collision prefix required')
    patch(0x166B, gate, 'same enemy SGT ABI, literal-plane data bank')
    patch(64*16384+0x2800, payload, 'all132 exact SGTs share literal eight-byte windows')
    node = next(r for r in m['native_lanes']['auxiliary_code'] if r['ram_address'] == 0xF400)
    for old, mode in (('x_sgt_upload', 'upload'), ('x_pattern_read', 'read')):
        address = g['sw_gate_'+mode]
        patch(node['bank']*16384+node['rom_address']-0x8000+s[old]-node['ram_address'],
              bytes((0xC3, address&255, address>>8)), 'preserve public '+old+' address')
    at = node['bank']*16384+node['rom_address']-0x8000
    node['sha256'] = digest(target[at:at+node['size']])
    (out/'world.bin').write_bytes(target[at:at+node['size']])
    m['world_x']['code_sha256'] = node['sha256']

    def refresh(value):
        if isinstance(value, dict):
            if all(k in value for k in ('bank', 'rom_address', 'ram_address', 'size', 'sha256')):
                start = value['bank']*16384+value['rom_address']-0x8000
                value['sha256'] = digest(target[start:start+value['size']])
            for child in value.values():
                refresh(child)
        elif isinstance(value, list):
            for child in value:
                refresh(child)
    refresh(m)
    row = next(r for r in m['compact_retired_resident']['ranges'] if r['address'] == 0x566B)
    row['address'] += len(gate)
    row['size'] -= len(gate)
    m['compact_retired_resident']['reused_for_resident_code_bytes'] += len(gate)
    row = next(r for r in m['compact_retired_pools']['ranges'] if r['bank'] == 64)
    row['size'] -= 0x1000
    m['compact_retired_pools']['retired_physical_bytes'] -= 0x1000
    graphics = m['compact_retired_graphics']
    graphics['ranges'] += [dict(bank=64, address=0xA800+len(payload), size=0x1000-len(payload),
        kind='unused enemy-window allocation suffix'), dict(bank=255, address=0x9400, size=4224,
        kind='original enemy SGT atlas retained for independent host oracle only')]
    graphics['retired_physical_bytes'] += 0x1000-len(payload)+4224
    for row in m['contact14']['arena']:
        b = row['bank']
        row['packed_sha256'] = digest(target[b*16384:(b+1)*16384])
    names = tuple(proof['sources'])+('scripts/build_compact_enemy_windows.py',)
    for n in names:
        m['source_files'][n] = digest((ROOT/n).read_bytes())
    m['compact_enemy_windows'] = dict(parent_rom_sha256=digest(parent), patches=patches,
        original_atlas_bytes=4224, directory_bytes=528, plane_pool_bytes=686,
        padding_bytes=8, code_bytes=q['sw_end']-q['sw_planes']-8,
        resident_bridge_bytes=len(gate), complete_native_patterns=132,
        old_atlas_host_oracle_only=True, original_clipping_and_SAT_retained=True,
        mapperless=False, human_test_candidate=False)
    filename = 'frostbite-compact-enemy-windows-internal.rom'
    (out/filename).write_bytes(target)
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    m.update(source_commit=commit, source_dirty=True, version='compact-enemy-windows-internal')
    m['complete_source'] = dict(commit=commit, working_tree_dirty=True, files=m['source_files'],
        scope='Exact enemy literal planes; full-game cadence and retirement qualification required.')
    m['rom'].update(filename=filename, sha256=digest(target))
    (out/'build.json').write_text(json.dumps(m, indent=2)+'\n')
    print(dict(rom_sha256=digest(target), payload_bytes=len(payload), bridge_bytes=len(gate)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    build(args.base, args.out)
