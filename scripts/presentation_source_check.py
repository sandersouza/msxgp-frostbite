"""Independently audit persisted original video/audio observations and repeats."""
import argparse
import hashlib
import json
from pathlib import Path

from environment import ROOT
from presentation_records import parse_records, normalize_frame
from presentation_reference import (HELPERS, digest, verify_backend, validate_marker,
                                    validate_equivalence, fixture_batch)
from reference_provenance import audit_manifest, snapshot_paths
from reference_state import decode_state
from reference_traces import STATE_NAME, batch_script, control_commands, validate_checkpoint, private_output

CHECK_FILES = (*HELPERS, 'scripts/presentation_source_check.py', 'scripts/graphics_reference.py',
               'scripts/original_graphics.py', 'scripts/render_model.py',
               'references/progression-config.json', 'references/graphics-result.json',
               'references/presentation-source-config.json')
FACTS = ('intervals', 'physical_frames', 'normalized_frames', 'unmapped_startup_frames', 'audio_writes')


def sha(data): return hashlib.sha256(data).hexdigest()


def read_blob(path, expected):
    path = Path(path)
    if path.is_symlink() or not path.is_file(): raise ValueError(f'missing immutable source artifact: {path}')
    data = path.read_bytes()
    if sha(data) != expected: raise ValueError(f'changed source artifact: {path}')
    return data


def _states(directory, slots):
    directory = directory / 'settings/state'
    if {p.name for p in directory.glob('*.st?')} != {f'{STATE_NAME}.st{i}' for i in slots}:
        raise ValueError('complete exact persisted source checkpoint slots required')
    return {i: (directory / f'{STATE_NAME}.st{i}').read_bytes() for i in slots}


def audit_batch(directory, initial, samples, points, raw_sha, fixture=False, allow_startup=False):
    """Read actual files; success flags and mutually agreeing reports are insufficient."""
    directory = Path(directory); start = decode_state(initial); count = len(samples)
    if not count or count != len(points): raise ValueError('complete sampled source records required')
    raw = read_blob(directory / 'records.bin', raw_sha); records = parse_records(raw)
    if len(records) != count: raise ValueError('source stream count differs from requested samples')
    validate_marker((directory / 'observed/stella.log').read_text(), count)
    slots = set(range(count)) | ({9} if fixture else set())
    plain = _states(directory / 'plain', slots); observed = _states(directory / 'observed', slots)
    if fixture:
        scripts = {'plain': fixture_batch(samples, False), 'observed': fixture_batch(samples, True)}
        if plain[9] != observed[9]: raise ValueError('controlled restore baselines differ')
    else:
        commands = ['base dec', 'loadState 0']
        for slot, sample in enumerate(samples): commands += control_commands(sample) + ['presentationProbe', f'saveState {slot}']
        scripts = {'plain': batch_script(samples), 'observed': '\n'.join(commands + ['exitRom', ''])}
    for name, script in scripts.items():
        if (directory / name / 'settings/autoexec.script').read_text() != script:
            raise ValueError('persisted source input/restore script differs from requested journal')
    facts = dict.fromkeys(FACTS, 0); offset = int(directory.name[6:]); previous = start
    for slot, (record, sample, point) in enumerate(zip(records, samples, points)):
        after = decode_state(plain[slot]); before = {**start, 'ram': list(sample['ram'])} if fixture else previous
        validate_equivalence([record], before, [after], [plain[slot]], [observed[slot]])
        validate_checkpoint(after, sample['input'] if fixture else sample)
        if (record['source_frame'] != before['tia']['frame']['total'] or record['after_frame'] != after['tia']['frame']['total']
                or record['cycles'] != after['cycles'] - before['cycles']
                or sha(observed[slot]) != point['state_sha256'] or len(record['audio']) != point['audio_writes']):
            raise ValueError('source timing/frame/event/capsule receipt differs from actual evidence')
        if fixture:
            ram_hash = sha(bytes(sample['ram']))
            if point['name'] != sample['name'] or point['requested_ram_sha256'] != ram_hash or point['before_ram_sha256'] != ram_hash:
                raise ValueError('controlled requested RAM differs from observed source snapshot')
            if len(record['frames']) != 1: raise ValueError('one complete frame required per controlled fixture')
        else:
            if point['input'] != sample or point['index'] != offset + slot:
                raise ValueError('complete ordered natural input receipt required')
        for frame in record['frames']:
            if (allow_startup and record['source_frame'] == 1 and record['cycles'] == 142059
                    and frame['scanlines'] in (310, 10) and len(record['frames']) == 7):
                facts['unmapped_startup_frames'] += 1
            else:
                raster = normalize_frame(frame); facts['normalized_frames'] += 1
                if fixture:
                    read_blob(directory.parent / f'{offset + slot:04d}-{sample["name"]}.tia', point['raster_sha256'])
                    if sha(raster) != point['raster_sha256']:
                        raise ValueError('derived raster differs from the actual completed original frame')
        facts['intervals'] += 1; facts['physical_frames'] += len(record['frames']); facts['audio_writes'] += len(record['audio'])
        previous = after
    return facts


