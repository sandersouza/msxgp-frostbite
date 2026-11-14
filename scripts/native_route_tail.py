"""Append independently replayed neutral source intervals for PAL tail coverage.

Never repeat/fabricate source states. Original route directories stay immutable.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

from environment import ROOT
from reference_traces import capture_steps, NEUTRAL, private_output
from trace_compare import compare_traces, validate_trace
from progression_play import assess_receipt, source_helpers
from reference_provenance import audit_manifest, snapshot_paths


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_parent_endpoint(trace, final):
    validate_trace(trace)
    if not trace['steps'] or bytes.fromhex(trace['steps'][-1]['state_bytes']) != final:
        raise ValueError('parent final capsule differs from its last source point')


def extend(source, out):
    source = source.resolve()
    out = private_output(out)
    if out.exists():
        raise ValueError('fresh extended source output required')
    receipt = json.loads((source/'route.json').read_bytes())
    audit_manifest(receipt, source_helpers(receipt))
    hashes = {name: sha(source/name) for name in receipt['files']}
    if hashes != receipt['files'] or receipt.get('clean_start') is not True:
        raise ValueError('immutable clean original route required')
    producer = sha(Path(__file__))
    executed_helpers = tuple(dict.fromkeys((*source_helpers(receipt),
        'scripts/native_route_tail.py', 'scripts/progression_play.py',
        'scripts/trace_compare.py', 'scripts/reference_traces.py')))
    executed_producers = snapshot_paths(executed_helpers)
    parent_sha = sha(source/'route.json')
    initial = (source/'final.state').read_bytes()
    trace = json.loads((source/'trace.json').read_bytes())
    check_parent_endpoint(trace, initial)
    parent_steps = len(trace['steps'])
    inputs = json.loads((source/'inputs.json').read_bytes())
    samples = [dict(NEUTRAL) for _ in range(4)]
    out.mkdir(parents=True)
    first, end = capture_steps(ROOT/'references/roms/frostbite.bin', initial,
                               samples, out/'tail-a', policy=trace['policy'])
    second, end2 = capture_steps(ROOT/'references/roms/frostbite.bin', initial,
                                 samples, out/'tail-b', policy=trace['policy'])
    if compare_traces(first, second) or end != end2 or first['backend'] != trace['backend']:
        raise ValueError('independent source tail repeat/backend differs')
    for name in receipt['files']:
        shutil.copyfile(source/name, out/name)
    points = trace['steps']
    for point in first['steps']:
        point['index'] = len(points)
        points.append(point)
    validate_trace(trace)
    (out/'trace.json').write_text(json.dumps(trace)+'\n')
    (out/'inputs.json').write_text(json.dumps(inputs+samples)+'\n')
    journal = json.loads((source/'journal.json').read_bytes())
    journal.append(dict(path='tail-a', intervals=4,
                        trace_sha256=sha(out/'tail-a/trace.json'),
                        final_sha256=sha(out/'tail-a/final.state')))
    (out/'journal.json').write_text(json.dumps(journal)+'\n')
    (out/'final.state').write_bytes(end)
    extension = dict(parent_path=str(source), parent_receipt_sha256=parent_sha,
                     parent_files=hashes, producer_sha256=producer,
                     independent_runs=2, appended_intervals=4,
                     tail_a_trace_sha256=sha(out/'tail-a/trace.json'),
                     tail_b_trace_sha256=sha(out/'tail-b/trace.json'),
                     tail_a_final_sha256=sha(out/'tail-a/final.state'),
                     tail_b_final_sha256=sha(out/'tail-b/final.state'),
                     executed_producers=executed_producers,
                     original_horizon=parent_steps,
                     source_state_injections=0)
    (out/'extension.json').write_text(json.dumps(extension, indent=2)+'\n')
    receipt['steps'] = len(points)
    if assess_receipt(points[:parent_steps], receipt) != receipt['assessment']:
        raise ValueError('original route assessment changed')
    receipt['files'] = {name: sha(out/name) for name in (*hashes, 'extension.json')}
    receipt['extension'] = extension
    if snapshot_paths(executed_helpers) != executed_producers or sha(Path(__file__)) != producer or sha(source/'route.json') != parent_sha or any(sha(source/name) != value for name,value in hashes.items()):
        raise ValueError('producer/original route changed during extension')
    (out/'route.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(extension))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    extend(**vars(p.parse_args()))
