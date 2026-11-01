"""Independent original presentation observations, separate from frozen contacts."""
import hashlib
import json
from pathlib import Path
import re
import os
import subprocess

from presentation_records import parse_records
from reference_provenance import snapshot_paths, audit_manifest
from reference_state import decode_state
from reference_traces import (private_output, run_debugger, batch_script, control_commands,
                              validate_checkpoint, validate_progress)

from environment import ROOT

UPSTREAM = 'https://github.com/stella-emu/stella.git'
REVISION = 'd55b1aec0d067a4c901a6dcdf81cb8f579685659'
PATCH = ROOT / 'tools/stella-presentation.patch'
HELPERS = ('scripts/presentation_reference.py', 'scripts/presentation_records.py',
           'tools/stella-presentation.patch', 'references/presentation-contract.json',
           'scripts/reference_traces.py', 'scripts/reference_state.py', 'scripts/reference_provenance.py',
           'scripts/reference_inventory.py', 'scripts/source_timing.py', 'scripts/trace_compare.py',
           'scripts/graphics_mapping.py', 'scripts/environment.py', 'references/manifest.json')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_backend(binary, patch=PATCH):
    """Check executable/patch identity; capture additionally audits Git provenance."""
    binary = Path(binary)
    report = json.loads((binary.parent / 'frostbite-presentation-observer.json').read_text())
    if (report.get('revision') != REVISION or report.get('binary_sha256') != digest(binary)
            or report.get('patch_sha256') != digest(patch) or report.get('producer_dirty') is not False
            or not re.fullmatch('[0-9a-f]{40}', str(report.get('producer_commit', '')))):
        raise ValueError('exact clean presentation backend/revision/patch required')
    return report


def validate_marker(log, count):
    if (type(count) is not int or not 1 <= count <= 5000
            or re.findall(r'^FROSTBITE_PRESENTATION_COMPLETE (\d+)$', log, re.M) != [str(count)]
            or 'FROSTBITE_PRESENTATION_FAIL' in log):
        raise ValueError('unique complete presentation observation marker required')


def validate_equivalence(records, initial, expected, original_capsules, observed_capsules):
    """Every intermediate CPU/RAM snapshot and complete serialized after-state."""
    if not records or len({len(records), len(expected), len(original_capsules), len(observed_capsules)}) != 1:
        raise ValueError('complete original/observer state chains required')
    previous = initial
    for record, after, plain, observed in zip(records, expected, original_capsules, observed_capsules):
        for phase, state in (('before', previous), ('after', after)):
            if record[phase] != {'registers': {k: state['cpu'][k] for k in ('a', 'x', 'y', 'p', 'sp')}, 'ram': state['ram']}:
                raise ValueError(f'original CPU/all RAM differs at {phase}')
        if plain != observed:
            raise ValueError('complete original capsule changed during observation')
        previous = after


def _producer():
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True):
        raise ValueError('canonical observation requires clean committed producers')
    return snapshot_paths(HELPERS)


def build_backend(out):
    """Fresh source build, with sound core enabled even when runtime output is muted."""
    producer = _producer(); out = private_output(out)
    out.mkdir(parents=True, exist_ok=False)
    commands = [(['git', 'clone', '--no-hardlinks', UPSTREAM, str(out / 'source')], ROOT),
                (['git', 'checkout', '--detach', REVISION], out / 'source'),
                (['git', 'apply', str(PATCH)], out / 'source'),
                (['./configure', '--enable-debugger', '--enable-sound', '--disable-joystick',
                  '--disable-png', '--disable-zip', '--disable-cheats', '--enable-release'], out / 'source'),
                (['make', '-j4'], out / 'source')]
    with (out / 'build.log').open('w') as log:
        for command, cwd in commands:
            subprocess.run(command, cwd=cwd, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=600)
    source = out / 'source'; binary = source / 'stella'
    if '-DSOUND_SUPPORT' not in (source / 'config.mak').read_text():
        raise ValueError('original audio oscillator core must be enabled')
    actual = subprocess.check_output(['git', 'diff', '--binary', '--no-ext-diff'], cwd=source)
    if actual != PATCH.read_bytes(): raise ValueError('backend source differs from exact observer patch')
    if _producer() != producer: raise ValueError('observer producer changed while building')
    report = {'revision': REVISION, 'upstream': UPSTREAM, 'producer_commit': producer['tool_source_commit'],
              'producer_dirty': False, 'producer': producer, 'patch_sha256': digest(PATCH),
              'binary_sha256': digest(binary), 'sound_core': True,
              'commands': [command for command, _ in commands]}
    (source / 'frostbite-presentation-observer.json').write_text(json.dumps(report, indent=2) + '\n')
    verify_backend(binary)
    return report


