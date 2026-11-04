"""Build an isolated native-band experiment from the sealed local M-C ROM.

No original assets are embedded here. Output and generated symbols stay local.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from environment import ROOT, verified_tool
from render_build import symbols

PARENT_SHA = '0e43bd16a5219a2d2548580e581ee5e26c7f440e715c18d96e07dbe033351ad0'
COMPANIONS = {
    'build.json': 'd540bad0b19b232d151b18b52a1e4d3adfca11e366b8d716e2f2b3f45404d43b',
    'presentation.sym': '2255dae0feb4ba0a34fc4cb4c07fe1c6d9895ad218293c4978ec0e05eed620b9',
    'i_symbols': '0d4e3fea8465325be6a4c36f39c4a4c13ad53403a2917c11cc10159fe53dd976',
    'i_allocation': 'ddd972e9c543b3136f567bdd5e1263f7d8f37c159dddcc145c98b128ce9e634e',
}


def apply_patch(rom, offset, old, new):
    if (offset < 0 or offset + len(old) > len(rom) or len(old) != len(new)
            or rom[offset:offset + len(old)] != old):
        raise ValueError(f'patch precondition failed at {offset:#x}')
    rom[offset:offset + len(old)] = new
    return dict(offset=offset, before=old.hex(), after=new.hex())


def column_table():
    return bytes((8 + 3 * x // 2) // 8 for x in range(160))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verified_bytes(path, expected):
    data = path.read_bytes()
    if sha(data) != expected:
        raise ValueError(f'companion identity mismatch: {path}')
    return data


def build(base, out):
    base, out = Path(base).resolve(), Path(out).resolve()
    if out.exists():
        raise ValueError('choose a new output directory; previous artifacts are immutable')
    paths = {'build.json': base / 'build.json',
             'presentation.sym': base / 'presentation.sym',
             'i_symbols': ROOT / 'outputs/presentation/direct-playfield-i/patch.sym',
             'i_allocation': ROOT / 'outputs/presentation/direct-playfield-i/tables.json'}
    inputs = {name: verified_bytes(path, COMPANIONS[name])
              for name, path in paths.items()}
    meta = json.loads(inputs['build.json'])
    parent = (base / meta['rom']['filename']).read_bytes()
    if sha(parent) != PARENT_SHA:
        raise ValueError('expected sealed M-C parent')
    out.mkdir(parents=True)
    # Assemble from verified snapshots, never reread mutable companion paths.
    for name, data in inputs.items():
        (out / ('input-' + name)).write_bytes(data)
    syms = symbols(out / 'input-presentation.sym')
    # I's private labels were not appended to the original public symbol file.
    syms.update(symbols(out / 'input-i_symbols'))
    # The I compiler proved these old atlas slots unreachable from live row/
    # bear descriptors. Subtract every I allocation before reclaiming more.
    allocation = json.loads(inputs['i_allocation'])
    bank, origin, end = 7, 0xA10C, 0xAA68
    if not any(b == bank and a <= origin and end <= z
               for b, a, z in allocation['regions']):
        raise ValueError('code range lacks the prior live-domain proof')
    if any(b == bank and a < end and origin < a + n
           for b, a, n in allocation['allocations']):
        raise ValueError('code range intersects a live packet allocation')
    (out / 'symbols.inc').write_text('\n'.join(
        f'{name} EQU ${value:04X}' for name, value in sorted(syms.items())
        if '.' not in name and name not in ('i_end',))
        + f'\nn_code_bank EQU {bank}\nn_code_origin EQU ${origin:04X}\nn_code_limit EQU ${end:04X}\n')
    (out / 'columns.bin').write_bytes(column_table())
    source = ROOT / 'src/presentation_band_spike.asm'
    run = subprocess.run([str(verified_tool('sjasmplus')), '--nologo',
                          f'--inc={out}', f'--raw={out / "patch.bin"}',
                          f'--sym={out / "patch.sym"}', str(source)],
                         text=True, capture_output=True, cwd=ROOT)
    (out / 'assembler.log').write_text(run.stdout + run.stderr)
    if run.returncode:
        raise ValueError(run.stdout + run.stderr)
    new = symbols(out / 'patch.sym')
    code = (out / 'patch.bin').read_bytes()
    resident_size = new['n_resident_end'] - new['n_entry']
    bank_size = new['n_end'] - new['n_primitive']
    assert len(code) == resident_size + bank_size
    rom = bytearray(parent)
    patches = []
    def patch(at, before, after):
        patches.append(apply_patch(rom, at, before, after))
    def jump(address):
        return bytes((0xC3, address & 255, address >> 8))
    patch(syms['i_primitive'] - 0x4000, bytes.fromhex('3a25c2'), jump(new['n_entry']))
    patch(new['n_entry'] - 0x4000, bytes(resident_size), code[:resident_size])
    at = bank * 16384 + new['n_primitive'] - 0x8000
    patch(at, parent[at:at + bank_size], code[resident_size:])
    name = 'frostbite-native-bands-n-spike.rom'
    (out / name).write_bytes(rom)
    (out / 'presentation.sym').write_text(inputs['presentation.sym'].decode()
        + '\n' + '\n'.join(f'{k}: EQU 0x{v:08X}' for k, v in new.items()
                           if k.startswith('n_')) + '\n')
    (out / 'geometry').symlink_to((base / 'geometry').resolve(), target_is_directory=True)
    assets = out / 'template-assets'
    assets.mkdir()
    for asset_bank in meta['template_assets']['physical_banks']:
        asset_name = f'assets-{asset_bank:03d}.bin'
        blob = bytes(rom[asset_bank*16384:(asset_bank+1)*16384])
        (assets / asset_name).write_bytes(blob)
        meta['template_assets']['files'][asset_name] = sha(blob)
        meta['static_presentation']['files'][asset_name] = sha(blob)
    meta['version'] = 'native-bands-n-spike'
    meta['rom'].update(filename=name, sha256=sha(rom))
    meta['native_bands_n'] = dict(
        parent_rom_sha256=PARENT_SHA, patches=patches,
        code_bytes=resident_size + bank_size,
        reclaimed_code_region=[bank, origin, origin + bank_size],
        allocation_proof_sha256=sha(inputs['i_allocation']),
        companion_inputs={name: dict(path=str(paths[name]), sha256=sha(data))
                          for name, data in inputs.items()},
        scratch=[new['n_meta'], new['n_scratch_end']],
        sources={str(f.relative_to(ROOT)): sha(f.read_bytes()) for f in
                 (Path(__file__).resolve(), source)},
        scope='Internal feasibility build. Fixed-row enemy traversal; exact existing publisher and ice fusion. Not qualified for human delivery.')
    (out / 'build.json').write_text(json.dumps(meta, indent=2) + '\n')
    print(json.dumps(dict(rom_sha256=sha(rom), code_bytes=resident_size+bank_size)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=ROOT/'outputs/presentation/playfield-m-c/build')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    build(args.base, args.out)
