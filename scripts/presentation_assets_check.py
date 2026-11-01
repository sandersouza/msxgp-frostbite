"""Audit general source graphics and finite SCREEN2 transaction resources."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from environment import ROOT
from graphics_mapping import map_frame
from original_graphics import SOURCE_SHA256
from presentation_assets import compile_assets, pack_frame
from presentation_model import describe, pixels
from presentation_palette import HELPERS as PALETTE_FILES, audit_palette
from presentation_records import normalize_frame, parse_records
from presentation_source_check import CHECK_FILES as SOURCE_FILES, audit_capture, read_blob
from reference_provenance import audit_manifest, snapshot_paths
from reference_traces import private_output

HELPERS = tuple(dict.fromkeys((*SOURCE_FILES, *PALETTE_FILES, 'scripts/presentation_model.py',
    'scripts/presentation_assets.py', 'scripts/presentation_assets_check.py',
    'references/presentation-assets-config.json', 'references/presentation-source-result.json')))


def sha(data): return hashlib.sha256(data).hexdigest()


def compare_scene(rom, ram, expected):
    if len(expected) != 33600: raise ValueError('complete actual160x210 original raster required')
    saved = bytes(ram); actual = pixels(rom, describe(rom, {'ram': ram}))
    if bytes(ram) != saved: raise ValueError('source compositor changed canonical RAM')
    count = sum(a != b for a, b in zip(expected, actual))
    if count: raise ValueError(f'general compositor differs at{count} source pixel(s)')
    return {'pixels': actual, 'source_sha256': sha(expected), 'ram_sha256': sha(saved), 'different_pixels': count}


def check(config_path, out):
    producer = snapshot_paths(HELPERS); config_path = Path(config_path)
    config = json.loads(read_blob(config_path, producer['utility_fingerprints']['references/presentation-assets-config.json']))
    summary = json.loads((ROOT / config['source_summary']).read_text())
    receipt = json.loads(read_blob(ROOT / config['source_receipt'], summary['private_sha256']))
    audit_manifest(receipt['checker_producer'], SOURCE_FILES)
    if receipt['checker_producer'] != summary['checker_producer']: raise ValueError('source receipt producer differs from approved summary')
    source = json.loads((ROOT / config['source_config']).read_text()); backend = ROOT / source['backend']
    palette_root = ROOT / config['palette']; palette = audit_palette(palette_root)
    out = private_output(out); out.mkdir(parents=True, exist_ok=False)
    rom = (ROOT / 'references/roms/frostbite.bin').read_bytes()
    if sha(rom) != SOURCE_SHA256: raise ValueError('original ROM identity differs')
    assets = compile_assets(rom, out / 'assets', measured_palette=palette)
    roots = []
    for name in ('fixtures', 'cold_route'):
        root = ROOT / source[name][0]; expected = receipt['groups'][name]['repeats'][0]['report_sha256']
        read_blob(root / 'report.json', expected); audited = audit_capture(root, backend, name == 'fixtures', name == 'cold_route')
        if audited['report_sha256'] != expected: raise ValueError('source capture changed while auditing')
        roots.append((root, name))
    windows = receipt['groups']['natural_windows']['windows']; root = ROOT / source['windows'][0]
    for window in windows:
        directory = root / f'{window["route"]}-{window["event"]}'
        read_blob(directory / 'report.json', window['report_sha256']); audited = audit_capture(directory, backend)
        if audited['report_sha256'] != window['report_sha256']: raise ValueError('source window changed while auditing')
        roots.append((directory, 'natural_window'))
    rows = []; maxima = {key: 0 for key in ('prepare_bytes', 'commit_bytes', 'new_tiles', 'sprite_patterns_bytes', 'sprites_per_line')}
    tile_max = [0, 0, 0]; families = {}; startup = 0
    for root, family in roots:
        cache = None
        for batch in sorted(root.glob('batch-*')):
            for record in parse_records((batch / 'records.bin').read_bytes()):
                for frame in record['frames']:
                    if frame['scanlines'] not in (262, 263): startup += 1; continue
                    compared = compare_scene(rom, record['before']['ram'], normalize_frame(frame))
                    mapped = map_frame(compared.pop('pixels'), palette); packed = pack_frame(mapped, cache); cache = packed['cache']
                    transfers = b''.join(struct.pack('<HBH', p['address'], p['phase'] == 'commit', len(p['data'])) + p['data'] for p in packed['uploads'])
                    metrics = {key: packed[key] for key in maxima}
                    for key, value in metrics.items(): maxima[key] = max(maxima[key], value)
                    tile_max = [max(a, b) for a, b in zip(tile_max, packed['tiles_per_bank'])]
                    families[family] = families.get(family, 0) + 1
                    rows.append({'root': str(root.relative_to(ROOT)), 'batch': batch.name, 'index': record['index'],
                                 **compared, 'mapped_sha256': sha(mapped), 'transfers_sha256': sha(transfers), **metrics})
                    if len(rows) % 100 == 0: print(json.dumps({'frames': len(rows), 'maxima': maxima}), flush=True)
    if families != {'fixtures': 1690, 'cold_route': 31, 'natural_window': 394} or startup != 7:
        raise ValueError('complete approved source domain was not checked')
    if snapshot_paths(HELPERS) != producer: raise ValueError('asset/model producer changed during verification')
    result = {'schema_version': 1, 'producer': producer, 'source_receipt_sha256': summary['private_sha256'],
              'palette_receipt_sha256': sha((palette_root / 'palette.json').read_bytes()), 'source_sha256': sha(rom),
              'assets': assets, 'frames': rows, 'families': families, 'unmapped_startup': startup,
              'maxima': maxima, 'max_tiles_per_bank': tile_max, 'different_source_pixels': 0,
              'scope': 'General source compositor and offline resource/transaction model; no target CPU/RAM/VRAM performance acceptance',
              'pending': ['native RAM/cache allocation', 'live Z80 compositor', 'audio', 'standard-clock integrated timing', 'manual/hardware acceptance']}
    encoded = (json.dumps(result, indent=2) + '\n').encode(); (out / 'assets.json').write_bytes(encoded)
    compact = {key: value for key, value in result.items() if key != 'frames'}
    compact['frames'] = len(rows); compact['private_sha256'] = sha(encoded)
    (out / 'compact.json').write_text(json.dumps(compact, indent=2) + '\n')
    return compact


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'references/presentation-assets-config.json')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(); result = check(args.config, args.out)
    print(json.dumps({key: result[key] for key in ('frames', 'families', 'maxima', 'private_sha256')}))
