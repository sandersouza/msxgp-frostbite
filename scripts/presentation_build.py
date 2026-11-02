"""Distinct private native presentation profile; runtime acceptance is pending."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from environment import ROOT, verified_tool
import hazard_build
from hazard_tables import compile_catalog
from native_write_loop import generate
from original_graphics import SOURCE_SHA256
from presentation_assets import compile_assets, memory_layout
from presentation_palette import HELPERS as PALETTE_FILES, audit_palette
from reference_inventory import verified_input
from reference_traces import private_output
from render_build import symbols

VERSION = '0.0.7-presentation'
ROM_BYTES = 4194304
FILES = tuple(dict.fromkeys((*hazard_build.FILES, *PALETTE_FILES, 'scripts/presentation_build.py',
    'scripts/presentation_assets.py', 'scripts/native_write_loop.py', 'src/presentation.asm',
    'src/presentation_cache.asm', 'references/presentation-assets-config.json', 'references/presentation-assets-result.json')))


def bank_layout(contact_banks):
    if type(contact_banks) is not int or not 1 <= contact_banks <= 242:
        raise ValueError('contact banks must fit the fixed256-bank cartridge')
    contacts = list(range(14, 14 + contact_banks))
    return {'resident': 0, 'fragments': 1, 'native': 2, 'contacts': contacts,
            'available_assets': list(range(3, 14)) + list(range(14 + contact_banks, 256))}


def profile():
    ram = memory_layout()
    # Existing native acquisition scratch is retained separately from bus IO.
    ram['regions'].append({'name': 'native_contacts', 'start': 0xC780, 'end': 0xC7A0})
    return {'version': VERSION, 'signature': 'FBP0', 'source_sha256': SOURCE_SHA256,
            'clock_hz': 3579545, 'ram_bytes': 65536, 'vram_bytes': 16384, 'mapper': 'ASCII16',
            'rom_bytes': ROM_BYTES, 'ram': ram, 'runtime_qualified': False,
            'scope': 'New build profile; source/live target equivalence and timing gates remain pending'}


def validate_rom(data):
    errors = []
    if len(data) != ROM_BYTES: errors.append('4MiB ASCII16 cartridge required')
    if data[:2] != b'AB' or data[16:20] != b'FBP0': errors.append('distinct presentation cartridge signature required')
    if len(data) < 20 or not 0x4014 <= int.from_bytes(data[2:4], 'little') < 0x8000 or any(data[4:16]):
        errors.append('resident cartridge entry and zero vectors required')
    return errors


def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(floes, edge, ordinary, shore, aliases, out, *, explore=False):
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip())
    if dirty and not explore: raise ValueError('commit presentation producers before canonical build')
    fingerprints = {name: digest(ROOT / name) for name in FILES}
    original = verified_input(ROOT / 'references/roms/frostbite.bin'); rom = (ROOT / 'references/roms/frostbite.bin').read_bytes()
    config = json.loads((ROOT / 'references/presentation-assets-config.json').read_text())
    measured = audit_palette(ROOT / config['palette'])
    out = private_output(out); out.mkdir(parents=True, exist_ok=False)
    tables = compile_catalog(floes, edge, ordinary, shore, aliases, out / 'tables'); banks = bank_layout(tables['banks'])
    fragments = compile_assets(rom, out / 'assets', measured_palette=measured)
    (out / 'core.inc').write_text(generate(rom, carry_fusion=True)); (out / 'data.bin').write_bytes(rom[0xC00:])
    (out / 'boot_tables.inc').write_text(f'    INCBIN "{out / "assets/fragments.bin"}"\n')
    (out / 'resident_tables.inc').write_text('; Presentation metadata belongs to its explicit profile.\n')
    # Keep original fixed contact indices while reclaiming old synthetic-row banks.
    (out / 'row_banks.inc').write_text('    ORG $8000\n    DS $4000,$FF\n' * 11)
    (out / 'cartridge_padding.inc').write_text('    ORG $8000\n    DS $4000,$FF\n' * (256 - 14 - tables['banks']))
    (out / 'entry.asm').write_text('    DEFINE WITH_HAZARDS\n    DEFINE WITH_FLOES\n    DEFINE WITH_PROGRESSION\n    DEFINE WITH_PRESENTATION\n    INCLUDE "movement.asm"\n')
    artifact = out / f'frostbite-{VERSION}.rom'; assembler = verified_tool('sjasmplus')
    command = [str(assembler), '--nologo', f'--inc={ROOT/"src"}', f'--inc={out}', f'--inc={out/"tables"}',
               f'--raw={artifact}', f'--sym={out/"presentation.sym"}', f'--lst={out/"presentation.lst"}', str(out / 'entry.asm')]
    compiled = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=60)
    (out / 'assembler.log').write_text(compiled.stdout + compiled.stderr)
    if compiled.returncode: raise ValueError('presentation assembler failed: ' + (compiled.stdout + compiled.stderr)[-2500:])
    errors = validate_rom(artifact.read_bytes())
    if errors: raise ValueError('; '.join(errors))
    syms = symbols(out / 'presentation.sym')
    if (subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() != commit
            or any(digest(ROOT / name) != value for name, value in fingerprints.items())
            or verified_input(ROOT / 'references/roms/frostbite.bin') != original):
        raise ValueError('presentation build producer changed during compilation')
    final_dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip())
    if not explore and final_dirty: raise ValueError('canonical presentation checkout changed')
    metadata = {'version': VERSION, 'diagnostic': True, 'runtime_qualified': False, 'profile': profile(),
                'source_commit': commit, 'source_dirty': dirty or final_dirty, 'exploratory': explore,
                'original': original, 'source_files': fingerprints, 'rom': {'filename': artifact.name, 'size': artifact.stat().st_size,
                'sha256': digest(artifact), 'mapper': 'ASCII16'}, 'fragments': fragments, 'tables': tables,
                'banks': {**banks, 'resident_used': syms['resident_end'] - 0x4000, 'native_used': syms['native_end'] - 0x8000,
                          'assets_used': syms['assets_end'] - 0x8000}, 'assembler_sha256': digest(assembler),
                'limitations': 'Private incomplete renderer bootstrap; full graphics/source pixels, live cache, PSG and integrated acceptance are not implemented or qualified. Not a human-testable game delivery.'}
    (out / 'build.json').write_text(json.dumps(metadata, indent=2) + '\n'); return metadata


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('floes', 'edge', 'ordinary', 'shore', 'aliases', 'out'): parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--explore', action='store_true'); args = parser.parse_args()
    result = build(**vars(args)); print(json.dumps({key: result[key] for key in ('version', 'rom', 'runtime_qualified')}))
