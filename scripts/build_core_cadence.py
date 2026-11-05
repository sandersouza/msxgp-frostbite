"""Build Z from verified X and maintained assembly, never private patch ROMs.

The complete parent hash binds all prior bytes. Individual patch records and
non-overlap checks audit the replacement spans. Original-derived data stays in
the ignored build directory. See docs/core-cadence.md for the retired-code ABI.
"""
import argparse
import json
import subprocess
from pathlib import Path

from environment import ROOT, verified_tool
from presentation_band_spike import apply_patch, sha, verified_bytes
from presentation_header_dictionary import compile_dictionary
from render_build import symbols

PARENT = 'b92478f778a57c70e152497e92102637879248fefac7a9161a9f196928a2c0dc'
SELECTED = 'e59d719e9169a4a73300eb9099008d1a92c77a247b205c78d6961015d16886c5'
ORIGINAL = 'cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834'


def build(base, out):
    if out.exists():
        raise ValueError('immutable output exists')
    meta = json.loads((base/'build.json').read_text())
    parent = verified_bytes(base/meta['rom']['filename'], PARENT)
    for name, value in meta['source_files'].items():
        if sha((ROOT/name).read_bytes()) != value:
            raise ValueError('parent source differs: ' + name)
    source = verified_bytes(ROOT/'references/roms/frostbite.bin', ORIGINAL)
    out.mkdir(parents=True)
    original_symbols = symbols(base/'presentation.sym')
    s = dict(original_symbols)
    rom = bytearray(parent)
    patches, sources, allocated = [], [], set()

    def ins(op, address):
        return bytes((op, address & 255, address >> 8))

    def patch(at, old, new):
        if len(old) != len(new) or allocated.intersection(range(at, at+len(new))):
            raise ValueError('invalid or overlapping patch')
        allocated.update(range(at, at+len(new)))
        patches.append(apply_patch(rom, at, old, new))

    def replace(at, code):
        patch(at, parent[at:at+len(code)], code)

    def assemble(stem, filename, prefix):
        path = ROOT/'src'/filename
        sources.append(path)
        (out/'symbols.inc').write_text('\n'.join(
            f'{n} EQU ${v:04X}' for n, v in sorted(original_symbols.items()) if '.' not in n)+'\n')
        run = subprocess.run([str(verified_tool('sjasmplus')), '--nologo',
            f'--inc={out}', f'--raw={out/(stem+".bin")}',
            f'--sym={out/(stem+".sym")}', f'--lst={out/(stem+".lst")}', str(path)],
            cwd=ROOT, capture_output=True, text=True)
        (out/(stem+'-assembler.log')).write_text(run.stdout+run.stderr)
        if run.returncode:
            raise ValueError(run.stdout+run.stderr)
        q = symbols(out/(stem+'.sym'))
        if prefix:
            s.update({n: v for n, v in q.items() if n.startswith(prefix)})
        return (out/(stem+'.bin')).read_bytes(), q

    effect, q = assemble('effect', 'presentation_core_effect.asm', None)
    assert len(effect) == 135 and q['start'] == 0x9709
    replace(2*16384+0x1709, effect)
    ice, q = assemble('ice', 'presentation_core_ice.asm', 'ice_')
    assert len(ice) == 107 and q['ice_entry'] == 0x8fd9 and q['ice_loop'] == 0x9a24
    replace(2*16384+0x0fd9, ice[:46])
    replace(2*16384+0x1a24, ice[46:])
    actor, q = assemble('actor', 'presentation_core_actors.asm', 'az_')
    assert len(actor) == 133 and q['az_start'] == 0x8c42 and q['az_end'] <= 0x8cc7
    replace(2*16384+0x0c42, actor)

    header, q = assemble('header', 'presentation_direct_header.asm', 'hy_')
    main_size = q['hy_main_end']-q['hy_header']
    lookup_size = q['hy_lookup_end']-q['hy_lookup']
    assert main_size == 739 and lookup_size == 139 and len(header) == main_size+lookup_size
    assert q['hy_header'] == 0x5dd3 and q['hy_lookup'] == 0xfd00
    replace(0x1dd3, header[:main_size])
    patch(s['p_fast_header_prepare.rows']-0x4000,
          ins(0xc3, s['w_header']), ins(0xc3, q['hy_header']))
    replace(146*16384+0x3e00, header[main_size:])
    oldsize = next(r['size'] for r in meta['coherent_x']['auxiliary_code'] if r['ram_address'] == 0xfd00)
    lo, hi = s['w_header_resume']+3-0x4000, s['p_fast_header_glyph']-0x4000
    needle = ins(1, oldsize)+bytes.fromhex('edb0')
    assert parent.count(needle, lo, hi) == 1
    patch(parent.index(needle, lo, hi), ins(1, oldsize), ins(1, lookup_size))
    # X embedded these pointers into the 1280 immutable ice packets. Only the
    # now-unused directory storage is reclaimed; never the live NAME programs.
    for index in range(1280):
        lane = (0, 3, 3, 2, 2, 1, 1, 0)[index//160]
        packet = (35+index//16)*16384+0x3800+index%16*128
        program = parent[packet+116]
        for page in (0, 1):
            owner = lane+page*4
            directory = (116+owner//2)*16384+0x3800+(owner%2)*1024+program*4
            assert parent[directory:directory+3] == parent[packet+117+page*3:packet+120+page*3]
    dictionary, sections = compile_dictionary(source)
    assert sha(dictionary) == '6da3852f056e983f5b4335a222f85a441560045efaf6e746fb02b87beda8de0f'
    (out/'header-dictionary.bin').write_bytes(dictionary)
    for offset in range(0, len(dictionary), 2048):
        replace((116+offset//2048)*16384+0x3800, dictionary[offset:offset+2048])
    for key in ('coherent_x', 'native_lanes'):
        for row in meta[key]['auxiliary_code']:
            if row['ram_address'] == 0xfd00:
                row.update(size=lookup_size, sha256=sha(header[main_size:]))

    selector, q = assemble('selector', 'presentation_player_selector.asm', None)
    assert s['p_player_select'] == 0xadd9 and len(selector) == 35
    replace(2*16384+0x2dd9, selector)
    tail, q = assemble('static', 'presentation_static_tail.asm', 'ys_')
    assert q['ys_static'] == 0x6950 and len(tail) == 172
    assert parent[0x294d:0x2950] == ins(0xc3, s['xh_bg'])
    replace(0x2950, tail)
    lo = 2*16384+(s['presentation_sprites_prepare'] & 16383)
    hi = 2*16384+(s['p_s_finish'] & 16383)
    needle = ins(0xcd, s['p_static_lookup'])
    assert parent.count(needle, lo, hi) == 1
    patch(parent.index(needle, lo, hi), needle, ins(0xcd, q['ys_static']))

    if sha(rom) != SELECTED:
        raise ValueError('source build differs from measured candidate: ' + sha(rom))
    # Remove misleading internal source-PC labels. Only exact surviving public
    # entry labels retain meaning inside these lowered source contexts.
    retired = []
    entries = {'core_F875', 'core_FA0B', 'core_FEB8_rF850'}
    spans = ((0x8c42, 0x8cc7), (0x8fd9, 0x9007), (0x9709, 0x9790), (0x9a24, 0x9a61))
    for name, address in list(s.items()):
        if name.startswith('core_') and name not in entries and any(a <= address < b for a, b in spans):
            retired.append(name)
            del s[name]
    (out/'presentation.sym').write_text('\n'.join(f'{n}: EQU 0x{v:08X}' for n, v in s.items())+'\n')
    for name in ('world.bin', 'hybrid.bin'):
        (out/name).write_bytes((base/name).read_bytes())
    (out/'geometry').symlink_to((base/'geometry').resolve(), target_is_directory=True)
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
    sources.extend((Path(__file__).resolve(), ROOT/'scripts/presentation_header_dictionary.py'))
    files = dict(meta['source_files'])
    for path in sources:
        files[str(path.relative_to(ROOT))] = sha(path.read_bytes())
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip())
    meta.update(version='core-cadence-z-diagnostic', source_commit=commit, source_dirty=dirty,
        source_files=files, complete_source=dict(commit=commit, working_tree_dirty=dirty, files=files,
        scope='Verified X plus maintained core summaries, direct header dictionary, player selector and static SAT tail.'))
    meta['core_cadence'] = dict(parent_rom_sha256=PARENT, original_rom_sha256=ORIGINAL,
        patches=patches, retired_core_labels=retired, dictionary_sections=sections,
        dictionary_sha256=sha(dictionary), new_ram_bytes=0,
        scope='Coherent diagnostic; source CPU/all RAM and input/audio ordering preserved. Not fluidity acceptance.')
    name = 'frostbite-core-cadence-z.rom'
    (out/name).write_bytes(rom)
    meta['rom'].update(filename=name, sha256=sha(rom))
    (out/'build.json').write_text(json.dumps(meta, indent=2)+'\n')
    print(dict(rom_sha256=sha(rom), retired_core_labels=len(retired), source_dirty=dirty))
    return meta


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    build(args.base.resolve(), args.out.resolve())
