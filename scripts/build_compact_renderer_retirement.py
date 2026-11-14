"""Reclaim superseded scalar render code after native lane/bear replacement.

This retires internal constructors, not any original gameplay behavior. Keep
the igloo typed closure and all live native publishers at their public entries.
"""
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
    if not m.get('compact_enemy_ram') or digest(parent) != m['rom']['sha256']:
        raise ValueError('bound native RAM enemy base required')
    if any(digest((ROOT/n).read_bytes()) != h for n, h in m['source_files'].items()):
        raise ValueError('parent source changed')
    for mode in ('ntsc', 'pal', 'bear-ntsc', 'bear-pal', 'matrix'):
        p = json.loads((base.parent/mode/'enemy-ram-check.json').read_bytes())
        if not p['complete'] or p['rom_sha256'] != m['rom']['sha256']:
            raise ValueError('all five native RAM/full-game checks required')
    s = symbols(base/'presentation.sym')
    # Full native lanes replace the scalar tail unconditionally, not by a
    # sampled state. The grid anchors keep floes and enemies in separate rows.
    entry = s['presentation_world_prepare.template_floes']
    if parent[entry-0x4000:entry-0x4000+3] != bytes((0xC3, 0, 0xF4)):
        raise ValueError('unconditional native world dispatch required')
    if m['grid24']['enemy_y'] != [152, 128, 104, 80] or m['grid24']['floe_y'] != [168, 144, 120, 96]:
        raise ValueError('declared separate native lane rows required')
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.is_file():
            shutil.copyfile(p, out/p.name)
        elif p.is_dir():
            (out/p.name).symlink_to(p.resolve(), target_is_directory=True)
    text = [f' ORG ${s["presentation_typed_construct"]:04X}',
            f' LD (${s["pt_bank"]:04X}),A', ' XOR A', f' LD (${s["pt_error"]:04X}),A',
            f' LD A,(${s["pt_bank"]:04X})', ' CP 3', f' JP NC,${s["pt_fail"]:04X}',
            f' LD A,(${s["pt_key"]+5:04X})', f' LD (${s["pt_kind"]:04X}),A',
            ' CP 5', f' JP NZ,${s["pt_fail"]:04X}', f' JP ${s["pt_igloo"]:04X}']
    (out/'rr-typed.asm').write_text('\n'.join(text)+'\n')
    r = subprocess.run([str(verified_tool('sjasmplus')), '--nologo',
        f'--raw={out/"rr-typed.bin"}', str(out/'rr-typed.asm')], capture_output=True, text=True)
    (out/'rr-typed.log').write_text(r.stdout+r.stderr)
    if r.returncode:
        raise ValueError('typed igloo gate assembly failed')
    typed = (out/'rr-typed.bin').read_bytes()
    if len(typed) >= s['pt_fail']-s['presentation_typed_construct']:
        raise ValueError('bounded typed igloo dispatcher required')
    ranges = [
        (s['p_fixed_put_actor'], s['c14_slot'], 'old scalar actor resolver'),
        (s['p_actor_contexts'], s['p_fixed_resolve'], 'old scalar actor contexts'),
        (s['p_template_floe_pattern'], s['p_template_half'], 'superseded generic template pattern readers'),
        (s['p_template_address'], s['p_template_fail'], 'superseded generic template addressing'),
        (s['p_template_load'], s['pk_names_tail'], 'superseded generic floe loader'),
        (s['p_fixed_floe_prepare'], s['presentation_typed_construct'], 'superseded scalar floe/fusion compositor'),
        (s['presentation_typed_construct']+len(typed), s['pt_fail'], 'unused old typed dispatch'),
        (s['pt_pattern'], s['pt_igloo'], 'superseded mono/literal/union/floe typed constructors'),
        (s['pt_footer'], s['hy_header'], 'superseded generic footer constructor'),
        (s['p_fast_geometry_lookup'], s['p_fast_clear_memo'], 'superseded generic geometry memo lookup'),
        (s['p_fast_old_key'], s['p_fast_put'], 'superseded scalar fusion key reader'),
        (s['p_fast_world_tile'], s['aq_unmasked_return'], 'superseded scalar world tile compositor'),
        (s['presentation_geometry_pattern'], s['presentation_world_prepare'], 'superseded generic pattern decoder'),
        (entry+3, s['p_world_row_y'], 'unreachable scalar world tail after unconditional native dispatch'),
        (s['p_world_primitive'], s['p_world_merge'], 'superseded generic scalar primitive'),
        (s['i_primitive'], s['i_vram_address'], 'superseded scalar actor publication path')]
    target = bytearray(parent)
    for first, end, kind in ranges:
        if not 0x4000 <= first < end <= 0x8000:
            raise ValueError('bounded nonempty resident reclamation required')
        target[first-0x4000:end-0x4000] = bytes([255])*(end-first)
        m['compact_retired_resident']['ranges'].append(dict(address=first, size=end-first, kind=kind))
    start = s['presentation_typed_construct']-0x4000
    target[start:start+len(typed)] = typed
    graphics = m['compact_retired_graphics']
    bank_ranges = [(0xA000, s['qe_primitive']), (s['qe_primitive'], s['qe_bulk']),
                   (s['x_hybrid_end'], 0xB800)]
    for first, end in bank_ranges:
        at = 7*16384+first-0x8000
        target[at:at+end-first] = bytes([255])*(end-first)
        graphics['ranges'].append(dict(bank=7, address=first, size=end-first,
            kind='superseded old ice/scalar enemy/geometry residue around the retained native renderer'))
    graphics['retired_physical_bytes'] += sum(b-a for a, b in bank_ranges)
    m['compact_retired_resident']['reclaimed_bytes'] += sum(b-a for a, b, _ in ranges)
    packed = m['template_assets']
    packed['files']['assets-007.bin'] = digest(target[7*16384:8*16384])
    for row in m['contact14']['arena']:
        bank = row['bank']
        row['packed_sha256'] = digest(target[bank*16384:(bank+1)*16384])
    m['source_files']['scripts/build_compact_renderer_retirement.py'] = digest(Path(__file__).read_bytes())
    m['compact_renderer_retirement'] = dict(parent_rom_sha256=digest(parent),
        resident_ranges=[dict(address=a, size=b-a, kind=k) for a, b, k in ranges],
        resident_bytes=sum(b-a for a, b, _ in ranges), bank7_bytes=sum(b-a for a, b in bank_ranges),
        retained_bank7_native_half_open=[s['qe_bulk'], s['x_hybrid_end']],
        typed_igloo_only=True, original_source_game_API_only=True,
        cold_entry_guards_required=True, mapperless=False, human_test_candidate=False)
    filename = 'frostbite-compact-renderer-retirement-internal.rom'
    (out/filename).write_bytes(target)
    m['rom'].update(filename=filename, sha256=digest(target))
    (out/'build.json').write_text(json.dumps(m, indent=2)+'\n')
    print(dict(rom_sha256=digest(target), resident_bytes=sum(b-a for a, b, _ in ranges),
               bank7_bytes=sum(b-a for a, b in bank_ranges)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    build(args.base, args.out)
