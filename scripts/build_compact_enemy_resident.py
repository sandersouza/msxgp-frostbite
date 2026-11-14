"""Relink the remaining enemy renderer into reclaimed resident code space."""
import argparse
import json
from pathlib import Path
import re
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
    if not m.get('compact_renderer_retirement') or digest(parent) != m['rom']['sha256']:
        raise ValueError('bound scalar renderer retirement required')
    if any(digest((ROOT/n).read_bytes()) != h for n, h in m['source_files'].items()):
        raise ValueError('parent source changed')
    for mode in ('ntsc', 'pal', 'bear-ntsc', 'bear-pal', 'matrix'):
        proof = json.loads((base.parent/mode/'enemy-ram-check.json').read_bytes())
        if not proof['complete'] or proof['rom_sha256'] != m['rom']['sha256']:
            raise ValueError('all five current retirement gates required')
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.is_file():
            shutil.copyfile(p, out/p.name)
        elif p.is_dir():
            (out/p.name).symlink_to(p.resolve(), target_is_directory=True)
    s = symbols(base/'presentation.sym')
    read = lambda address, size: parent[7*16384+address-0x8000:7*16384+address-0x8000+size]
    roles = read(s['qe_roles_data'], 96)
    (out/'qe-roles.bin').write_bytes(roles)
    (out/'er-dirty.bin').write_bytes(read(s['x_dirty_masks'], 32))
    bulk = (ROOT/'src/presentation_direct_enemy_body.asm').read_text()
    bulk = bulk[:bulk.index('qe_primitive:\n')]+bulk[bulk.index('qe_bulk:\n'):]
    # Two assembled uses plus one in the disabled eager-key publisher.
    if bulk.count('    LD A,(p_w_coarse)\n') != 3:
        raise ValueError('accepted grid24 coarse override sites changed')
    bulk = bulk.replace('    LD A,(p_w_coarse)\n', '    XOR A\n    NOP\n    NOP\n')
    hybrid = (ROOT/'src/presentation_certified_enemies.asm').read_text()
    hybrid = hybrid.replace('    INCLUDE "world-addresses.inc"\n', '')
    expanded = (ROOT/'src/presentation_open_view.asm').read_text()
    eligible = expanded[expanded.index('aq_eligible:\n'):expanded.index('aq_eligible_code_end:\n')]
    eligible = eligible.replace('aq_eligible:', 'x_eligible:', 1)
    start, end = hybrid.index('x_eligible:\n'), hybrid.index('x_accepted:\n')
    hybrid = hybrid[:start]+eligible+'    DS x_accepted-$,0\n'+hybrid[end:]
    # The reference to the fixed x_accepted address above is deliberately only
    # used while reproducing the old source. Use its literal old value to avoid
    # a forward-symbol DS expression in both assembly passes.
    hybrid = hybrid.replace('    DS x_accepted-$,0\n', f'    DS ${s["x_accepted"]:04X}-$,0\n')
    if hybrid.count('    ADD A,153\n') != 1:
        raise ValueError('one accepted preflight Y anchor required')
    hybrid = hybrid.replace('    ADD A,153\n', '    ADD A,152\n')
    # The accepted border stage replaced the clip routine and its unused left
    # table with the full-playfield mask reader. Preserve that source, including
    # its old alignment padding, before relocating any instruction.
    border = (ROOT/'src/presentation_border.asm').read_text()
    clip = border[border.index('ac_clip:\n'):border.index('ac_clip_code_end:\n')]
    clip = clip.replace('ac_clip:', 'x_clip_pattern:', 1)
    first, last = hybrid.index('x_clip_pattern:\n'), hybrid.index('x_right_masks:\n')
    hybrid = hybrid[:first]+clip+f'x_left_masks:\n    DS ${s["x_right_masks"]:04X}-$,0\n'+hybrid[last:]
    first, last = hybrid.index('ab_certified_setup:\n'), hybrid.index('ab_certified_setup_end:\n')
    setup = hybrid[first:last]
    if setup.count('    CP 8\n') != 1:
        raise ValueError('one accepted certified clipping threshold required')
    hybrid = hybrid[:first]+setup.replace('    CP 8\n', '    CP 11\n')+hybrid[last:]
    start = hybrid.index('x_dirty_masks:\n')
    end = hybrid.index('x_hybrid_end:\n', start)
    hybrid = hybrid[:start]+'x_dirty_masks:\n    INCBIN "er-dirty.bin"\n'+hybrid[end:]
    owned = set(re.findall(r'^([A-Za-z_][A-Za-z0-9_]*):', bulk+'\n'+hybrid, re.M))
    owned.update(re.findall(r'^([A-Za-z_][A-Za-z0-9_]*) EQU', bulk+'\n'+hybrid, re.M))
    (out/'symbols.inc').write_text('\n'.join(f'{n} EQU ${v:04X}' for n, v in s.items()
        if '.' not in n and n not in owned)+'\n')

    def assemble(name, text):
        p = out/(name+'.asm')
        p.write_text(text)
        r = subprocess.run([str(verified_tool('sjasmplus')), '--nologo', f'--inc={out}',
            f'--raw={out/(name+".bin")}', f'--sym={out/(name+".sym")}', str(p)], capture_output=True, text=True)
        (out/(name+'.log')).write_text(r.stdout+r.stderr)
        if r.returncode:
            raise ValueError('assembly failed: '+(r.stdout+r.stderr)[-1500:])
        return (out/(name+'.bin')).read_bytes(), symbols(out/(name+'.sym'))

    bulk = '    INCLUDE "symbols.inc"\n    DEFINE WITH_LAZY_ENEMY\n    ORG $A3CD\n'+bulk
    old_bulk, _ = assemble('er-bulk-baseline', bulk)
    old_hybrid, _ = assemble('er-hybrid-baseline', hybrid)
    for name, actual, expected in (('bulk', old_bulk, read(s['qe_bulk'], s['qe_end']-s['qe_bulk'])),
                                   ('hybrid', old_hybrid, read(s['x_hybrid'], s['x_hybrid_end']-s['x_hybrid']))):
        if actual != expected:
            differences = [(i, a, b) for i, (a, b) in enumerate(zip(actual, expected)) if a != b]
            raise ValueError(f'current {name} source differs: lengths{len(actual)}/{len(expected)}, first{differences[:16]}')
    bulk = bulk.replace('    ORG $A3CD\n', '    ORG $5AF6\n')
    bulk = bulk.replace('    ASSERT $ < $A800', '    ASSERT $ <= $5C98')
    hybrid = hybrid.replace('    ORG $A50D\n', '    ORG $585F\n')
    hybrid = hybrid.replace(f'    DS ${s["x_accepted"]:04X}-$,0\n', '')
    hybrid = hybrid.replace(f'    DS ${s["x_right_masks"]:04X}-$,0\n', '')
    hybrid = hybrid.replace('x_right_masks:\n', '    ASSERT $ <= $5A5F\n    ORG $7A13\nx_right_masks:\n')
    hybrid = hybrid.replace('    ASSERT $ <= $AA00\n    DS $AA00-$,0\n', '')
    hybrid = hybrid.replace('    ASSERT $ <= $AA68', '    ASSERT $ <= $7B2A')
    new_bulk, qb = assemble('er-bulk', bulk)
    new_hybrid, qh = assemble('er-hybrid', hybrid)
    first_size = qh['x_left_masks']-qh['x_hybrid']
    if not 0 < first_size <= 512 or len(new_hybrid)-first_size > 279:
        raise ValueError('bounded split native enemy allocation required')
    target = bytearray(parent)
    allocations = [(0x5AF6, new_bulk), (0x585F, new_hybrid[:first_size]), (0x7A13, new_hybrid[first_size:])]
    for address, blob in allocations:
        if parent[address-0x4000:address-0x4000+len(blob)] != bytes([255])*len(blob):
            raise ValueError('exact reclaimed resident range required')
        target[address-0x4000:address-0x4000+len(blob)] = blob
    # Only direct CALL operands in the known RAM world driver change. No raw
    # global search/replace over data or generated source instructions.
    world = next(r for r in m['native_lanes']['auxiliary_code'] if r['ram_address'] == 0xF400)
    world_at = world['bank']*16384+world['rom_address']-0x8000
    replacement_entries = {s['qe_bulk']: qb['qe_bulk'], s['x_hybrid']: qh['x_hybrid'],
                           s['x_force_previous']: qh['x_force_previous'], s['x_force_apply']: qh['x_force_apply']}
    callsites = []
    for old, new in replacement_entries.items():
        needle = bytes((0xCD, old&255, old>>8))
        hits = [i for i in range(world_at, world_at+world['size']-2) if parent[i:i+3] == needle]
        if len(hits) != 1:
            raise ValueError(f'exact single world CALL required for{old:04X}: {hits}')
        at = hits[0]
        target[at+1:at+3] = new.to_bytes(2, 'little')
        callsites.append(dict(rom_offset=at, old_target=old, new_target=new))
    (out/'world.bin').write_bytes(target[world_at:world_at+world['size']])
    m['world_x']['code_sha256'] = digest(target[world_at:world_at+world['size']])
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
    resident = m['compact_retired_resident']
    for address, blob in allocations:
        row = next(r for r in resident['ranges'] if r['address'] == address and r['size'] >= len(blob))
        row['address'] += len(blob)
        row['size'] -= len(blob)
        if not row['size']:
            resident['ranges'].remove(row)
        resident['reused_for_resident_code_bytes'] += len(blob)
    # Remove the earlier one-byte entry guard, now inside the resident native
    # function. Its complete superseded scalar allocation was already retired.
    resident['ranges'] = [r for r in resident['ranges'] if not (r['address'] == 0x585F and r['size'] == 1)]
    start, end = s['qe_bulk'], s['x_hybrid_end']
    target[7*16384+start-0x8000:7*16384+end-0x8000] = bytes([255])*(end-start)
    m['compact_retired_graphics']['ranges'].append(dict(bank=7, address=start, size=end-start, kind='relinked complete native enemy renderer'))
    m['compact_retired_graphics']['retired_physical_bytes'] += end-start
    m['template_assets']['files']['assets-007.bin'] = digest(target[7*16384:8*16384])
    for row in m['contact14']['arena']:
        bank = row['bank']
        row['packed_sha256'] = digest(target[bank*16384:(bank+1)*16384])
    # Keep source-facing public auxiliary symbols while replacing only actual
    # bank7-owned symbols, not same-valued bank2 labels such as x_resume.
    s.update({n: v for n, v in {**qb, **qh}.items() if n in owned or any(n.startswith(k+'.') for k in owned)})
    (out/'presentation.sym').write_text('\n'.join(f'{n}: EQU 0x{v:08X}' for n, v in s.items())+'\n')
    m['source_files']['scripts/build_compact_enemy_resident.py'] = digest(Path(__file__).read_bytes())
    m['compact_enemy_resident'] = dict(parent_rom_sha256=digest(parent),
        allocations=[dict(address=a, size=len(b)) for a, b in allocations], callsites=callsites,
        complete_old_module_reproduced=True, all_bank7_runtime_reads_forbidden=True,
        original_native_admission_and_cache_semantics_retained=True, mapperless=False, human_test_candidate=False)
    filename = 'frostbite-compact-enemy-resident-internal.rom'
    (out/filename).write_bytes(target)
    m['rom'].update(filename=filename, sha256=digest(target))
    (out/'build.json').write_text(json.dumps(m, indent=2)+'\n')
    print(dict(rom_sha256=digest(target), allocations=[(hex(a), len(b)) for a, b in allocations]))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    build(args.base, args.out)
