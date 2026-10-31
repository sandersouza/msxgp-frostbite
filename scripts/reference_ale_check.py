#!/usr/bin/env python3
"""Secondary seeded ALE0.12.1 repeatability; never a four-mode/port1 oracle."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from reference_inventory import ROOT, verified_input
from reference_traces import private_output, verify_fingerprints

ALE_COMMIT = '8a8fafb1ac37796e3e8197a2e5727204fa1b926d'


def legal_action_codes(actions):
    values = {action.value for action in actions}
    if any(type(value) is not int or not 0 <= value <= 17 for value in values):
        raise ValueError('unsupported native ALE action values')
    return values


def validate_ale_repeats(first, second):
    for run in (first, second):
        policy = run['policy']
        if run['mode'] not in (0, 2) or policy['frame_skip'] != 1 or policy['repeat_action_probability'] != 0:
            raise ValueError('ALE requires supported mode0/2, frame_skip1, sticky probability0')
        if type(policy['seed']) is not int or not run['steps']:
            raise ValueError('explicit seed/nonempty ALE steps required')
        if not re.fullmatch('[0-9a-f]{64}', run['initial_sha256']): raise ValueError('ALE initial-state hash required')
        for index, point in enumerate(run['steps'], 1):
            if point['frame'] != index: raise ValueError('ALE frame skipped/repeated')
            if len(point['ram']) != 128 or any(type(v) is not int or not 0 <= v <= 255 for v in point['ram']):
                raise ValueError('complete128byte ALE RAM required')
            if any(not re.fullmatch('[0-9a-f]{64}', point[key]) for key in ('state_sha256', 'screen_sha256')):
                raise ValueError('complete serialized/screen hashes required')
    if first != second: raise ValueError('independent ALE serialized/input/RAM/frame/screen evidence differs')


def capture_ale(rom, out, seed=1):
    source = verified_input(Path(rom))
    if type(seed) is not int or not 0 <= seed <= 0x7FFFFFFF: raise ValueError('ALE seed must be positive int32/zero')
    import ale_py
    import ale_py._ale_py as binary
    import numpy
    if ale_py.__version__ != '0.12.1': raise ValueError('reviewed ALE0.12.1 required; preserve existing environment')
    tool_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    fingerprints = {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in (Path(__file__), Path(binary.__file__))}
    out = private_output(out); out.mkdir(parents=True, exist_ok=False)
    actions = list(range(18)) + [0, 2, 3, 4, 5, 1, 0, 1, 0]
    summaries = []
    for mode in (0, 2):
        runs = []
        for repeat in range(2):
            directory = out/f'mode-{mode}-run-{repeat}'; directory.mkdir()
            ale = ale_py.ALEInterface()
            ale.setInt('random_seed', seed); ale.setInt('frame_skip', 1)
            ale.setFloat('repeat_action_probability', 0)
            ale.loadROM(str(rom))
            if list(ale.getAvailableModes()) != [0, 2]: raise ValueError('unexpected ALE mode contract')
            ale.setMode(mode)
            policy = {'seed': ale.getInt('random_seed'), 'frame_skip': ale.getInt('frame_skip'),
                      'repeat_action_probability': ale.getFloat('repeat_action_probability')}
            initial = ale.cloneSystemState().serialize()
            (directory/'initial.state').write_bytes(initial)
            legal = legal_action_codes(ale.getLegalActionSet())
            if not set(actions) <= legal: raise ValueError('unsupported ALE action schedule')
            points = []
            for index, action in enumerate(actions, 1):
                reward = ale.act(action)
                raw = ale.cloneSystemState().serialize()
                (directory/f'frame-{index:04d}.state').write_bytes(raw)
                points.append({'frame': ale.getFrameNumber(), 'action': action, 'reward': reward,
                    'ram': ale.getRAM().tolist(), 'state_sha256': hashlib.sha256(raw).hexdigest(),
                    'screen_sha256': hashlib.sha256(ale.getScreenRGB().tobytes()).hexdigest()})
            run = {'mode': mode, 'policy': policy, 'initial_sha256': hashlib.sha256(initial).hexdigest(), 'steps': points}
            (directory/'trace.json').write_text(json.dumps(run, indent=2)+'\n')
            runs.append(run)
        validate_ale_repeats(*runs)
        summaries.append({'mode': mode, 'steps': len(actions), 'policy': runs[0]['policy'],
            'full_serialized_states_equal': True, 'ram_screen_inputs_equal': True,
            'initial_sha256': runs[0]['initial_sha256'],
            'trace_sha256': hashlib.sha256((out/f'mode-{mode}-run-0/trace.json').read_bytes()).hexdigest()})
    verify_fingerprints(fingerprints); verified_input(Path(rom))
    report = {'schema_version': 1, 'source': source, 'tool_source_commit': tool_commit,
        'backend': {'name': 'ALE', 'version': ale_py.__version__, 'source_commit': ALE_COMMIT,
                    'binary_sha256': fingerprints[str(Path(binary.__file__))], 'numpy': numpy.__version__},
        'utility_sha256': fingerprints[str(Path(__file__))], 'modes': summaries,
        'limits': ['Only ALE adapter modes0/2; Python act second argument is paddle strength, not controller2',
                   'ALE initialization/adaptor resets are not aligned to the Stella PCF019 capsule',
                   'No cross-backend full-state equality, natural alternating-player or MSX acceptance claimed']}
    (out/'summary.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=ROOT/'references/roms/frostbite.bin')
    parser.add_argument('--seed', type=int, default=1)
    parser.add_argument('--output', type=Path, default=ROOT/'outputs/reference-ale/summary.json')
    args = parser.parse_args(argv)
    try:
        verified_input(args.rom)
        parent = ROOT/'outputs/reference-ale'; parent.mkdir(parents=True, exist_ok=True)
        out = Path(tempfile.mkdtemp(prefix='capture-', dir=parent))/'raw'
        report = capture_ale(args.rom, out, args.seed)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2)+'\n')
        print(f'ALE0/2 seeded whole-state repeatability passed; raw evidence {out}')
        return 0
    except (OSError, ValueError, KeyError, TypeError, ImportError, subprocess.SubprocessError) as error:
        print(f'Secondary ALE check failed: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__': sys.exit(main())
