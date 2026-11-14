"""Remove the unreachable hybrid bear backend after the complete sprite trial."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from build_compact_packet_experiment import digest
from environment import ROOT, verified_tool
from reference_traces import private_output
from render_build import symbols


def build(base, out):
    base, out = base.resolve(), private_output(out)
    if out.exists():
        raise ValueError('fresh output required')
    m = json.loads((base/'build.json').read_bytes())
    parent = (base/m['rom']['filename']).read_bytes()
    if not m.get('compact_bear_sprite_trial') or digest(parent) != m['rom']['sha256']:
        raise ValueError('qualified exact sprite trial required')
    if any(digest((ROOT/n).read_bytes()) != h for n, h in m['source_files'].items()):
        raise ValueError('trial source changed')
    for mode in ('ntsc', 'pal', 'bear-ntsc', 'bear-pal', 'matrix'):
        proof = json.loads((base.parent/mode/'grid-window-check.json').read_bytes())
        if not proof['complete'] or proof['rom_sha256'] != m['rom']['sha256']:
            raise ValueError('all five unchanged output oracles required')
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.is_file():
            shutil.copyfile(p, out/p.name)
        elif p.is_dir():
            (out/p.name).symlink_to(p.resolve(), target_is_directory=True)
    s = symbols(base/'presentation.sym')
    (out/'symbols.inc').write_text('\n'.join(f'{n} EQU ${v:04X}' for n, v in s.items()
        if '.' not in n and not n.startswith(('an_', 'ao_'))
        and n not in ('AN_RECORD', 'AN_TILE', 'AN_KEYS', 'AO_INFO', 'AO_PACKET', 'AN_HUD_CONT'))
        +f'\nAN_HUD_CONT EQU ${s["presentation_hud_prepare"]+3:04X}\n')
    source = (base/'bs-trial.asm').read_text()
    for first, last in (('an_record_offset:\n', 'an_force_rows:\n'),
                        ('an_draw:\n', 'an_append:\n'),
                        ('an_roles:\n', 'an_background_rows:\n')):
        if source.count(first) != 1 or source.count(last) != 1:
            raise ValueError('unique obsolete module boundaries required')
        start = source.index(first)
        finish = source.index(last, start)
        source = source[:start]+source[finish:]
    old = 'an_registry EQU $A800\nan_extra_records:\n    INCBIN "bear-extra-records.bin"\n'
    if source.count(old) != 1:
        raise ValueError('exact obsolete registry and extra records required')
    source = source.replace(old, '', 1)
    asm = out/'bu-unified.asm'
    asm.write_text(source)
    r = subprocess.run([str(verified_tool('sjasmplus')), '--nologo', f'--inc={out}',
        f'--inc={ROOT/"src"}', f'--raw={out/"bu-unified.bin"}',
        f'--sym={out/"bu-unified.sym"}', str(asm)], capture_output=True, text=True)
    (out/'bu-unified.log').write_text(r.stdout+r.stderr)
    if r.returncode:
        raise ValueError('assembly failed: '+(r.stdout+r.stderr)[-1600:])
    code = (out/'bu-unified.bin').read_bytes()
    q = symbols(out/'bu-unified.sym')
    slot = s['w_selected']-s['w_header']
    ram_at = 115*16384+0x3800+s['w_header']-0xE900
    if code[:slot] != parent[ram_at:ram_at+slot]:
        raise ValueError('public bear RAM wrapper must remain byte-identical')
    target = bytearray(parent)
    body_at = 2*16384+0x1C10
    old_body = m['compact_bear_native_bank']['hybrid_bytes']
    body = code[slot:]
    if len(body) >= old_body:
        raise ValueError('no obsolete body bytes reclaimed')
    target[body_at:body_at+old_body] = body+bytes([255])*(old_body-len(body))
    ranges = [(59, 0xA000, 6144), (133, 0xB800, 2048), (132, 0xB800, 1024),
              (2, 0x9C10+len(body), old_body-len(body))]
    graphics = m['compact_retired_graphics']
    for bank, address, size in ranges:
        at = bank*16384+address-0x8000
        # The duplicated bear directory remains host input for earlier finite
        # packet tests. It has no runtime reader after the source-level relink.
        if bank != 132:
            target[at:at+size] = bytes([255])*size
        graphics['ranges'].append(dict(bank=bank, address=address, size=size,
            kind='superseded hybrid bear backend; full sprites or exact native tiles'))
    graphics['retired_physical_bytes'] += sum(n for _, _, n in ranges)
    target[0x15FF:0x160E] = bytes([255])*15
    resident = m['compact_retired_resident']
    resident['ranges'].append(dict(address=0x55FF, size=15))
    resident['reused_for_resident_code_bytes'] -= 15
    for n in list(s):
        if n.startswith(('an_', 'ao_')):
            del s[n]
    s.update({n: v for n, v in q.items() if n.startswith(('an_', 'ao_'))})
    (out/'presentation.sym').write_text('\n'.join(f'{n}: EQU 0x{v:08X}' for n, v in s.items())+'\n')
    m['bear_three']['body_bytes'] = len(body)
    m['bear_hybrid']['replaced_by'] = 'compact_bear_unified: complete sprites or native tile fallback; former hybrid metadata is ancestry only'
    for row in m['contact14']['arena']:
        bank = row['bank']
        row['packed_sha256'] = digest(target[bank*16384:(bank+1)*16384])
    m['source_files']['scripts/build_compact_bear_unified.py'] = digest(Path(__file__).read_bytes())
    m['compact_bear_unified'] = dict(parent_rom_sha256=digest(parent),
        body_bytes=len(body), former_body_bytes=old_body,
        hybrid_dictionary_and_record_allocation_removed_bytes=8192,
        duplicate_directory_runtime_removed_bytes=1024,
        removed_resident_bridge_bytes=15, native_tile_fallback_retained=True,
        full_rectangle_admission_retained=True, original_data_preserved_in_parent=True,
        mapperless=False, human_test_candidate=False,
        scope='Source-level deletion of unreachable hybrid path; new cold retirement/full-frame checks required.')
    filename = 'frostbite-compact-bear-unified-internal.rom'
    (out/filename).write_bytes(target)
    m['rom'].update(filename=filename, sha256=digest(target))
    (out/'build.json').write_text(json.dumps(m, indent=2)+'\n')
    print(dict(rom_sha256=digest(target), body_bytes=len(body),
               physical_runtime_bytes_retired=sum(n for _, _, n in ranges)+15))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    build(args.base, args.out)