def audit_capture(root, backend, fixture=False, allow_startup=False):
    root = Path(root); report = json.loads((root / 'report.json').read_text())
    audit_manifest(report['producer'], HELPERS)
    if report['backend'] != verify_backend(backend): raise ValueError('capture backend differs from current immutable executable/patch')
    initial = read_blob(root / 'initial.state', report['initial_sha256'])
    points = report['points']; size = 9 if fixture else 10
    if not points or len(points) > 5000 or [j['offset'] for j in report['journals']] != list(range(0, len(points), size)):
        raise ValueError('complete bounded contiguous source batch journals required')
    if fixture:
        samples = json.loads(read_blob(root / 'fixtures.json', report['fixture_sha256']))
    else: samples = [p['input'] for p in points]
    if len(samples) != len(points): raise ValueError('sample/record count differs')
    total = dict.fromkeys(FACTS, 0); current = initial
    for journal in report['journals']:
        offset = journal['offset']; count = min(size, len(points) - offset); directory = root / f'batch-{offset:05d}'
        if journal['count'] != count: raise ValueError('source batch count differs from journal')
        batch = audit_batch(directory, current, samples[offset:offset + count], points[offset:offset + count],
                            journal['records_sha256'], fixture, allow_startup)
        for key in FACTS: total[key] += batch[key]
        if fixture:
            baseline = (directory / f'plain/settings/state/{STATE_NAME}.st9').read_bytes()
            if sha(baseline) != journal['restored_sha256']: raise ValueError('controlled restore checkpoint changed')
        else:
            if sha(current) != journal['restored_sha256']: raise ValueError('natural restore chain changed')
            current = (directory / f'observed/settings/state/{STATE_NAME}.st{count - 1}').read_bytes()
        for name in ('plain', 'observed'):
            # Every staged original copy is checked too; raw ROMs remain ignored.
            read_blob(directory / name / 'frostbite.bin', 'cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834')
    if not fixture:
        if read_blob(root / 'final.state', report['final_sha256']) != current: raise ValueError('final capsule differs from actual source chain')
    return {'facts': total, 'report_sha256': digest(root / 'report.json'), 'producer': report['producer']}


def compare_capture(first, second):
    first, second = Path(first), Path(second)
    if (first / 'report.json').read_bytes() != (second / 'report.json').read_bytes():
        raise ValueError('independent complete source capture reports differ')
    for name in ('initial.state', 'final.state', 'fixtures.json'):
        if (first / name).exists() and (first / name).read_bytes() != (second / name).read_bytes():
            raise ValueError('independent original input/final state artifacts differ')
    a = sorted(first.glob('batch-*')); b = sorted(second.glob('batch-*'))
    if [p.name for p in a] != [p.name for p in b]: raise ValueError('independent original batch sets differ')
    for x, y in zip(a, b):
        if (x / 'records.bin').read_bytes() != (y / 'records.bin').read_bytes():
            raise ValueError('independent raw original raster/audio streams differ')


