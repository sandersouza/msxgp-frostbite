"""Repeated measured RGB calibration; all raw pixels and states stay local."""
import argparse
import hashlib
import json
from pathlib import Path

from environment import ROOT
from original_graphics import SOURCE_SHA256
from reference_provenance import audit_manifest, snapshot_paths
from reference_traces import private_output

HELPERS = ('scripts/presentation_palette.py', 'scripts/environment.py', 'scripts/original_graphics.py',
           'scripts/reference_provenance.py', 'scripts/reference_inventory.py', 'scripts/reference_traces.py',
           'scripts/reference_state.py', 'scripts/source_timing.py', 'scripts/trace_compare.py')
ALE_SHA256 = '34ac656b5d24fc5b4e3978c9628b958f95a620ab9cf10e159a7198a3d5bec8dc'


def sha(data): return hashlib.sha256(data).hexdigest()


def sample_palette(indexed, rgb, requested, before, after):
    if not before or before != after: raise ValueError('RGB observation changed source state')
    if len(indexed) != 33600 or len(rgb) != 100800 or any(code & 1 for code in indexed):
        raise ValueError('complete160x210 indexed/RGB source frame with even color codes required')
    if requested not in indexed: raise ValueError('requested source color was not observed')
    colors = {}
    for offset, code in enumerate(indexed):
        color = tuple(rgb[offset * 3:offset * 3 + 3])
        if code in colors and colors[code] != color: raise ValueError('inconsistent per-pixel measured RGB')
        colors[code] = color
    return colors


def audit_palette(directory):
    directory = Path(directory); report = json.loads((directory / 'palette.json').read_text())
    audit_manifest(report['producer'], HELPERS)
    if report['ale_version'] != '0.12.1' or report['ale_sha256'] != ALE_SHA256 or report['source_sha256'] != SOURCE_SHA256:
        raise ValueError('unreviewed palette backend/original identity')
    if len(report['runs']) != 2: raise ValueError('two complete repeated palette runs required')
    runs = []; results = []
    for repeat, run in enumerate(report['runs']):
        if [p['code'] for p in run] != list(range(0, 256, 2)): raise ValueError('all128 even color samples required')
        colors = {}; hashes = []
        for point in run:
            blobs = {}
            for name in ('indexed.bin', 'rgb.bin', 'before.state', 'after.state', 'input.state'):
                path = directory / f'run-{repeat}' / f'{point["code"]:03d}' / name
                if path.is_symlink(): raise ValueError('palette artifact must be a regular local file')
                blobs[name] = path.read_bytes()
                if sha(blobs[name]) != point['files'][name]: raise ValueError('changed persisted palette artifact')
            measured = sample_palette(blobs['indexed.bin'], blobs['rgb.bin'], point['code'], blobs['before.state'], blobs['after.state'])
            for code, color in measured.items():
                if code in colors and colors[code] != color: raise ValueError('inconsistent measured palette between frames')
                colors[code] = color
            hashes.append(point)
        if set(colors) != set(range(0, 256, 2)): raise ValueError('incomplete measured palette')
        runs.append(colors); results.append(hashes)
    if runs[0] != runs[1] or results[0] != results[1]: raise ValueError('repeated palette pixels/states differ')
    if {str(k): list(v) for k, v in runs[0].items()} != report['palette']:
        raise ValueError('reported palette differs from persisted RGB pixels')
    return runs[0]


def capture_palette(rom_path, directory):
    import ale_py
    import ale_py._ale_py as binary
    producer = snapshot_paths(HELPERS); directory = private_output(directory)
    rom_path = Path(rom_path).resolve(); rom = rom_path.read_bytes()
    if sha(rom) != SOURCE_SHA256 or ale_py.__version__ != '0.12.1' or sha(Path(binary.__file__).read_bytes()) != ALE_SHA256:
        raise ValueError('reviewed original ROM and ALE0.12.1 binary required')
    directory.mkdir(parents=True, exist_ok=False); runs = []; palette = {}
    for repeat in range(2):
        ale = ale_py.ALEInterface(); ale.setInt('random_seed', 1); ale.setInt('frame_skip', 1)
        ale.setFloat('repeat_action_probability', 0); ale.loadROM(str(rom_path))
        for _ in range(20): ale.act(0)
        baseline = ale.cloneSystemState(); run = []
        for code in range(0, 256, 2):
            ale.restoreSystemState(baseline)
            patch = {0xA3: rom[0xD0A], 0xA7: code, 0x91: 0, 0xD4: 32, 0xD8: 1}
            for address, value in patch.items(): ale.setRAM(address & 127, value)
            inputs = ale.cloneSystemState().serialize(); ale.act(0); before = ale.cloneSystemState().serialize()
            indexed = ale.getScreen().tobytes(); rgb = ale.getScreenRGB().tobytes(); after = ale.cloneSystemState().serialize()
            measured = sample_palette(indexed, rgb, code, before, after)
            for key, value in measured.items():
                if key in palette and palette[key] != value: raise ValueError('inconsistent source palette')
                palette[key] = value
            sample = directory / f'run-{repeat}' / f'{code:03d}'; sample.mkdir(parents=True)
            blobs = {'indexed.bin': indexed, 'rgb.bin': rgb, 'before.state': before, 'after.state': after, 'input.state': inputs}
            for name, data in blobs.items(): (sample / name).write_bytes(data)
            run.append({'code': code, 'patch': {str(k): v for k, v in patch.items()}, 'files': {name: sha(data) for name, data in blobs.items()}})
        runs.append(run)
    report = {'schema_version': 1, 'producer': producer, 'ale_version': ale_py.__version__, 'ale_sha256': ALE_SHA256,
              'source_sha256': sha(rom), 'runs': runs, 'palette': palette,
              'method': 'Two independent seeded ALE instances; controlled original row-color injections; complete indexed/RGB pixels and read-only state equality',
              'scope': 'RGB calibration only; Stella7 presentation/CPU authority and native gameplay are unchanged'}
    if snapshot_paths(HELPERS) != producer: raise ValueError('palette producer changed during capture')
    (directory / 'palette.json').write_text(json.dumps(report, indent=2) + '\n')
    audit_palette(directory)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=ROOT / 'references/roms/frostbite.bin')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(); result = capture_palette(args.rom, args.out)
    print(json.dumps({'palette_codes': len(result['palette']), 'producer': result['producer']['tool_source_commit']}))
