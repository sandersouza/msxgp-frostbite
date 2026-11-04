"""Reproduce sealed Q-E with public producers and locally generated canonical F.

Example (all outputs are immutable and ignored)::

    python scripts/native_pipeline_build.py \
        --base-f outputs/presentation/performance-canonical-a \
        --out outputs/presentation/canonical-chain-s/reproduction-a

Canonical F itself is produced by public scripts/presentation_build.py --audio
--floes F --edge E --ordinary O --shore S --aliases A --out OUTPUT. Those five
contact catalogs and the supplied original reference ROM remain local generated
inputs, never public source. This entry authenticates F bytes before rebuilding
I/J/K/L/M, contact14, P and Q-E; it never reads historical private producers.
"""
import argparse
import ast
import json
from pathlib import Path
import re
import subprocess

from environment import ROOT
from build_contact14 import build as build_contact14
from build_prepared_ice import build as build_prepared
from presentation_band_spike import sha, verified_bytes
from presentation_inherited_build import build as build_inherited, EXPECTED as INHERITED
from presentation_build import FILES as F_FILES
from render_build import symbols

EXPECTED = {**INHERITED,
    'contact14': '209992bdbbf93ba30729d9cf94b7d8a0f6e1c55ac4c1f8206cecb464aa2e75d8',
    'p': '923219216c217c11b1eeed03d19c80e2c1a6702b369624c03cbda63b8269e0eb',
    'q': '2654da3abdb2fc2624f6485a9104327447e0493f64a864feb56b41212dc5ada9',
}


def source_manifest():
    """Hash complete public producer closure; generated inputs are separate."""
    pending = set(F_FILES) | {
        'scripts/native_pipeline_build.py', 'scripts/presentation_inherited_build.py',
        'scripts/presentation_inherited_tables.py', 'scripts/build_contact14.py',
        'scripts/build_prepared_ice.py', 'src/presentation_contact14.asm',
        'src/presentation_prepared_ice.asm', 'src/presentation_direct_enemy_body.asm',
        'src/presentation_direct_enemy_helpers.asm',
        *(f'src/presentation_inherited_{s}.asm' for s in 'ijkl'),
        'references/tools-lock.json',
    }
    files = {}
    while pending:
        name = pending.pop()
        if name in files:
            continue
        path = ROOT / name
        files[name] = sha(path.read_bytes())
        if path.suffix == '.py':
            tree = ast.parse(path.read_text())
            modules = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    modules.extend(alias.name.split('.')[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    modules.append(node.module.split('.')[0])
            for module in modules:
                local = f'scripts/{module}.py'
                if (ROOT / local).is_file():
                    pending.add(local)
        elif path.suffix == '.asm':
            for include in re.findall(r'^\s*INCLUDE\s+"([^"]+)"', path.read_text(), re.M | re.I):
                local = Path('src') / include
                if (ROOT / local).is_file():
                    pending.add(str(local))
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    status = subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True)
    return dict(commit=head, working_tree_dirty=bool(status.strip()), files=dict(sorted(files.items())),
                scope='Corresponding public producer closure at these exact file hashes. Commit alone is insufficient when working_tree_dirty is true.')


def build(base, out):
    base, out = Path(base).resolve(), Path(out).resolve()
    if out.exists():
        raise ValueError('immutable output directory already exists')
    required_parent = (ROOT / 'outputs/presentation/canonical-chain-s').resolve()
    if required_parent not in out.parents:
        raise ValueError('new chain output must be under outputs/presentation/canonical-chain-s/')
    input_meta = json.loads((base / 'build.json').read_text())
    original = verified_bytes(base / input_meta['rom']['filename'], EXPECTED['f'])
    manifest = source_manifest()
    out.mkdir(parents=True)
    parent = base
    for stage in 'ijklm':
        build_inherited(stage, parent, out / stage, i_symbols=out / 'i/patch.sym')
        parent = out / stage
    build_contact14(out / 'contact14', base=parent, allocation=out / 'i/tables.json')
    build_prepared(out / 'p', base=out / 'contact14', allocation=out / 'i/tables.json')
    build_prepared(out / 'q', base=out / 'contact14', allocation=out / 'i/tables.json',
                   i_symbols=out / 'i/patch.sym', direct_enemy=True, lazy_enemy=True)
    generated = {}
    for stage in ('i', 'j', 'k', 'l', 'm', 'contact14', 'p', 'q'):
        meta_path = out / stage / 'build.json'
        meta = json.loads(meta_path.read_text())
        data = verified_bytes(out / stage / meta['rom']['filename'], EXPECTED[stage])
        generated[stage] = dict(rom_sha256=sha(data), filename=meta['rom']['filename'])
        # Do not imply historical source fields represent corresponding source.
        meta['ancestry_source'] = {key: meta.pop(key) for key in ('source', 'source_commit', 'source_files', 'source_dirty', 'exploratory') if key in meta}
        meta.update(source_commit=manifest['commit'], source_files=manifest['files'],
                    source_dirty=manifest['working_tree_dirty'], exploratory=True)
        meta['complete_source'] = manifest
        meta_path.write_text(json.dumps(meta, indent=2)+'\n')
    # The raw floe ID zero is valid data and remains byte-for-byte intact.
    s = symbols(base / 'presentation.sym')
    address = s['p_template_floe_patterns_offset']
    bank = address // 16384
    at = (bank+3 if bank < 11 else bank+242)*16384+address % 16384
    q_meta = json.loads((out / 'q/build.json').read_text())
    q_rom = (out / 'q' / q_meta['rom']['filename']).read_bytes()
    raw_zero = q_rom[at:at+8] == original[at:at+8]
    if not raw_zero:
        raise ValueError('raw floe zero namespace was changed')
    # Inputs derived from the supplied reference are deliberately not sources.
    generated_inputs = {str(p.relative_to(base)): sha(p.read_bytes()) for p in sorted((base / 'tables').glob('*')) if p.is_file()}
    generated_inputs['presentation.sym'] = sha((base / 'presentation.sym').read_bytes())
    result = dict(rom_sha256=EXPECTED['q'], stages=generated, complete_source=manifest,
                  ancestry=dict(canonical_f_rom_sha256=EXPECTED['f'], metadata_sha256=sha((base / 'build.json').read_bytes()),
                                metadata=input_meta),
                  generated_local_inputs=generated_inputs, raw_floe_zero_preserved=raw_zero,
                  scope='Exact byte reproduction only; no timing, emulator, owner, or physical-hardware acceptance implied.')
    (out / 'chain.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-f', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = build(args.base_f, args.out)
    print(json.dumps(dict(rom_sha256=result['rom_sha256'], complete_source=result['complete_source']['commit'])))
