"""Cold input-only original routes with explicit progression/terminal predicates."""
import argparse
import hashlib
import json
from pathlib import Path

from environment import ROOT
from floe_routes import HELPERS as FLOE_HELPERS, route_policy
from reference_provenance import audit_manifest, snapshot_paths
from reference_state import decode_state
from reference_traces import NEUTRAL, capture_steps, poweron_capsule, private_output
from stella_floe import digest
from trace_compare import compare_traces, validate_trace

CONFIG = ROOT / 'references/progression-routes.json'
HELPERS = tuple(dict.fromkeys((*FLOE_HELPERS, 'scripts/progression_routes.py', 'references/progression-routes.json')))
KINDS = ('progression', 'exhaustion-restart')


def controller(keys, player):
    if type(keys) is not int or not 0 <= keys <= 255 or keys & 15 != 15 or type(player) is not int or player not in (0, 1):
        raise ValueError('active-player high-nibble directions with neutral inactive input required')
    return keys if player == 0 else (keys >> 4) | 240


def validate_policy(policy):
    if (policy.get('ram_injections') != {} or policy.get('source_hazards_disabled') is not False
            or policy.get('instruction_skipping') is not False or policy.get('raw_input_every_interval') is not True):
        raise ValueError('continuous input-only original policy required')


def assess(points, kind, active_start=0):
    if (kind not in KINDS or not points or not 0 <= active_start < len(points)
            or any(len(p.get('ram', [])) != 128 for p in points)
            or [p.get('index') for p in points] != list(range(len(points)))):
        raise ValueError('complete contiguous original route and known predicate required')
    rows = [p['ram'] for p in points]
    initial = rows[active_start]
    variation = initial[0]
    start_level = 4 if variation & 2 else 0
    if (variation not in range(4) or initial[0x4B] != start_level or initial[0x47] != 0
            or initial[0x4C] != 3 or initial[0x52] != (4 if variation & 1 else 0)
            or initial[0x45] & 128 or initial[0x46] or initial[0x71]):
        raise ValueError('source initialized regular/advanced one/two-player start required')
    turns = []
    for i in range(active_start + 1, len(rows)):
        before, after = rows[i - 1], rows[i]
        if (after[0x47] != before[0x47] and not before[0x46] and not after[0x46]
                and not (before[0x45] | after[0x45]) & 128):
            current = list(before[0x4E:0x54]); current[4] -= 1
            if (before[0x52] == 0 or after[0x48:0x4E] != current
                    or after[0x4E:0x54] != before[0x48:0x4E]):
                raise ValueError('observed natural turn must preserve exact six-byte player records')
            turns.append({'step': i, 'player': after[0x47]})
    result = {'kind': kind, 'variation': variation, 'start_level': start_level,
              'turn_players': [turn['player'] for turn in turns], 'turns': turns}
    if kind == 'progression':
        built = next((i for i in range(active_start, len(rows)) if rows[i][0x4B] == start_level and rows[i][0x4D] == 15), None)
        entered = next((i for i in range((built + 1) if built is not None else len(rows), len(rows))
                        if rows[i][0x4B] == start_level and rows[i][0x71] & 64 and rows[i][0x64] == 0 and rows[i][0x69] == 0), None)
        request = next((i for i in range((entered + 1) if entered is not None else len(rows), len(rows))
                        if rows[i][0x71] & 8 and rows[i][0x65] == 0), None)
        advanced = next((i for i in range((request + 1) if request is not None else len(rows), len(rows))
                         if rows[i][0x4B] == start_level + 1 and rows[i][0x4D] == 255
                         and rows[i][0x64] == 27 and rows[i][0x65] == 0x45
                         and rows[i][0x6A] == 0 and rows[i][0x71] == 0), None)
        if advanced is None or any(r[0x45] & 128 or r[0x46] for r in rows[active_start:advanced + 1]):
            raise ValueError('construction, real entry, completed bonus and active next level required')
        result.update(construction_step=built, entry_step=entered, bonus_complete_step=request, next_level_step=advanced)
    else:
        death = next((i for i in range(active_start, len(rows)) if rows[i][0x71] & 0x90), None)
        terminal = next((i for i in range((death + 1) if death is not None else len(rows), len(rows))
                         if rows[i][0x4C] == rows[i][0x52] == 0 and rows[i][0x46] == 255 and rows[i][0x71] == 0), None)
        restarted = next((i for i in range((terminal + 1) if terminal is not None else len(rows), len(rows))
                          if rows[i][0] == variation and rows[i][0x47] == 0 and rows[i][0x4B] == start_level
                          and rows[i][0x4C] == 3 and rows[i][0x52] == (4 if variation & 1 else 0)
                          and not rows[i][0x45] & 128 and rows[i][0x46] == rows[i][0x71] == 0
                          and rows[i][0x48:0x4B] == [0, 0, 0]), None)
        if restarted is None or variation & 1 and not {0, 1}.issubset(result['turn_players']):
            raise ValueError('natural death, both-empty terminal, both turn directions and actual restart required')
        result.update(death_step=death, terminal_step=terminal, restart_step=restarted)
    return result


