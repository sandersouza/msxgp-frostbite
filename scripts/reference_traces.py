#!/usr/bin/env python3
"""Bounded original-ROM Stella captures; complete raw evidence stays ignored."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

from reference_inventory import ROOT, verified_input
from reference_state import decode_state, freeze_poweron
from trace_compare import validate_trace, compare_traces
from reference_provenance import producer_snapshot, verify_snapshot

CONTRACT = 'd55b1aec0d067a4c901a6dcdf81cb8f579685659'
STATE_NAME = 'Frostbite (1983) (Activision)'
NEUTRAL = {'swcha': 255, 'swchb': 63, 'fire': [False, False]}
LOADED_UTILITY_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def verify_fingerprints(expected):
    for path, digest in expected.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != digest:
            raise ValueError(f'capture utility changed during execution: {Path(path).name}')


def control_commands(sample):
    if not isinstance(sample, dict) or set(sample) != {'swcha', 'swchb', 'fire'}:
        raise ValueError('raw SWCHA/SWCHB/two fire states required')
    for name in ('swcha', 'swchb'):
        if type(sample[name]) is not int or not 0 <= sample[name] <= 255:
            raise ValueError('raw controller/console byte outside uint8')
    if not isinstance(sample['fire'], list) or len(sample['fire']) != 2 or any(type(v) is not bool for v in sample['fire']):
        raise ValueError('two explicit boolean fire states required')
    commands = [f'swchb ${sample["swchb"]:02x}']
    for port in range(2):
        for bit, key in enumerate(('Up', 'Down', 'Left', 'Right')):
            level = int(bool(sample['swcha'] & (1 << (bit + (4 if port == 0 else 0)))))
            commands.append(f'joy{port}{key} {level}')
        commands.append(f'joy{port}Fire {int(not sample["fire"][port])}')
    return commands


def batch_script(steps):
    if not isinstance(steps, list) or not 1 <= len(steps) <= 10:
        raise ValueError('one batch requires1–10 explicitly sampled steps/save slots')
    commands = ['base dec', 'loadState 0']
    for slot, sample in enumerate(steps):
        commands += control_commands(sample) + ['runToPc $f019', f'saveState {slot}']
    return '\n'.join(commands + ['exitRom', ''])


def observed_input(state):
    swcha = 0
    fires = []
    for port, controller in enumerate(state['controllers']):
        for bit, level in enumerate(controller['digital'][:4]):
            swcha |= int(level) << (bit + (4 if port == 0 else 0))
        fires.append(not controller['digital'][4])
    return {'swcha': swcha, 'swchb': state['switches'], 'fire': fires}


def validate_checkpoint(state, sample):
    if state['cpu']['pc'] != 0xF019:
        raise ValueError('source checkpoint did not reach PCF019')
    if observed_input(state) != sample:
        raise ValueError('observed electrical controller/console state differs from requested input')


def validate_progress(before, after):
    if after['cycles'] <= before['cycles'] or after['tia']['frame']['total'] < before['tia']['frame']['total']:
        raise ValueError('checkpoint has no fresh forward source execution')


def private_output(path):
    path = Path(path).resolve()
    if path == (ROOT / 'outputs').resolve() or not path.is_relative_to((ROOT / 'outputs').resolve()):
        raise ValueError('raw source captures must stay in a fresh ignored outputs subtree')
    return path


def backend_identity(stella='stella'):
    executable = shutil.which(stella)
    if not executable: raise ValueError('Stella unavailable')
    executable = str(Path(executable).resolve())
    result = subprocess.run([executable, '-help'], capture_output=True, text=True, timeout=10)
    help_text = result.stdout + result.stderr
    if not re.search(r'^Stella version 7\.0$', help_text, re.M) or '-debug' not in help_text:
        raise ValueError('unsupported backend: requires Stella7.0 with Debugger')
    return executable, {'name': 'Stella', 'version': '7.0', 'source_contract': CONTRACT,
                        'binary_sha256': hashlib.sha256(Path(executable).read_bytes()).hexdigest()}


def run_debugger(rom, script, out, initial=None, stella='stella'):
    identity = verified_input(Path(rom))
    out = private_output(out)
    executable, backend = backend_identity(stella)
    if initial is not None: decode_state(initial)
    out.mkdir(parents=True, exist_ok=False)
    settings = out / 'settings'; (settings / 'state').mkdir(parents=True)
    local_rom = out / 'frostbite.bin'; shutil.copyfile(rom, local_rom)
    if hashlib.sha256(local_rom.read_bytes()).hexdigest() != identity['sha256']:
        raise ValueError('canonical input changed while staging')
    if initial is not None:
        (settings / f'state/{STATE_NAME}.st0').write_bytes(initial)
    (settings / 'autoexec.script').write_text(script)
    options = ['-basedir', str(settings), '-video', 'software', '-audio.enabled', '0',
               '-logtoconsole', '1', '-loglevel', '2', '-format', 'NTSC', '-dev.settings', '1',
               '-dev.ramrandom', '0', '-dev.tiarandom', '0', '-dev.cpurandom', '0',
               '-dev.bankrandom', '0', '-dev.tv.jitter', '0', '-dev.tiadriven', '0',
               '-dev.hsrandom', '0', '-dbg.autosave', '0', '-debug', '-exitlauncher', '0']
    env = {**os.environ, 'SDL_VIDEODRIVER': 'dummy', 'SDL_AUDIODRIVER': 'dummy'}
    try:
        process = subprocess.run([executable, *options, str(local_rom)], cwd=out,
                                 env=env, text=True, capture_output=True, timeout=30, check=True)
    except subprocess.TimeoutExpired as error:
        (out / 'failure.txt').write_text('Stella30-second watchdog expired; no acceptance.\n')
        raise ValueError('Stella bounded capture timed out') from error
    log = process.stdout + process.stderr
    (out / 'stella.log').write_text(log)
    if not re.search(r'^Stella 7\.0$', log, re.M) or 'Debugger' not in log:
        raise ValueError('unsupported backend: requires Stella7.0 with Debugger')
    verified_input(Path(rom))
    if hashlib.sha256(Path(executable).read_bytes()).hexdigest() != backend['binary_sha256']:
        raise ValueError('Stella binary changed during capture')
    states = {}
    for slot in range(10):
        path = settings / f'state/{STATE_NAME}.st{slot}'
        if path.exists():
            data = path.read_bytes(); decode_state(data); states[slot] = data
    if not states: raise ValueError('no full source states captured')
    return states, backend


def poweron_capsule(rom, out, seed=1, timer=127, stella='stella'):
    if type(timer) is not int or not 0 <= timer <= 255:
        raise ValueError('RIOT preset must be uint8')
    script = '\n'.join(['base dec', 'reset', *control_commands(NEUTRAL),
                        f'ram $297 ${timer:02x}', 'saveState 0', 'exitRom', ''])
    states, backend = run_debugger(rom, script, out, stella=stella)
    raw = freeze_poweron(states[0], seed)
    decoded = decode_state(raw)
    if any(decoded['ram']) or decoded['riot']['timer'] != timer or decoded['riot']['divider'] != 1024:
        raise ValueError('unexpected power-on RAM/RIOT conditions')
    if observed_input(decoded) != NEUTRAL:
        raise ValueError('power-on inputs not neutral')
    (Path(out) / 'capsule.state').write_bytes(raw)
    return raw, backend


def capture_steps(rom, initial, steps, out, stella='stella', policy=None):
    verified_input(Path(rom))
    start = decode_state(initial)
    if start['cpu']['pc'] not in (0xF000, 0xF019):
        raise ValueError('unexpected initial source PC')
    if not isinstance(steps, list) or not 1 <= len(steps) <= 5000:
        raise ValueError('capture requires1–5000 explicit source steps')
    for sample in steps: control_commands(sample)
    out = private_output(out); out.mkdir(parents=True, exist_ok=False)
    current = initial; points = []; backend = None; previous = start
    for offset in range(0, len(steps), 10):
        batch = steps[offset:offset+10]
        states, current_backend = run_debugger(rom, batch_script(batch), out / f'batch-{offset:05d}',
                                              current, stella)
        if backend is not None and backend != current_backend: raise ValueError('backend changed during capture')
        backend = current_backend
        if set(states) != set(range(len(batch))): raise ValueError('missing/unexpected source checkpoints')
        for slot, sample in enumerate(batch):
            current = states[slot]
            point = decode_state(current); validate_checkpoint(point, sample)
            validate_progress(previous, point); previous = point
            point.update(index=len(points), input=sample, state_bytes=current.hex())
            points.append(point)
    trace = {'schema_version': 2, 'source_sha256': verified_input(Path(rom))['sha256'], 'backend': backend,
             'initial_sha256': hashlib.sha256(initial).hexdigest(),
             'policy': policy or {'boundary': 'PCF019 interval; actual frame/cycle counters retained',
                                 'input_sampling': 'explicit raw pins at every boundary, no sticky-action RNG'},
             'steps': points}
    validate_trace(trace)
    (out / 'trace.json').write_text(json.dumps(trace, indent=2) + '\n')
    (out / 'final.state').write_bytes(current)
    return trace, current


def expand_route(segments):
    if not isinstance(segments, list) or not segments: raise ValueError('nonempty route required')
    result = []
    for segment in segments:
        count = segment['count']
        if type(count) is not int or not 1 <= count <= 200: raise ValueError('route count must be1–200')
        sample = {key: value for key, value in segment.items() if key != 'count'}
        control_commands(sample)
        result.extend(copy.deepcopy(sample) for _ in range(count))
    if len(result) > 1000: raise ValueError('route exceeds1000 intervals')
    return result


def negative_controls(trace):
    results = {}
    for kind in ('coordinate', 'flag', 'collision', 'order', 'input', 'seed'):
        altered = copy.deepcopy(trace)
        if kind == 'coordinate': altered['steps'][-1]['ram'][0x64] ^= 1
        elif kind == 'flag': altered['steps'][-1]['cpu']['p'] ^= 1
        elif kind == 'collision': altered['steps'][-1]['ram'][0x30] ^= 0x80
        elif kind == 'order': altered['steps'][0], altered['steps'][1] = altered['steps'][1], altered['steps'][0]
        elif kind == 'input': altered['steps'][-1]['input']['swcha'] ^= 1
        elif kind == 'seed': altered['policy']['host_seed'] ^= 1
        errors = compare_traces(trace, altered)
        if not errors: raise ValueError(f'negative control {kind} escaped detection')
        results[kind] = errors[:3]
    return results


def selected_player_fixture(raw, player):
    state = decode_state(raw)
    if state['cpu']['pc'] != 0xF019 or state['ram'][0] not in (1, 3) or type(player) is not int or player not in (0, 1):
        raise ValueError('selected-player fixture requires an alternating mode at PCF019')
    data = bytearray(raw)
    data[state['_offsets']['ram'] + 0x47] = player
    decode_state(bytes(data))
    return bytes(data)


def capture_suite(rom, config_path, out, stella='stella'):
    identity = verified_input(Path(rom))
    producer=producer_snapshot('stella')
    verify_fingerprints({str(Path(__file__)): LOADED_UTILITY_SHA256})
    dependencies = ('reference_traces.py', 'reference_state.py', 'trace_compare.py', 'source_timing.py', 'reference_inventory.py')
    fingerprints = {str(ROOT/'scripts'/name): hashlib.sha256((ROOT/'scripts'/name).read_bytes()).hexdigest()
                    for name in dependencies}
    config_bytes = Path(config_path).read_bytes(); config = json.loads(config_bytes)
    if hashlib.sha256(config_bytes).hexdigest()!=producer['utility_fingerprints']['references/trace-scenarios.json']:
        raise ValueError('scenario differs from committed producer input')
    if config.get('schema_version') != 1 or config.get('source_sha256') != identity['sha256']:
        raise ValueError('scenario source/schema mismatch')
    if config['variations'] != [0, 1, 2, 3]: raise ValueError('all four original variations required')
    for key in ('warmup_intervals', 'select_release_intervals', 'reset_release_intervals'):
        if type(config[key]) is not int or not 1 <= config[key] <= 128: raise ValueError(f'invalid {key}')
    route = expand_route(config['route'])
    out = private_output(out); out.mkdir(parents=True, exist_ok=False)
    seed, timer = config['host_seed'], config['riot_timer_preset']
    initial, backend = poweron_capsule(rom, out/'poweron-a', seed, timer, stella)
    independent, second_backend = poweron_capsule(rom, out/'poweron-b', seed, timer, stella)
    if initial != independent or backend != second_backend: raise ValueError('independent power-on capsules differ')
    base_policy = {'host_seed': seed, 'riot_timer_preset': timer, 'boundary': 'PCF019',
                   'raw_input_every_interval': True, 'instruction_skipping': False,
                   'initialization': 'controlled power-on; host seed/debug counter fixed before source execution'}
    warm = [NEUTRAL] * config['warmup_intervals']
    warm_trace, aligned = capture_steps(rom, initial, warm, out/'warmup-a', stella, base_policy)
    warm_again, aligned_again = capture_steps(rom, independent, warm, out/'warmup-b', stella, base_policy)
    if compare_traces(warm_trace, warm_again) or aligned != aligned_again:
        raise ValueError('independent warmup/full-state replay differs')
    scenarios = []; controlled_turns = []
    for mode in config['variations']:
        prep = []
        for _ in range(mode):
            prep += [{**NEUTRAL, 'swchb': 0x3D}] + [NEUTRAL] * config['select_release_intervals']
        prep += [{**NEUTRAL, 'swchb': 0x3E}] + [NEUTRAL] * config['reset_release_intervals']
        policy = {**base_policy, 'variation': mode, 'fixture': 'source-executed console and controller inputs',
                  'preparation_intervals': len(prep)}
        a, final_a = capture_steps(rom, aligned, prep + route, out/f'variation-{mode}-a', stella, policy)
        b, final_b = capture_steps(rom, aligned_again, prep + route, out/f'variation-{mode}-b', stella, policy)
        errors = compare_traces(a, b)
        if errors or final_a != final_b: raise ValueError(f'variation{mode} replay differs: {errors[:3]}')
        reset = a['steps'][len(prep)-1]
        if reset['ram'][0] != mode: raise ValueError(f'variation{mode} console selection not observed')
        negatives = negative_controls(a)
        (out/f'variation-{mode}-negative-controls.json').write_text(json.dumps(negatives, indent=2)+'\n')
        scenarios.append({'variation': mode, 'steps': len(a['steps']), 'mode_after_reset': reset['ram'][0],
                          'player_after_reset': reset['ram'][0x47], 'full_states_equal': True,
                          'trace_sha256': hashlib.sha256((out/f'variation-{mode}-a/trace.json').read_bytes()).hexdigest(),
                          'raw_state_chain_sha256': hashlib.sha256(''.join(p['state_sha256'] for p in a['steps']).encode()).hexdigest(),
                          'negative_controls_detected': list(negatives)})
        if mode in (1, 3):
            fixture_a = selected_player_fixture(final_a, 1)
            fixture_b = selected_player_fixture(final_b, 1)
            turn_inputs = [NEUTRAL, {**NEUTRAL, 'swcha': 0xEF}, NEUTRAL,
                {**NEUTRAL, 'swcha': 0xFE}, NEUTRAL, {**NEUTRAL, 'swcha': 0xF7}, NEUTRAL,
                {**NEUTRAL, 'fire': [True, False]}, NEUTRAL,
                {**NEUTRAL, 'fire': [False, True]}, NEUTRAL]
            turn_policy = {**policy, 'fixture': 'controlled C7=01 selected-player byte injection; not natural death/swap',
                           'ram_injection': {'C7': 1}}
            turn_a, end_a = capture_steps(rom, fixture_a, turn_inputs, out/f'player1-{mode}-a', stella, turn_policy)
            turn_b, end_b = capture_steps(rom, fixture_b, turn_inputs, out/f'player1-{mode}-b', stella, turn_policy)
            if compare_traces(turn_a, turn_b) or end_a != end_b: raise ValueError('instrumented player1 replay differs')
            if any(point['ram'][0x47] != 1 for point in turn_a['steps']): raise ValueError('selected player1 was not retained')
            if turn_a['steps'][1]['ram'][4] != 0x0F or turn_a['steps'][3]['ram'][4] != 0x0E:
                raise ValueError('controlled player1 did not ignore port0/consume port1 direction')
            if not (turn_a['steps'][7]['ram'][0x2F] & 0x80) or turn_a['steps'][9]['ram'][0x2F] & 0x80:
                raise ValueError('controlled player1 did not select port1 fire')
            controlled_turns.append({'variation': mode, 'fixture': turn_policy['fixture'],
                'steps': len(turn_inputs), 'full_states_equal': True, 'port1_direction_and_fire_observed': True,
                'trace_sha256': hashlib.sha256((out/f'player1-{mode}-a/trace.json').read_bytes()).hexdigest()})
        print(f'Variation{mode}: {len(a["steps"])} complete source states reproduced; six negative controls rejected.', flush=True)
    verify_fingerprints(fingerprints)
    verify_snapshot(producer,'stella')
    report = {'schema_version': 1, 'source': identity, 'backend': backend, 'policy': base_policy,
              **producer,
              'config_sha256': hashlib.sha256(config_bytes).hexdigest(),
              'utility_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'poweron_sha256': hashlib.sha256(initial).hexdigest(),
              'aligned_sha256': hashlib.sha256(aligned).hexdigest(), 'warmup_intervals': len(warm),
              'warmup_full_states_equal': True, 'scenarios': scenarios, 'controlled_player1_turns': controlled_turns,
              'limits': ['Source-executed input surface, not complete-game or all natural boundary-route acceptance',
                         'Active player1 evidence uses an explicit C7 byte injection; natural death/record-swap routes remain pending',
                         'No MSX gameplay/rendering/audio/hardware acceptance']}
    (out/'summary.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=ROOT/'references/roms/frostbite.bin')
    parser.add_argument('--scenarios', type=Path, default=ROOT/'references/trace-scenarios.json')
    parser.add_argument('--stella', default='stella')
    parser.add_argument('--output', type=Path, default=ROOT/'outputs/reference-traces/summary.json')
    args = parser.parse_args(argv)
    try:
        verified_input(args.rom)
        parent = ROOT/'outputs/reference-traces'; parent.mkdir(parents=True, exist_ok=True)
        out = Path(tempfile.mkdtemp(prefix='capture-', dir=parent))/'raw'
        report = capture_suite(args.rom, args.scenarios, out, args.stella)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2)+'\n')
        print(f'Independent reference capture passed; raw evidence {out}; summary {args.output}')
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(f'Reference capture failed: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
