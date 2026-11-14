"""Make the complete hot enemy SGT module independent of the ROM mapper."""
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
    base, out = base.resolve(), private_output(out)
    if out.exists():
        raise ValueError('fresh output required')
    m = json.loads((base/'build.json').read_bytes())
    parent = (base/m['rom']['filename']).read_bytes()
    if not m.get('compact_bear_unified') or digest(parent) != m['rom']['sha256']:
        raise ValueError('bound unified bear base required')
    if any(digest((ROOT/n).read_bytes()) != h for n, h in m['source_files'].items()):
        raise ValueError('parent source changed')
    for mode in ('ntsc', 'pal', 'bear-ntsc', 'bear-pal', 'matrix'):
        proof = json.loads((base.parent/mode/'grid-window-check.json').read_bytes())
        if not proof['complete'] or proof['rom_sha256'] != m['rom']['sha256']:
            raise ValueError('all five original whole-game gates required')
    proof = json.loads((ROOT/'outputs/compact/issue44-enemy-ram-native-01/component-result.json').read_bytes())
    if not proof['complete'] or proof['cases'] != 132 or proof['oracle_rom_sha256'] != CONTROL_SHA:
        raise ValueError('both complete native RAM paths required')
    for n, h in proof['sources'].items():
        if digest((ROOT/n).read_bytes()) != h:
            raise ValueError('RAM component source changed')
    data, _ = assets(ROOT/'outputs/presentation/credit-reference-at/build-final')
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
        r = subprocess.run([str(verified_tool('sjasmplus')), '--nologo', f'--inc={ROOT/"src"}',
            f'--raw={out/(name+".bin")}', f'--sym={out/(name+".sym")}', str(p)], capture_output=True, text=True)
        (out/(name+'.log')).write_text(r.stdout+r.stderr)
        if r.returncode:
            raise ValueError('assembly failed: '+(r.stdout+r.stderr)[-1400:])
        return (out/(name+'.bin')).read_bytes(), symbols(out/(name+'.sym'))

    code, q = assemble('sr-code', [' ORG $E300', 'sw_directory EQU $DB00', 'sw_pool EQU $DD10',
        f'vdp_stream EQU ${s["vdp_stream"]:04X}', ' INCLUDE "compact_enemy_windows.asm"', ' ASSERT $ <= $E500'])
    directory = data['offsets']+data['pool']
    (out/'sr-data.bin').write_bytes(directory)
    gate = [' ORG $566B', f't_mapper EQU ${s["t_mapper"]:04X}']
    for mode in ('upload', 'read'):
        old = symbols(base/'sw-bank.sym')['sw_'+mode]
        gate += [f'sr_{mode}:', ' PUSH HL', ' PUSH DE', ' LD A,H', ' SUB $94',
                 ' RLCA', ' RLCA', ' RLCA', ' LD C,A', ' LD A,L',
                 ' RRCA', ' RRCA', ' RRCA', ' RRCA', ' RRCA', ' AND 7', ' OR C', ' PUSH AF',
                 f' LD A,(${s["t_enabled"]:04X})', ' OR A', f' JR Z,sr_cold_{mode}',
                 ' POP AF', f' CALL ${q["sw_"+mode]:04X}', f' JR sr_done_{mode}',
                 f'sr_cold_{mode}:', ' LD A,64', ' CALL t_mapper', ' POP AF', f' CALL ${old:04X}',
                 f'sr_done_{mode}:', ' LD A,7', ' CALL t_mapper', ' POP DE', ' POP HL',
                 ' LD BC,32', ' ADD HL,BC', f' LD BC,{152 if mode=="upload" else 0}', ' RET']
    gate += [' ASSERT $ <= $5790']
    gates, g = assemble('sr-gates', gate)
    loader, _ = assemble('sr-loader', [' ORG $BF00', ' LD HL,$AD80', ' LD DE,$E300',
        f' LD BC,{len(code)}', ' LDIR', ' LD HL,$A800', ' LD DE,$DB00', ' LD BC,1214', ' LDIR', ' RET'])
    initializer, _ = assemble('sr-init', [' ORG $55FF', ' LD A,64', f' CALL ${s["t_mapper"]:04X}',
        ' CALL $BF00', ' LD A,1', f' JP ${s["t_mapper"]:04X}', ' ASSERT $ <= $560E', ' DS $560E-$,$FF'])
    target = bytearray(parent)
    patches = []

    def patch(at, blob, reason):
        patches.append(dict(offset=at, size=len(blob), before_sha256=digest(parent[at:at+len(blob)]),
                            after_sha256=digest(blob), reason=reason))
        target[at:at+len(blob)] = blob

    for address, blob in ((0xAD80, code), (0xBF00, loader)):
        at = 64*16384+address-0x8000
        if parent[at:at+len(blob)] != bytes([255])*len(blob):
            raise ValueError('empty cold source allocation required')
        patch(at, blob, 'startup-only RAM enemy SGT source')
    if parent[64*16384+0x2800:64*16384+0x2800+len(directory)] != directory:
        raise ValueError('exact shared initializer required')
    if parent[0x3CF1] != 0xC9 or parent[0x15FF:0x160E] != bytes([255])*15:
        raise ValueError('exact bootstrap return and free initializer bridge required')
    patch(0x3CF1, bytes((0xC3, 0xFF, 0x55)), 'preload RAM module before IRQ installation')
    patch(0x15FF, initializer, 'cold initializer uses reclaimed hybrid bridge')
    patch(0x166B, gates, 'hot SGT read/upload calls native RAM without a source bank switch')
    world = next(r for r in m['native_lanes']['auxiliary_code'] if r['ram_address'] == 0xF400)
    for old, mode in (('x_sgt_upload', 'upload'), ('x_pattern_read', 'read')):
        address = g['sr_'+mode]
        at = world['bank']*16384+world['rom_address']-0x8000+s[old]-world['ram_address']
        patch(at, bytes((0xC3, address&255, address>>8)), 'same public SGT entry')
    at = world['bank']*16384+world['rom_address']-0x8000
    (out/'world.bin').write_bytes(target[at:at+world['size']])
    m['world_x']['code_sha256'] = digest(target[at:at+world['size']])

    def refresh(value):
        if isinstance(value, dict):
            if all(k in value for k in ('bank', 'rom_address', 'ram_address', 'size', 'sha256')):
                at = value['bank']*16384+value['rom_address']-0x8000
                value['sha256'] = digest(target[at:at+value['size']])
            for child in value.values():
                refresh(child)
        elif isinstance(value, list):
            for child in value:
                refresh(child)
    refresh(m)
    graphics = m['compact_retired_graphics']
    old_ranges = [r for r in graphics['ranges'] if r['bank'] == 64]
    graphics['ranges'] = [r for r in graphics['ranges'] if r['bank'] != 64]
    graphics['retired_physical_bytes'] -= sum(r['size'] for r in old_ranges)
    for start, end in ((0xAD70, 0xAD80), (0xAD80+len(code), 0xBF00), (0xBF00+len(loader), 0xC000)):
        graphics['ranges'].append(dict(bank=64, address=start, size=end-start, kind='unused cold enemy source allocation'))
        graphics['retired_physical_bytes'] += end-start
    resident = m['compact_retired_resident']
    old = next(r for r in resident['ranges'] if r['address'] == 0x55FF)
    resident['ranges'].remove(old)
    old = next(r for r in resident['ranges'] if r['address'] == 0x56C1)
    additional = len(gates)-86
    old['address'] += additional
    old['size'] -= additional
    resident['reused_for_resident_code_bytes'] += 15+additional
    # The only old DE00 name-cache producer is the superseded floe entry. Its
    # entry is now guarded even though its source bytes are retained for audit.
    resident['ranges'].append(dict(address=s['p_fixed_floe_prepare'], size=1))
    for row in m['contact14']['arena']:
        bank = row['bank']
        row['packed_sha256'] = digest(target[bank*16384:(bank+1)*16384])
    for n in tuple(proof['sources'])+('scripts/build_compact_enemy_ram.py',):
        m['source_files'][n] = digest((ROOT/n).read_bytes())
    m['compact_enemy_ram'] = dict(parent_rom_sha256=digest(parent), patches=patches,
        initializers=[dict(file='sr-code.bin', ram_address=0xE300, size=len(code), sha256=digest(code)),
                      dict(file='sr-data.bin', ram_address=0xDB00, size=len(directory), sha256=digest(directory))],
        old_name_cache_source_only=True, obsolete_floe_entry_guarded=True,
        cold_constructor_retained=True, RAM_only_hot_constructor=True,
        hot_source_ROM_range=dict(bank=64, address=0xA800, size=0x1000),
        mapperless=False, human_test_candidate=False)
    filename = 'frostbite-compact-enemy-ram-internal.rom'
    (out/filename).write_bytes(target)
    m['rom'].update(filename=filename, sha256=digest(target))
    (out/'build.json').write_text(json.dumps(m, indent=2)+'\n')
    print(dict(rom_sha256=digest(target), RAM_code_bytes=len(code), RAM_data_bytes=len(directory), gate_bytes=len(gates)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    build(args.base, args.out)