def frozen_window(root, trace_path, start, count, expected_sha=None):
    """Cross-journal frozen comparison covers every source register/RAM/input."""
    trace_path = Path(trace_path); trace = json.loads(trace_path.read_text()); policy = trace['policy']
    if expected_sha is not None: read_blob(trace_path, expected_sha)
    if (policy.get('ram_injections') != {} or policy.get('source_hazards_disabled') is not False
            or policy.get('instruction_skipping') is not False or policy.get('raw_input_every_interval') is not True):
        raise ValueError('frozen source window must come from an input-only route')
    root = Path(root); report = json.loads((root / 'report.json').read_text())
    points = trace['steps']; selected = points[start:start + count]
    if start < 1 or len(selected) != count or len(report['points']) != count:
        raise ValueError('complete bounded frozen window required')
    if (root / 'initial.state').read_bytes() != bytes.fromhex(points[start - 1]['state_bytes']):
        raise ValueError('window restore capsule differs from frozen original route')
    for directory in sorted(root.glob('batch-*')):
        offset = int(directory.name[6:])
        for record in parse_records((directory / 'records.bin').read_bytes()):
            index = offset + record['index']; frozen = selected[index]
            expected = {'registers': {k: frozen['cpu'][k] for k in ('a', 'x', 'y', 'p', 'sp')}, 'ram': frozen['ram']}
            if record['after'] != expected or report['points'][index]['input'] != frozen['input']:
                raise ValueError('observed source CPU/all RAM/raw pins differ from frozen route')


def controlled_domains(root):
    fixtures = json.loads((Path(root) / 'fixtures.json').read_text())
    if len(fixtures) != 1690 or len({f['name'] for f in fixtures}) != len(fixtures):
        raise ValueError('complete unique1690-fixture domain required')
    domains = {}
    for family, address, expected in (('temperature', 0xE5, 256), ('footer', 0xC6, 256), ('daynight', 0xCB, 256),
                                      ('reserves', 0xCC, 10), ('bear-coordinate', 0xE8, 160), ('player-coordinate', 0xE6, 160)):
        rows = [f for f in fixtures if f['family'] == family]; values = sorted(f['ram'][address - 128] for f in rows)
        if values != list(range(expected)): raise ValueError(f'incomplete literal original domain: {family}')
        domains[family] = expected
    scores = [f for f in fixtures if f['family'] == 'score']
    score_pairs = {(int(''.join(f'{v:02x}' for v in f['ram'][0x48:0x4B]), 10), f['ram'][0x47]) for f in scores}
    if len(scores) != 16 or score_pairs != {(score, player) for score in (0, 9, 10, 99, 100, 99999, 100000, 999999) for player in (0, 1)}:
        raise ValueError('complete six-digit BCD/player HUD source fixtures required')
    blink = [f for f in fixtures if f['family'] == 'attract']
    if len(blink) != 32 or {(f['ram'][1], f['ram'][0x47]) for f in blink} != {(phase, player) for phase in range(16) for player in (0, 1)}:
        raise ValueError('complete source blink and both-player fixtures required')
    domains.update(score_player_pairs=16, attract_player_pairs=32)
    return fixtures, domains


