"""Build shared ice residency against authenticated private M-C inputs."""
import argparse
import json
from pathlib import Path
import subprocess

from environment import ROOT, verified_tool
from presentation_band_spike import COMPANIONS, PARENT_SHA, apply_patch, sha, verified_bytes
from render_build import symbols


def build(out):
    out = Path(out).resolve()
    if out.exists():
        raise ValueError('immutable output directory already exists')
    base = ROOT / 'outputs/presentation/playfield-m-c/build'
    paths = {'build.json': base/'build.json', 'presentation.sym': base/'presentation.sym',
             'i_symbols': ROOT/'outputs/presentation/direct-playfield-i/patch.sym',
             'i_allocation': ROOT/'outputs/presentation/direct-playfield-i/tables.json'}
    inputs = {n: verified_bytes(p, COMPANIONS[n]) for n, p in paths.items()}
    meta = json.loads(inputs['build.json'])
    parent = verified_bytes(base/meta['rom']['filename'], PARENT_SHA)
    if meta['template_assets']['floe_patterns'] != 2049:
        raise ValueError('direct head namespace requires raw IDs0..2048')
    allocation = json.loads(inputs['i_allocation'])
    if (not any(b == 7 and a <= 0xA10C and z >= 0xAA68 for b,a,z in allocation['regions'])
            or any(b == 7 and a < 0xAA68 and a+n > 0xA10C for b,a,n in allocation['allocations'])):
        raise ValueError('bank7 code allocation is not certified unreachable')
    out.mkdir(parents=True)
    for n, data in inputs.items():
        (out/('input-'+n)).write_bytes(data)
    syms = symbols(out/'input-presentation.sym')
    (out/'symbols.inc').write_text('\n'.join(f'{n} EQU ${v:04X}' for n,v in sorted(syms.items()) if '.' not in n)+'\n')
    source = ROOT/'src/presentation_shared_ice.asm'
    run = subprocess.run([str(verified_tool('sjasmplus')), '--nologo', f'--inc={out}',
                          f'--raw={out/"patch.bin"}', f'--sym={out/"patch.sym"}', str(source)],
                         cwd=ROOT, capture_output=True, text=True)
    (out/'assembler.log').write_text(run.stdout+run.stderr)
    if run.returncode:
        raise ValueError(run.stdout+run.stderr)
    q = symbols(out/'patch.sym')
    code = (out/'patch.bin').read_bytes()
    resident = q['q_resident_end']-q['q_init']
    banked = q['q_end']-q['q_strip']
    assert len(code) == resident+banked
    rom = bytearray(parent); patches = []
    def patch(at, old, new):
        patches.append(apply_patch(rom, at, old, new))
    def instruction(op, address):
        return bytes((op,address&255,address>>8))
    patch(q['q_init']-0x4000, bytes(resident), code[:resident])
    at = 7*16384+q['q_strip']-0x8000
    patch(at, parent[at:at+banked], code[resident:])
    patch(syms['presentation_init']-0x4000, instruction(0xCD,0x7F5F), instruction(0xCD,q['q_init']))
    patch(syms['p_template_strip_publish.mask']-0x4000, instruction(0xC3,0x7E5D), instruction(0xC3,q['q_entry']))
    patch(6474, instruction(0xCD,0x7F77), instruction(0xCD,q['q_decode_entry']))
    start, end = syms['p_template_object_fuse']-0x4000, syms['p_template_object_fuse']-0x4000+20
    at = parent.index(instruction(0xCD,syms['p_fast_old_key']),start,end)
    patch(at,instruction(0xCD,syms['p_fast_old_key']),instruction(0xCD,q['q_old_entry']))
    name = 'frostbite-shared-ice-o.rom'
    (out/name).write_bytes(rom)
    (out/'presentation.sym').write_text(inputs['presentation.sym'].decode()+'\n'+'\n'.join(
        f'{n}: EQU 0x{v:08X}' for n,v in q.items() if n.startswith('q_'))+'\n')
    (out/'geometry').symlink_to((base/'geometry').resolve(),target_is_directory=True)
    assets = out/'template-assets';assets.mkdir()
    for bank in meta['template_assets']['physical_banks']:
        n = f'assets-{bank:03d}.bin'; data = bytes(rom[bank*16384:(bank+1)*16384])
        (assets/n).write_bytes(data)
        meta['template_assets']['files'][n] = sha(data)
        meta['static_presentation']['files'][n] = sha(data)
    meta['version'] = 'shared-ice-o-internal'
    meta['rom'].update(filename=name,sha256=sha(rom))
    meta['shared_ice'] = dict(parent_rom_sha256=PARENT_SHA,patches=patches,
        resident_bytes=resident,banked_bytes=banked,ram=[0xE800,0xF240],
        companions={n:sha(data) for n,data in inputs.items()},
        sources={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in (Path(__file__).resolve(),source)},
        scope='Internal unqualified implementation; shared physical ice IDs require independent reference-aware checks.')
    (out/'build.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(dict(rom_sha256=sha(rom),resident_bytes=resident,banked_bytes=banked))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    build(parser.parse_args().out)