def observe(out, initial, inputs, backend):
    """Bounded input-only execution, independently repeated without the probe."""
    if not isinstance(inputs, list) or not 1 <= len(inputs) <= 5000:
        raise ValueError('bounded explicit original pin samples required')
    for sample in inputs: control_commands(sample)
    producer = _producer(); identity = verify_backend(backend)
    audit_manifest(identity['producer'], HELPERS)
    initial_bytes = Path(initial).read_bytes(); start = decode_state(initial_bytes)
    if start['cpu']['pc'] != 0xF019: raise ValueError('complete F019 capsule required')
    out = private_output(out); out.mkdir(parents=True, exist_ok=False)
    (out / 'initial.state').write_bytes(initial_bytes)
    current = initial_bytes; points = []; journals = []
    for offset in range(0, len(inputs), 10):
        samples = inputs[offset:offset + 10]; directory = out / f'batch-{offset:05d}'
        directory.mkdir()
        restored_sha256 = hashlib.sha256(current).hexdigest()
        plain, plain_identity = run_debugger(ROOT / 'references/roms/frostbite.bin', batch_script(samples),
                                            directory / 'plain', current, stella=str(backend))
        commands = ['base dec', 'loadState 0']
        for slot, sample in enumerate(samples):
            commands += control_commands(sample) + ['presentationProbe', f'saveState {slot}']
        commands += ['exitRom', '']
        env = {'FROSTBITE_PRESENTATION_OUTPUT': str(directory / 'records.bin'),
               'FROSTBITE_PRESENTATION_COUNT': str(len(samples))}
        previous_env = {key: os.environ.get(key) for key in env}
        try:
            os.environ.update(env)
            observed, observed_identity = run_debugger(ROOT / 'references/roms/frostbite.bin', '\n'.join(commands),
                                                       directory / 'observed', current, stella=str(backend))
        finally:
            for key, value in previous_env.items():
                if value is None: os.environ.pop(key, None)
                else: os.environ[key] = value
        if set(plain) != set(range(len(samples))) or set(observed) != set(plain) or plain_identity != observed_identity:
            raise ValueError('missing/different source checkpoint chain or backend')
        validate_marker((directory / 'observed/stella.log').read_text(), len(samples))
        records = parse_records((directory / 'records.bin').read_bytes())
        expected = [decode_state(plain[i]) for i in range(len(samples))]
        validate_equivalence(records, decode_state(current), expected, list(plain.values()), list(observed.values()))
        previous = decode_state(current)
        for slot, (sample, record, state) in enumerate(zip(samples, records, expected)):
            validate_checkpoint(state, sample); validate_progress(previous, state)
            if record['cycles'] != state['cycles'] - previous['cycles']:
                raise ValueError('source interval timestamp differs from full capsule')
            points.append({'index': offset + slot, 'input': sample, 'cycles': record['cycles'],
                           'visible_cycles': record['visible_cycles'], 'source_frame': record['source_frame'],
                           'after_frame': record['after_frame'], 'frame_count': len(record['frames']),
                           'audio_writes': len(record['audio']), 'state_sha256': hashlib.sha256(observed[slot]).hexdigest()})
            previous = state
        current = observed[len(samples) - 1]
        journals.append({'offset': offset, 'count': len(samples), 'restored_sha256': restored_sha256,
                         'records_sha256': digest(directory / 'records.bin')})
    if _producer() != producer or verify_backend(backend) != identity:
        raise ValueError('observer producer/backend changed during capture')
    (out / 'final.state').write_bytes(current)
    report = {'schema_version': 2, 'producer': producer, 'backend': identity, 'initial_sha256': hashlib.sha256(initial_bytes).hexdigest(),
              'final_sha256': hashlib.sha256(current).hexdigest(), 'points': points, 'journals': journals,
              'all_complete_capsules_equal': True, 'limits': ['Raw native viewports retained; target mapping and manual/physical review are separate gates']}
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return report