def compare_ale(root, graphics):
    """Retain, bound and adjudicate every cross-backend discrepancy explicitly."""
    from graphics_reference import validate_files
    graphics = Path(graphics); public = json.loads((ROOT / 'references/graphics-result.json').read_text())
    read_blob(graphics / 'evidence.json', public['private_sha256'])
    points = json.loads((graphics / 'run-0/points.json').read_text()); validate_files(graphics / 'run-0', points)
    if len(points) != 544: raise ValueError('complete frozen ALE graphics comparison required')
    fixtures = json.loads((Path(root) / 'fixtures.json').read_text()); differences = []
    for index, point in enumerate(points):
        name = point['name']; stem = f'{index:04d}-{name}'
        if fixtures[index]['name'] != name or bytes(fixtures[index]['ram']) != (graphics / f'run-0/{stem}.before-ram').read_bytes():
            raise ValueError('cross-backend original RAM fixtures differ')
        actual = (Path(root) / f'{stem}.tia').read_bytes(); expected = (graphics / f'run-0/{stem}.tia').read_bytes()
        wrong = [(i % 160, i // 160) for i, (a, b) in enumerate(zip(actual, expected)) if a != b]
        if wrong:
            differences.append({'name': name, 'different_pixels': len(wrong),
                                'bounds': [min(x for x, y in wrong), min(y for x, y in wrong), max(x for x, y in wrong), max(y for x, y in wrong)]})
    adjudicated = [{'name': 'edge-0', 'different_pixels': 109, 'bounds': [8, 58, 21, 73]},
                   {'name': 'edge-1', 'different_pixels': 123, 'bounds': [8, 58, 22, 73]},
                   {'name': 'edge-7', 'different_pixels': 126, 'bounds': [13, 58, 28, 73]},
                   {'name': 'edge-8', 'different_pixels': 126, 'bounds': [14, 58, 29, 73]}]
    if differences != adjudicated: raise ValueError('new/unadjudicated original backend disagreement')
    return {'cases': 544, 'exact_matches': 540, 'disagreements': differences,
            'authority': 'Pinned Stella7 for rendering/contact geometry; no real-Atari hardware verdict inferred'}


def bear_placement(root, fixtures):
    from original_graphics import catalog
    rom = (ROOT / 'references/roms/frostbite.bin').read_bytes(); glyph = catalog(rom)['assets']['bear-0-0']['pixels']; count = 0
    for index, fixture in enumerate(fixtures):
        if fixture['family'] != 'bear-coordinate': continue
        x = fixture['ram'][0x68]; pixels = (Path(root) / f'{index:04d}-{fixture["name"]}.tia').read_bytes()
        origin = (x + (6 if x < 15 else 1)) % 160; top = 58 + (x >= 150)
        for row in range(19):
            for column in range(160):
                dx = (column - origin) % 160
                expected = column >= 8 and dx < 16 and bool(glyph[row * 16 + dx])
                if (pixels[(top + row) * 160 + column] == 4) != expected:
                    raise ValueError('measured source bear position/glyph formula differs from raw original raster')
        count += 1
    if count != 160: raise ValueError('all160 actual bear-coordinate fixtures required')
    return {'cases': count, 'origin_x': '(E8+(6 if E8<15 else1)) mod160', 'origin_y': '58+(E8>=150)',
            'limits': 'Controlled pose0/reflection0/day bear; not the complete presentation model'}


def check(config_path, out):
    producer = snapshot_paths(CHECK_FILES); config_path = Path(config_path)
    config_bytes = config_path.read_bytes(); config = json.loads(config_bytes)
    if sha(config_bytes) != producer['utility_fingerprints']['references/presentation-source-config.json']:
        raise ValueError('source check config differs from committed input')
    backend = ROOT / config['backend']; identity = verify_backend(backend)
    result = {'schema_version': 1, 'checker_producer': producer, 'backend': identity,
              'source_sha256': 'cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834',
              'source_clock': {'numerator': 3579545, 'divisor': 3}, 'groups': {}}
    for kind in ('fixtures', 'cold_route'):
        a, b = (ROOT / p for p in config[kind]); compare_capture(a, b)
        runs = [audit_capture(p, backend, kind == 'fixtures', kind == 'cold_route') for p in (a, b)]
        result['groups'][kind] = {'repeats': runs}
        print(f'{kind}: {runs[0]["facts"]}, exact independent repeat', flush=True)
    fixture_root = ROOT / config['fixtures'][0]
    fixtures, domains = controlled_domains(fixture_root); result['controlled_domains'] = domains
    result['cross_backend'] = compare_ale(fixture_root, ROOT / config['graphics'])
    result['bear_placement'] = bear_placement(fixture_root, fixtures)
    original_config = json.loads((ROOT / 'references/progression-config.json').read_text())
    v0 = ROOT / original_config['routes']['progression-v0']['source'] / 'trace.json'
    for directory in config['cold_route']: frozen_window(ROOT / directory, v0, 1, 32)
    a, b = (ROOT / p for p in config['windows'])
    rows = json.loads((a / 'windows.json').read_text())
    if rows != json.loads((b / 'windows.json').read_text()) or len(rows) != 45:
        raise ValueError('complete repeated45-window original manifest required')
    totals = dict.fromkeys(FACTS, 0); windows = []
    for window in rows:
        name = f'{window["route"]}-{window["event"]}'; compare_capture(a / name, b / name)
        trace = ROOT / original_config['routes'][window['route']]['source'] / 'trace.json'
        audits = []
        for root in (a, b):
            read_blob(root / name / 'report.json', window['report_sha256'])
            audits.append(audit_capture(root / name, backend))
            frozen_window(root / name, trace, window['start'], window['count'], window['frozen_source_trace_sha256'])
        if audits[0]['facts'] != audits[1]['facts']: raise ValueError('independent source window facts differ')
        for key in FACTS: totals[key] += audits[0]['facts'][key]
        windows.append({**window, 'source_producer': audits[0]['producer']})
    result['groups']['natural_windows'] = {'windows': windows, 'facts': totals, 'independent_repeats': 2}
    result['limits'] = ['Source evidence only; live native graphics/HUD/PSG, integrated timing and ROM acceptance remain pending',
                        'Window observations overlap; their sum is not a count of unique whole-game intervals',
                        'Seven seeded startup physical frames retained raw and explicitly excluded from mapped rendering proof',
                        'Controlled complete128RAM injections do not prove natural reachability; invalid BCD bytes are literal source-domain probes',
                        'Four old-ALE left-edge bear disagreements explicitly retained; pinned Stella7 selected consistently with contact authority',
                        'No manual visual/listening, real Atari or physical MSX verdict inferred']
    if snapshot_paths(CHECK_FILES) != producer or verify_backend(backend) != identity:
        raise ValueError('source checker/backend changed during verification')
    out = private_output(out); out.mkdir(parents=True, exist_ok=False)
    private = (json.dumps(result, indent=2) + '\n').encode(); (out / 'source.json').write_bytes(private)
    compact = {k: result[k] for k in ('schema_version', 'checker_producer', 'source_sha256', 'source_clock', 'controlled_domains', 'cross_backend', 'bear_placement', 'limits')}
    compact['backend'] = {k: identity[k] for k in ('revision', 'producer_commit', 'patch_sha256', 'binary_sha256', 'sound_core')}
    compact['private_sha256'] = sha(private)
    compact['groups'] = {kind: {'facts_per_repeat': result['groups'][kind]['repeats'][0]['facts'], 'independent_repeats': 2,
                               'report_sha256': result['groups'][kind]['repeats'][0]['report_sha256']} for kind in ('fixtures', 'cold_route')}
    compact['groups']['natural_windows'] = {'windows': 45, 'observations_per_repeat': totals, 'independent_repeats': 2,
                                            'manifest_sha256': digest(a / 'windows.json')}
    (out / 'compact.json').write_text(json.dumps(compact, indent=2) + '\n')
    return compact


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'references/presentation-source-config.json')
    parser.add_argument('--out', type=Path, required=True)
    arguments = parser.parse_args(); print(json.dumps(check(arguments.config, arguments.out), indent=2))
