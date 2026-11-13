"""Add the owner-requested aligned wordmark to the exact sealed v28 ROM."""
import argparse, hashlib, json, shutil, subprocess
from pathlib import Path
from environment import ROOT, verified_tool
from render_build import symbols
from presentation_credit import compile_tiles, tile_colors

sha = lambda b: hashlib.sha256(b).hexdigest()
PARENT = 'e85b8bc13ebd07888b91d66fc76677ca3e7d210182d40c242cdd6c1a5c2dafd8'

def build(base, out):
    base, out = Path(base).resolve(), Path(out).resolve()
    m = json.loads((base / 'build.json').read_text())
    files = dict(m['source_files'])
    original = (base / m['rom']['filename']).read_bytes()
    if sha(original) != PARENT or len(files) != 225 or any(sha((ROOT / n).read_bytes()) != h for n, h in files.items()):
        raise ValueError('Exact sealed v28 source closure required')
    if out.exists():
        raise ValueError('Fresh output required')
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.name == 'geometry':
            (out / p.name).symlink_to(p.resolve(), target_is_directory=True)
        elif p.is_file():
            shutil.copyfile(p, out / p.name)
        elif p.is_dir():
            shutil.copytree(p, out / p.name)
    s = symbols(base / 'presentation.sym')
    (out / 'symbols.inc').write_text('\n'.join(f'{n} EQU ${v:04X}' for n, v in s.items() if '.' not in n) + '\n')
    tiles, cells = compile_tiles()
    if list(tiles) != [*range(134, 144), *range(250, 254)]:
        raise ValueError('Static credit reservation differs')
    (out / 'aligned-credit-patterns.bin').write_bytes(b''.join(tiles.values()))
    (out / 'aligned-credit-colors.bin').write_bytes(b''.join(tile_colors(i) for i in tiles))
    coarse, coarse_cells = compile_tiles(True)
    if coarse_cells != cells:
        raise ValueError('Vertical phases must share NAME identities')
    (out / 'aligned-credit-coarse.bin').write_bytes(b''.join(coarse.values()))
    source = ROOT / 'src/presentation_credit.asm'
    run = subprocess.run([str(verified_tool('sjasmplus')), '--nologo', f'--inc={out}', f'--raw={out / "aligned-credit.bin"}', f'--sym={out / "aligned-credit.sym"}', str(source)], capture_output=True, text=True)
    (out / 'aligned-credit-assembler.log').write_text(run.stdout + run.stderr)
    if run.returncode:
        raise ValueError(run.stdout + run.stderr)
    q = symbols(out / 'aligned-credit.sym')
    code = (out / 'aligned-credit.bin').read_bytes()
    rom, patches = bytearray(original), []
    def patch(at, data, expected):
        if bytes(rom[at:at + len(data)]) != expected:
            raise ValueError(f'Guard differs at {at:x}')
        if any(at < p['offset'] + p['size'] and p['offset'] < at + len(data) for p in patches):
            raise ValueError('Overlapping patch')
        rom[at:at + len(data)] = data
        patches.append(dict(offset=at, size=len(data), before_sha256=sha(expected), after_sha256=sha(data)))
    patch(0x26aa, code[:80], bytes(80))
    at = 147 * 16384 + 0x3800 + s['aq_credit'] - 0xf400
    patch(at, bytes((195, q['as_names'] & 255, q['as_names'] >> 8)), original[at:at + 3])
    at = 65 * 16384 + s['aq_boot'] - 0x8000
    n = q['as_boot_end'] - q['as_boot']
    tail = code[80:80 + n]
    old_end = 65 * 16384 + s['aq_boot_end'] - 0x8000
    if any(x != 255 for x in original[old_end:at + len(tail)]):
        raise ValueError('Boot tail is occupied')
    patch(at, tail, original[at:at + len(tail)])
    at = 147 * 16384 + 0x3800 + s['aq_credit'] + 3 - 0xf400
    patch(at, code[80 + n:], original[at:at + len(code[80 + n:])])
    at = s['presentation_commit'] - 0x4000
    if original[at:at+3] != bytes((33, s['SAT'] & 255, s['SAT'] >> 8)):
        raise ValueError('Commit hook differs')
    patch(at, bytes((195, q['as_commit_guard'] & 255, q['as_commit_guard'] >> 8)), original[at:at+3])
    def refresh(node):
        if isinstance(node, dict):
            if all(k in node for k in ('bank', 'rom_address', 'ram_address', 'size', 'sha256')):
                at = node['bank'] * 16384 + node['rom_address'] - 0x8000
                node['sha256'] = sha(rom[at:at + node['size']])
            for v in node.values(): refresh(v)
        elif isinstance(node, list):
            for v in node: refresh(v)
    refresh(m)
    world = bytes(rom[147 * 16384 + 0x3800:147 * 16384 + 0x3800 + 1240])
    (out / 'world.bin').write_bytes(world)
    m['world_x']['code_sha256'] = sha(world)
    regions = m['profile']['ram']['regions']
    reserved = next(r for r in regions if r['name'] == 'fixed_reserved')
    if reserved['start'] != 0xda08 or reserved['end'] != 0xdb00:
        raise ValueError('Credit phase byte must come from the existing reserved RAM')
    reserved['start'] = 0xda09
    regions.append(dict(name='credit_displayed_phase', start=0xda08, end=0xda09))
    for bank in (0, 65, 147):
        name = f'assets-{bank:03d}.bin'
        blob = bytes(rom[bank * 16384:(bank + 1) * 16384])
        for section in ('template_assets', 'static_presentation'):
            if name in m[section]['files']:
                m[section]['files'][name] = sha(blob)
                (out / 'template-assets' / name).write_bytes(blob)
    for row in m['contact14']['arena']:
        bank = row['bank']
        row['packed_sha256'] = sha(rom[bank * 16384:(bank + 1) * 16384])
    for p in (Path(__file__), source, ROOT / 'scripts/presentation_credit.py', ROOT / 'scripts/presentation_credit_check.py'):
        files[str(p.resolve().relative_to(ROOT))] = sha(p.read_bytes())
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip())
    m.update(version='aligned-credit-as-diagnostic', source_commit=commit, source_dirty=dirty, source_files=files,
        complete_source=dict(commit=commit, working_tree_dirty=dirty, files=files, scope='Aligned static credit only; v28 mechanics and visuals outside credit preserved.'))
    m['aligned_credit'] = dict(parent_rom_sha256=PARENT, patches=patches, tiles=list(tiles), cells=cells,
        word='RETROWORKS', hyphen=False, word_right=247, top=182, bottom=188, coarse_vertical_shift=1,
        new_ram_bytes=0, occupied_existing_ram_bytes=1, phase_cache_address=0xda08, occupied_existing_vram_bytes=80)
    s.update({n:v for n,v in q.items() if n.startswith('as_')})
    (out / 'presentation.sym').write_text('\n'.join(f'{n}: EQU 0x{v:08X}' for n,v in s.items()) + '\n')
    name = 'frostbite-aligned-credit-as.rom'
    (out / name).write_bytes(rom)
    m['rom'].update(filename=name, sha256=sha(rom))
    (out / 'build.json').write_text(json.dumps(m, indent=2) + '\n')
    print(dict(rom_sha256=sha(rom), sources=len(files), patches=len(patches)))
    return m

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    build(a.base, a.out)
