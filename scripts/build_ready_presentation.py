"""Build AB from exact AA plus certified enemies and first-safe-field admission.

The assembler uses maintained source only. No private candidate, original data
dump or research script is an input. Legacy two-field validators remain intact;
the new explicit one-field validation producers are part of this build closure.
"""
import argparse
import json
from pathlib import Path
import subprocess

from environment import ROOT, verified_tool
from presentation_band_spike import sha, verified_bytes
from render_build import symbols

PARENT = 'd28c68590a27004d6624af3d1ecb9d80dc422ed3f4f4241caed2df278d1a5db0'
SELECTED = '9d2ee2926bc8de7fd0d22b05e7ad334e76078141bfde997720adfb62414cc77b'
PARENT_SYMBOLS = '896f110f2606811437bbc0826c8eefc3517388ccb6afed854d255298f6f094a7'
PARENT_SOURCES = '67c7657b663329da3e279555eb7470dfb360a3c7b630f3d2dd6e590342f4fe52'
HYBRID_BANK, HYBRID_START, HYBRID_END = 7, 0xA50D, 0xAA26
KERNEL_BANK, KERNEL_ROM_START = 115, 0xB800
WORLD_BANK, WORLD_ROM_START, WORLD_SIZE = 147, 0xB800, 1240
EXTERNAL_WORLD = ('x_row_dirty', 'x_sgt_upload', 'x_pattern_read')
HYBRID_PREFIXES = ('x_hybrid', 'x_eligible', 'x_accepted', 'x_preflight',
    'x_apply_invalid', 'x_clip_pattern', 'x_counts', 'x_left_masks',
    'x_right_masks', 'x_lane_bits', 'x_dirty_masks', 'x_force_previous',
    'x_force_apply')


def offset(bank, address):
    return bank*16384+address-0x8000


def patch_record(at, before_data, after_data, **details):
    """Bounded provenance: hashes and byte counts, never large code hex dumps."""
    return dict(offset=at, size=len(after_data), before_sha256=sha(before_data),
        after_sha256=sha(after_data), changed_bytes=sum(a != b for a,b in zip(before_data,after_data)),
        **details)