def capture(out, kind, variation, stella='stella'):
    if kind not in KINDS or type(variation) is not int or variation not in range(4):
        raise ValueError('declared route and variation0..3 required')
    producer = snapshot_paths(HELPERS)
    config = json.loads(CONFIG.read_text())
    out = private_output(out); out.mkdir(parents=True, exist_ok=False)
    rom = ROOT / 'references/roms/frostbite.bin'
    initial, backend = poweron_capsule(rom, out / 'poweron', config['seed'], config['riot_timer_preset'], stella)
    prep = [NEUTRAL] * config['warmup']
    for _ in range(variation):
        prep += [{**NEUTRAL, 'swchb': 61}] + [NEUTRAL] * config['select_release_intervals']
    prep += [{**NEUTRAL, 'swchb': 62}] + [NEUTRAL] * config['reset_release_intervals']
    policy = {'variation': variation, 'kind': kind, 'ram_injections': {}, 'source_hazards_disabled': False,
              'instruction_skipping': False, 'raw_input_every_interval': True, 'preparation_intervals': len(prep),
              'boundary': 'Unchanged original PCF019; cold power-on and physical Select/Reset/controller pins'}
    validate_policy(policy)
    points, inputs, journal = [], [], []
    current, trace = initial, None

    def segment(samples, label):
        nonlocal current, trace
        trace, current = capture_steps(rom, current, samples, out / label, stella, policy)
        if trace['backend'] != backend:
            raise ValueError('original backend changed during route')
        for point in trace['steps']:
            point['index'] = len(points); points.append(point)
        inputs.extend(samples)
        journal.append({'path': label, 'intervals': len(samples),
                        'trace_sha256': digest(out / label / 'trace.json'), 'final_sha256': digest(out / label / 'final.state')})

    segment(prep, 'prepare')
    active_start = len(points) - 1
    stage, elapsed, assessment, reset_sent = 'build', 0, None, False
    for batch in range(config['maximum_batches']):
        ram = decode_state(current)['ram']
        if kind == 'progression':
            stage, samples = route_policy(ram, stage, elapsed)
            samples = [{**s, 'swcha': controller(s['swcha'], ram[0x47])} for s in samples]
        elif ram[0x46] == 255 and ram[0x4C] == ram[0x52] == 0 and not reset_sent:
            samples = [{**NEUTRAL, 'swchb': 62}] + [NEUTRAL] * config['reset_release_intervals']
            reset_sent = True
        else:
            direction = 0xDF if ram[0x71] == 0 and ram[0x67] == 0 else 255
            samples = [{**NEUTRAL, 'swcha': controller(direction, ram[0x47])}] * 10
        segment(samples, f'body-{batch:04d}'); elapsed += len(samples)
        try:
            assessment = assess(points, kind, active_start)
        except ValueError as error:
            last_error = str(error)
        else:
            break
        if elapsed >= config['maximum_intervals']:
            break
        if batch % 50 == 0:
            print(f'PROGRESSION_ROUTE {kind} v{variation} n={elapsed} stage={stage} level={ram[0x4B]} igloo={ram[0x4D]} x={ram[0x66]} y={ram[0x64]} turn={ram[0x47]} reserves={ram[0x4C]}/{ram[0x52]} flags={ram[0x71]:02x}', flush=True)
    if assessment is None:
        (out / 'failure.json').write_text(json.dumps({'kind': kind, 'variation': variation, 'intervals': elapsed,
            'reason': last_error, 'journal': journal}, indent=2) + '\n')
        raise ValueError(f'bounded original route failed: {last_error}; {out}')
    combined = {**trace, 'initial_sha256': hashlib.sha256(initial).hexdigest(), 'steps': points}
    validate_trace(combined)
    for name, data in (('trace.json', combined), ('inputs.json', inputs), ('journal.json', journal)):
        (out / name).write_text(json.dumps(data, indent=2) + '\n')
    (out / 'initial.state').write_bytes(initial); (out / 'final.state').write_bytes(current)
    if snapshot_paths(HELPERS) != producer:
        raise ValueError('original route producer changed during capture')
    report = {'schema_version': 1, **producer, 'clean_start': True, 'kind': kind, 'variation': variation,
              'backend': backend, 'steps': len(points), 'active_start': active_start,
              'preparation_intervals': len(prep), 'assessment': assessment,
              'files': {name: digest(out / name) for name in ('trace.json', 'inputs.json', 'journal.json', 'initial.state', 'final.state')},
              'scope': 'Original input-only continuous route; native/paced/manual/physical acceptance separate'}
    (out / 'route.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def replay(original, out, stella='stella'):
    producer = snapshot_paths(HELPERS)
    original = Path(original); out = private_output(out); out.mkdir(parents=True, exist_ok=False)
    receipt = json.loads((original / 'route.json').read_text()); audit_manifest(receipt, HELPERS)
    if receipt.get('clean_start') is not True or any(digest(original / n) != sha for n, sha in receipt['files'].items()):
        raise ValueError('clean immutable original route required')
    expected = json.loads((original / 'trace.json').read_text()); validate_trace(expected); validate_policy(expected['policy'])
    inputs = json.loads((original / 'inputs.json').read_text()); journal = json.loads((original / 'journal.json').read_text())
    if len(inputs) != len(expected['steps']) or sum(e['intervals'] for e in journal) != len(inputs):
        raise ValueError('complete original input/restore journal required')
    current, points, cursor, combined = (original / 'initial.state').read_bytes(), [], 0, None
    for i, entry in enumerate(journal):
        path = original / entry['path']
        if digest(path / 'trace.json') != entry['trace_sha256'] or digest(path / 'final.state') != entry['final_sha256']:
            raise ValueError('original restore segment changed')
        samples = inputs[cursor:cursor + entry['intervals']]; cursor += len(samples)
        combined, current = capture_steps(ROOT / 'references/roms/frostbite.bin', current, samples, out / f'segment-{i:04d}', stella, expected['policy'])
        for point in combined['steps']:
            point['index'] = len(points); points.append(point)
    combined = {**combined, 'initial_sha256': expected['initial_sha256'], 'steps': points}
    differences = compare_traces(expected, combined)
    if differences or current != (original / 'final.state').read_bytes():
        raise ValueError('complete original replay differs: ' + str(differences[:3]))
    if assess(points, receipt['kind'], receipt['active_start']) != receipt['assessment'] or snapshot_paths(HELPERS) != producer:
        raise ValueError('source route predicate or producer changed')
    (out / 'trace.json').write_text(json.dumps(combined, indent=2) + '\n'); (out / 'final.state').write_bytes(current)
    report = {**producer, 'complete': True, 'steps': len(points), 'route_sha256': digest(original / 'route.json'),
              'identical_full_cpu_ram_tia_riot_inputs': True, 'final_state_sha256': digest(out / 'final.state')}
    (out / 'replay.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--kind', choices=KINDS)
    p.add_argument('--variation', type=int, choices=range(4))
    p.add_argument('--replay', type=Path)
    args = p.parse_args()
    if not args.replay and (args.kind is None or args.variation is None):
        p.error('capture requires kind and variation')
    result = replay(args.replay, args.out) if args.replay else capture(args.out, args.kind, args.variation)
    print(json.dumps({k: result[k] for k in ('steps', 'assessment') if k in result}, indent=2))
