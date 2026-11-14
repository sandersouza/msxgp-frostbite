"""Try complete monochrome bear sprites before exact native tile fallback.

Internal architecture experiment: retain all original data until qualification.
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


def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('unique source transformation required: '+old[:80])
    return text.replace(old, new, 1)


def build(base, out):
    base, out = base.resolve(), private_output(out)
    if out.exists():
        raise ValueError('fresh output required')
    m = json.loads((base/'build.json').read_bytes())
    parent = (base/m['rom']['filename']).read_bytes()
    if not m.get('compact_enemy_windows') or digest(parent) != m['rom']['sha256']:
        raise ValueError('bound enemy window base required')
    if any(digest((ROOT/n).read_bytes()) != h for n, h in m['source_files'].items()):
        raise ValueError('parent source changed')
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

    def assemble(name, text):
        p = out/(name+'.asm')
        p.write_text(text)
        r = subprocess.run([str(verified_tool('sjasmplus')), '--nologo', f'--inc={out}',
            f'--inc={ROOT/"src"}', f'--raw={out/(name+".bin")}',
            f'--sym={out/(name+".sym")}', str(p)], capture_output=True, text=True)
        (out/(name+'.log')).write_text(r.stdout+r.stderr)
        if r.returncode:
            raise ValueError('assembly failed: '+(r.stdout+r.stderr)[-1800:])
        return (out/(name+'.bin')).read_bytes(), symbols(out/(name+'.sym'))

    source = (base/'bn-hybrid.asm').read_text()
    baseline, q0 = assemble('bs-baseline', source)
    slot = s['w_selected']-s['w_header']
    ram_at = 115*16384+0x3800+s['w_header']-0xE900
    body_at = 2*16384+0x1C10
    if baseline[:slot] != parent[ram_at:ram_at+slot] or baseline[slot:] != parent[body_at:body_at+len(baseline)-slot]:
        raise ValueError('complete current bear source must reproduce')
    # Preserve early-level ordering and its exact dirty-row contract. Only the
    # existing late bear publisher changes representation in this experiment.
    first = source.index('.restored:\n')
    last = source.index('an_record_offset:\n', first)
    source = source[:first]+'''.restored:
    LD A,(p_bg_profile)
    CP 32
    JP Z,.native
    LD A,(p_w_group)
    CP 16
    JP NC,.native
    LD A,(p_w_x)
    CP 11
    JP C,.native
    CP 145
    JP NC,.native
    LD A,(p_sat_bytes)
    CP 1
    JP C,.native
    CP 114
    JP NC,.native
    CALL an_admit
    JP NC,.native
    CALL ao_packet
    CALL ao_full_admit
    JP NC,.native
    CALL an_sprite_patterns
    CALL ao_thin_pattern
    CALL an_append
    CALL ao_append_thin
    JP an_return
.native:
    CALL an_native
    JP an_return

'''+source[last:]
    code, q = assemble('bs-trial', source)
    if any(q[n] != s[n] for n in ('an_early', 'an_header', 'an_copy', 'an_upload', 'an_native', 'an_ram_end')):
        raise ValueError('public RAM ABI changed')
    if len(code)-slot > m['bear_three']['body_bytes']:
        raise ValueError('trial exceeds old body allocation')
    target = bytearray(parent)
    target[ram_at:ram_at+slot] = code[:slot]
    target[body_at:body_at+m['bear_three']['body_bytes']] = code[slot:]+bytes([255])*(m['bear_three']['body_bytes']-(len(code)-slot))
    m['fixed_clock']['ram_code_sha256'] = digest(target[115*16384+0x3800:115*16384+0x3800+m['fixed_clock']['ram_code_bytes']])
    for n, v in q.items():
        if n.startswith(('an_', 'ao_')):
            s[n] = v
    (out/'presentation.sym').write_text('\n'.join(f'{n}: EQU 0x{v:08X}' for n, v in s.items())+'\n')
    filename = 'frostbite-compact-bear-sprite-trial-internal.rom'
    (out/filename).write_bytes(target)
    m['compact_bear_sprite_trial'] = dict(parent_rom_sha256=digest(parent), body_bytes=len(code)-slot,
        former_hybrid_paths_bypass=True, all_original_data_retained=True,
        source_hash=digest(Path(__file__).read_bytes()), human_test_candidate=False, mapperless=False)
    m['source_files']['scripts/build_compact_bear_sprite_trial.py'] = digest(Path(__file__).read_bytes())
    m['rom'].update(filename=filename, sha256=digest(target))
    (out/'build.json').write_text(json.dumps(m, indent=2)+'\n')
    print(dict(rom_sha256=digest(target), body_bytes=len(code)-slot))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    build(args.base, args.out)