def build(base, out, source=None):
    base, out = Path(base).resolve(), Path(out).resolve()
    if out.exists():
        raise ValueError('immutable output exists')
    source = Path(source).resolve() if source else ROOT/'src/presentation_certified_enemies.asm'
    producer = Path(__file__).resolve()
    validators = (ROOT/'scripts/presentation_ready_clock.py',
                  ROOT/'scripts/presentation_ready_check.py')
    additions = (source, producer, *validators)
    for path in additions:
        path.relative_to(ROOT)
        if not path.is_file():
            raise ValueError('maintained source missing: ' + str(path))
    original_meta = (base/'build.json').read_bytes()
    meta = json.loads(original_meta)
    files = dict(meta['source_files'])
    closure = json.dumps(files, sort_keys=True, separators=(',', ':')).encode()
    if (len(files) != 147 or sha(closure) != PARENT_SOURCES
            or files != meta['complete_source']['files']):
        raise ValueError('AA source closure differs')
    parent_path = base/meta['rom']['filename']
    parent = verified_bytes(parent_path, PARENT)
    verified_bytes(base/'presentation.sym', PARENT_SYMBOLS)
    protected = {name: sha((ROOT/name).read_bytes()) for name in files}
    if protected != files:
        raise ValueError('AA maintained sources differ')
    added_hashes = {str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in additions}
    if set(files) & set(added_hashes) or len(added_hashes) != 4:
        raise ValueError('four additive maintained sources required')
    files.update(added_hashes)
    if len(files) != 151:
        raise ValueError('complete source closure must contain 151 files')
    s = symbols(base/'presentation.sym')
    hybrid_at = offset(HYBRID_BANK, HYBRID_START)
    hybrid_size = HYBRID_END-HYBRID_START
    world_at = offset(WORLD_BANK, WORLD_ROM_START)
    if (base/'hybrid.bin').read_bytes() != parent[hybrid_at:hybrid_at+hybrid_size]:
        raise ValueError('AA hybrid companion differs')
    if (base/'world.bin').read_bytes() != parent[world_at:world_at+WORLD_SIZE]:
        raise ValueError('AA world companion differs')
    kernel_at = offset(KERNEL_BANK, KERNEL_ROM_START)
    kernel_size = meta['fixed_clock']['ram_code_bytes']
    if not 0 < kernel_size <= 1792:
        raise ValueError('AA kernel extent differs')
    if sha(parent[kernel_at:kernel_at+kernel_size]) != meta['fixed_clock']['ram_code_sha256']:
        raise ValueError('AA kernel identity differs')
    for bank in meta['template_assets']['physical_banks']:
        name = f'assets-{bank:03d}.bin'
        data = parent[bank*16384:(bank+1)*16384]
        if (sha(data) != meta['template_assets']['files'][name]
                or (base/'template-assets'/name).read_bytes() != data):
            raise ValueError('AA template companion differs: ' + name)
    for row in meta['contact14']['arena']:
        bank = row['bank']
        if sha(parent[bank*16384:(bank+1)*16384]) != row['packed_sha256']:
            raise ValueError('AA packed contact bank differs')
    out.mkdir(parents=True)
    (out/'symbols.inc').write_text('\n'.join(f'{n} EQU ${v:04X}'
        for n,v in sorted(s.items()) if '.' not in n and not n.startswith('x_'))+'\n')
    (out/'world-addresses.inc').write_text('\n'.join(
        f'{n} EQU ${s[n]:04X}' for n in EXTERNAL_WORLD)+'\n')
    assembler = verified_tool('sjasmplus')
    run = subprocess.run([str(assembler), '--nologo', f'--inc={out}',
        f'--raw={out/"hybrid.bin"}', f'--sym={out/"hybrid.sym"}',
        f'--lst={out/"hybrid.lst"}', str(source)], cwd=ROOT,
        capture_output=True, text=True)
    (out/'assembler.log').write_text(run.stdout+run.stderr)
    if run.returncode:
        raise ValueError(run.stdout+run.stderr)
    q = symbols(out/'hybrid.sym')
    hybrid = (out/'hybrid.bin').read_bytes()
    if (q['x_hybrid'] != HYBRID_START or q['x_hybrid_end'] != HYBRID_END
            or len(hybrid) != hybrid_size or q['x_force_previous'] != 0xAA00
            or q['x_force_apply'] != 0xAA03
            or not q['ab_certified_setup_end'] <= q['x_preflight'] < 0xAA00):
        raise ValueError('certified enemy allocation or external entry differs')
    if s['t_prepare_gate'] != 0xE900 or s['t_irq.commit'] != 0xEA39:
        raise ValueError('AA admission entry differs')
    admission_address = s['t_irq.commit']-3
    admission_at = kernel_at+admission_address-s['t_prepare_gate']
    context = bytes.fromhex('7cb720057dfe023814cd154a')
    if parent[admission_at-6:admission_at+6] != context:
        raise ValueError('AA ready-picture comparison bytes differ')
    rom = bytearray(parent)
    rom[hybrid_at:hybrid_at+hybrid_size] = hybrid
    rom[admission_at] = 1
    different = [i for i,(a,b) in enumerate(zip(parent,rom)) if a != b]
    if (len(rom) != len(parent) or admission_at not in different
            or any(i != admission_at and not hybrid_at <= i < hybrid_at+hybrid_size
                   for i in different)):
        raise ValueError('change outside the two declared regions')
    if sha(rom) != SELECTED:
        raise ValueError('maintained build differs from selected AB: ' + sha(rom))
    patches = [patch_record(hybrid_at, parent[hybrid_at:hybrid_at+hybrid_size],
        hybrid, bank=HYBRID_BANK, cpu_start=HYBRID_START, cpu_end_exclusive=HYBRID_END),
        patch_record(admission_at, parent[admission_at:admission_at+1],
            bytes((1,)), bank=KERNEL_BANK, ram_address=admission_address,
            instruction='CP 2 -> CP 1', before='02', after='01')]
    for name in list(s):
        if name.startswith(HYBRID_PREFIXES):
            del s[name]
    s.update({n:v for n,v in q.items() if n.startswith(('x_', 'ab_'))})
    (out/'presentation.sym').write_text('\n'.join(
        f'{n}: EQU 0x{v:08X}' for n,v in s.items())+'\n')
    world = bytes(rom[world_at:world_at+WORLD_SIZE])
    kernel = bytes(rom[kernel_at:kernel_at+kernel_size])
    (out/'world.bin').write_bytes(world)
    (out/'kernel.bin').write_bytes(kernel)
    (out/'geometry').symlink_to((base/'geometry').resolve(), target_is_directory=True)
    # Preserve logical asset ordering: bank115 is a supplemental image, not a
    # new logical template bank. The contact arena also binds its full image.
    assets = out/'template-assets'
    assets.mkdir()
    exported_banks = sorted(set(meta['template_assets']['physical_banks']) | {KERNEL_BANK})
    bank_images = {}
    for bank in exported_banks:
        name = f'assets-{bank:03d}.bin'
        data = bytes(rom[bank*16384:(bank+1)*16384])
        (assets/name).write_bytes(data)
        bank_images['template-assets/'+name] = sha(data)
        for section in ('template_assets', 'static_presentation'):
            if name in meta[section]['files']:
                meta[section]['files'][name] = sha(data)
    for row in meta['contact14']['arena']:
        bank = row['bank']
        row['packed_sha256'] = sha(rom[bank*16384:(bank+1)*16384])
    for key in ('coherent_x', 'native_lanes'):
        for row in meta[key]['auxiliary_code']:
            at = offset(row['bank'],row['rom_address'])
            row['sha256'] = sha(rom[at:at+row['size']])
    meta['world_x']['code_sha256'] = sha(world)
    meta['native_lanes']['hybrid_code'] = dict(bank=HYBRID_BANK,
        rom_address=HYBRID_START, size=hybrid_size, sha256=sha(hybrid))
    meta['fixed_clock'].update(ram_code_sha256=sha(kernel),
        minimum_commit_interval_vblanks=1)
    commit = subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip()
    dirty = bool(subprocess.check_output(['git','status','--porcelain'], cwd=ROOT, text=True).strip())
    scope = 'Verified AA plus source-built certified enemy selection and first-safe-VBlank admission; source clock, coherent snapshots, original graphics/input/audio are preserved.'
    meta.update(version='ready-presentation-ab-diagnostic', source_commit=commit,
        source_dirty=dirty, source_files=files, complete_source=dict(commit=commit,
        working_tree_dirty=dirty, files=files, scope=scope),
        assembler_sha256=sha(Path(assembler).read_bytes()))
    meta['ready_presentation'] = dict(parent_rom_sha256=PARENT,
        parent_build_json_sha256=sha(original_meta), parent_symbols_sha256=PARENT_SYMBOLS,
        parent_source_closure_sha256=PARENT_SOURCES, parent_source_files=147,
        complete_source_files=151, patches=patches, exact_different_bytes=len(different),
        minimum_commit_interval_vblanks=1, new_ram_bytes=0, new_vram_bytes=0,
        hybrid_rom_half_open=[HYBRID_START,HYBRID_END],
        fixed_hybrid_entries=[HYBRID_START,0xAA00,0xAA03],
        binary_files={n:sha((out/n).read_bytes()) for n in
            ('hybrid.bin','world.bin','kernel.bin','presentation.sym')},
        exported_bank_images=bank_images,
        validation_producers={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in validators},
        scope=scope+' This build is not owner-fluidity or hardware acceptance.')
    name = 'frostbite-ready-presentation-ab.rom'
    (out/name).write_bytes(rom)
    meta['rom'].update(filename=name, size=len(rom), sha256=sha(rom))
    if ((base/'build.json').read_bytes() != original_meta
            or parent_path.read_bytes() != parent
            or sha((base/'presentation.sym').read_bytes()) != PARENT_SYMBOLS):
        raise ValueError('AA parent changed during build')
    if any(sha((ROOT/n).read_bytes()) != h for n,h in files.items()):
        raise ValueError('maintained source changed during build')
    (out/'build.json').write_text(json.dumps(meta, indent=2)+'\n')
    print(dict(rom_sha256=sha(rom), source_commit=commit, source_dirty=dirty,
        source_files=len(files), changed_bytes=len(different),
        minimum_commit_interval_vblanks=1))
    return meta


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--source', type=Path,
        help='explicit maintained assembly path for isolated draft validation')
    args = parser.parse_args()
    build(args.base, args.out, args.source)
