"""Build AA from the immutable v0.0.14 control and maintained floe assembly.

Only the floe transaction and retired typed-header code are replaced. Generated
color bytes stay in the ignored build directory; the original packet, NAME,
clock, input, audio and gameplay bytes are preserved. See docs/floe-transactions.md.
"""
import argparse
import json
import subprocess
from pathlib import Path

from environment import ROOT, verified_tool
from presentation_band_spike import apply_patch, sha, verified_bytes
from render_build import symbols

PARENT = 'e59d719e9169a4a73300eb9099008d1a92c77a247b205c78d6961015d16886c5'
SELECTED = 'd28c68590a27004d6624af3d1ecb9d80dc422ed3f4f4241caed2df278d1a5db0'
MAIN_START, MAIN_END = 0xf43d, 0xf5d2
RESIDENT_START, RESIDENT_LIMIT = 0x60b6, 0x6249


def build(base, out):
    if out.exists():
        raise ValueError('immutable output exists')
    meta = json.loads((base/'build.json').read_text())
    parent = verified_bytes(base/meta['rom']['filename'], PARENT)
    for name, value in meta['source_files'].items():
        if sha((ROOT/name).read_bytes()) != value:
            raise ValueError('parent source differs: ' + name)
    out.mkdir(parents=True)
    original_symbols = symbols(base/'presentation.sym')
    s = dict(original_symbols)
    # Exact resident clone of the existing 256-entry color translation. This is
    # data from the verified local control, never a public literal asset dump.
    colors = parent[16384+0x35a0:16384+0x36a0]
    (out/'color-lut.bin').write_bytes(colors)
    (out/'symbols.inc').write_text('\n'.join(
        f'{n} EQU ${v:04X}' for n, v in sorted(s.items()) if '.' not in n)+'\n')
    source = ROOT/'src/presentation_floe_transactions.asm'
    run = subprocess.run([str(verified_tool('sjasmplus')), '--nologo',
        f'--inc={out}', f'--raw={out/"floe.bin"}',
        f'--sym={out/"floe.sym"}', f'--lst={out/"floe.lst"}', str(source)],
        cwd=ROOT, capture_output=True, text=True)
    (out/'assembler.log').write_text(run.stdout+run.stderr)
    if run.returncode:
        raise ValueError(run.stdout+run.stderr)
    q = symbols(out/'floe.sym')
    raw = (out/'floe.bin').read_bytes()
    main_size = MAIN_END-MAIN_START
    resident_size = q['aa_resident_end']-RESIDENT_START
    assert q['aa_floe'] == MAIN_START and q['aa_floe_end'] <= MAIN_END
    assert q['aa_publish'] == RESIDENT_START
    assert 0 < resident_size <= RESIDENT_LIMIT-RESIDENT_START
    assert len(raw) == main_size+resident_size
    rom = bytearray(parent)
    patches = []
    for at, code in ((147*16384+0x383d, raw[:main_size]),
                     (RESIDENT_START-0x4000, raw[main_size:])):
        patches.append(apply_patch(rom, at, parent[at:at+len(code)], code))
    if sha(rom) != SELECTED:
        raise ValueError('source build differs from measured candidate: ' + sha(rom))
    assert rom[0x2100:0x2200] == colors
    assert rom[147*16384+0x39d2:148*16384] == parent[147*16384+0x39d2:148*16384]
    retired = []
    for name in list(s):
        if name.startswith('x_floe') or name == 'x_owner':
            retired.append(name)
            del s[name]
    s.update({n:v for n,v in q.items() if n.startswith('aa_')})
    s['x_floe'] = q['aa_floe']
    (out/'presentation.sym').write_text('\n'.join(
        f'{n}: EQU 0x{v:08X}' for n,v in s.items())+'\n')
    world = bytes(rom[147*16384+0x3800:147*16384+0x3800+1240])
    (out/'world.bin').write_bytes(world)
    (out/'hybrid.bin').write_bytes((base/'hybrid.bin').read_bytes())
    (out/'geometry').symlink_to((base/'geometry').resolve(), target_is_directory=True)
    for key in ('coherent_x', 'native_lanes'):
        for row in meta[key]['auxiliary_code']:
            if row['ram_address'] == 0xf400:
                assert row['size'] == len(world)
                row['sha256'] = sha(world)
    meta['world_x']['code_sha256'] = sha(world)
    assets = out/'template-assets'
    assets.mkdir()
    for bank in meta['template_assets']['physical_banks']:
        name = f'assets-{bank:03d}.bin'
        blob = bytes(rom[bank*16384:(bank+1)*16384])
        (assets/name).write_bytes(blob)
        meta['template_assets']['files'][name] = sha(blob)
        if name in meta['static_presentation'].get('files', {}):
            meta['static_presentation']['files'][name] = sha(blob)
    for row in meta['contact14']['arena']:
        bank = row['bank']
        row['packed_sha256'] = sha(rom[bank*16384:(bank+1)*16384])
    files = dict(meta['source_files'])
    for path in (source, Path(__file__).resolve()):
        files[str(path.relative_to(ROOT))] = sha(path.read_bytes())
    commit = subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip()
    dirty = bool(subprocess.check_output(['git','status','--porcelain'], cwd=ROOT, text=True).strip())
    scope = 'Verified v0.0.14 plus native floe transactions and exact resident color table.'
    meta.update(version='floe-transactions-aa-diagnostic', source_commit=commit,
        source_dirty=dirty, source_files=files, complete_source=dict(commit=commit,
        working_tree_dirty=dirty, files=files, scope=scope))
    meta['floe_transactions'] = dict(parent_rom_sha256=PARENT, patches=patches,
        retired_world_labels=retired, main_ram=[MAIN_START,MAIN_END],
        resident_rom=[RESIDENT_START,q['aa_resident_end']],
        color_lut_sha256=sha(colors), new_ram_bytes=0, new_vram_bytes=0,
        scope='Rendering only. Coherent snapshot, source clock, input/audio and graphics preserved; not fluidity acceptance.')
    name = 'frostbite-floe-transactions-aa.rom'
    (out/name).write_bytes(rom)
    meta['rom'].update(filename=name, sha256=sha(rom))
    (out/'build.json').write_text(json.dumps(meta, indent=2)+'\n')
    print(dict(rom_sha256=sha(rom), source_files=len(files), source_dirty=dirty))
    return meta


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    build(args.base.resolve(), args.out.resolve())
