#!/usr/bin/env python3
"""Bounded natural-input refuge route from a validated source Reset checkpoint."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from reference_inventory import ROOT, verified_input
from reference_state import decode_state
from reference_traces import NEUTRAL, STATE_NAME, capture_steps, private_output, verify_fingerprints
from trace_compare import compare_traces, validate_trace


def assess_refuge(approach, wait):
    if len(approach) < 32 or len(wait) < 3: raise ValueError('incomplete natural refuge route')
    x = approach[-1]['ram'][0x66]
    if x > 16 or any(point['ram'][0x66] != x for point in approach[-32:]):
        raise ValueError('extreme-left held-input plateau was not reached')
    reserve = approach[0]['ram'][0x4C]
    for point in approach + wait:
        ram = point['ram']
        if (ram[0x4B] < 3 or ram[0x64] != 0x1B or ram[0x6A] != 0 or ram[0x6D] & 0x80
                or ram[0x71] != 0 or ram[0x4C] != reserve):
            raise ValueError('route hit/jump/phase/life-loss; no natural refuge acceptance')
    if any(point['ram'][0x66] != x for point in wait): raise ValueError('player left the refuge while waiting')
    bear = [point['ram'][0x68] for point in wait]
    unique = [value for index,value in enumerate(bear) if index == 0 or value != bear[index-1]]
    signs = [1 if b > a else -1 for a,b in zip(unique,unique[1:])]
    reversals = sum(a != b for a,b in zip(signs,signs[1:]))
    if min(bear) > x+8 or max(bear) < 128 or reversals < 2:
        raise ValueError('bear did not complete the observed two-direction shore sweep')
    return {'refuge_x':x, 'bear_min':min(bear), 'bear_max':max(bear), 'bear_direction_reversals':reversals,
            'reserve':reserve, 'grounded_shore':True, 'effective_bear_hits':0}


def source_reset_checkpoint(summary_path):
    summary_bytes = Path(summary_path).read_bytes(); summary = json.loads(summary_bytes)
    digest = hashlib.sha256(summary_bytes).hexdigest()
    candidates = [path.parent for path in (ROOT/'outputs/reference-traces').glob('capture-*/raw/summary.json')
                  if hashlib.sha256(path.read_bytes()).hexdigest() == digest]
    if not candidates: raise ValueError('matching private source capture unavailable; run reference_traces first')
    root = max(candidates,key=lambda path:path.stat().st_mtime)
    trace_path = root/'variation-2-a/trace.json'; trace = json.loads(trace_path.read_text()); validate_trace(trace)
    declared = next(case for case in summary['scenarios'] if case['variation'] == 2)
    if hashlib.sha256(trace_path.read_bytes()).hexdigest() != declared['trace_sha256']:
        raise ValueError('private source preparation trace identity mismatch')
    index = trace['policy']['preparation_intervals']-1
    raw_path = root/f'variation-2-a/batch-{index//10*10:05d}/settings/state/{STATE_NAME}.st{index%10}'
    raw = raw_path.read_bytes(); state = decode_state(raw)
    expected = {key:value for key,value in trace['steps'][index].items() if key not in ('index','input')}
    if state != expected or state['ram'][0] != 2 or state['cpu']['pc'] != 0xF019:
        raise ValueError('source Reset checkpoint does not match complete raw evidence')
    return raw, {'preparation_summary_sha256':digest, 'preparation_trace_sha256':declared['trace_sha256'],
                 'source_sha256':trace['source_sha256'], 'preparation_tool_commit':summary['tool_source_commit']}


def capture_refuge(rom, summary_path, out, stella='stella'):
    source = verified_input(Path(rom)); initial, provenance = source_reset_checkpoint(summary_path)
    if provenance['source_sha256'] != source['sha256']: raise ValueError('refuge source identity mismatch')
    fingerprints = {str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in
        (Path(__file__),ROOT/'scripts/reference_traces.py',ROOT/'scripts/reference_state.py',ROOT/'scripts/trace_compare.py')}
    out = private_output(out); out.mkdir(parents=True,exist_ok=False)
    policy = {**provenance, 'route':'source-executed variation2 Reset -> held left500 -> neutral1536',
              'ram_injections':{}, 'boundary':'PCF019; no frame/instruction skipping'}
    steps = [{**NEUTRAL,'swcha':0xBF}]*500 + [NEUTRAL]*1536
    first, end_a = capture_steps(rom,initial,steps,out/'run-a',stella,policy)
    print('Natural refuge first execution captured2036 intervals; starting independent replay.',flush=True)
    second,end_b = capture_steps(rom,initial,steps,out/'run-b',stella,policy)
    if compare_traces(first,second) or end_a != end_b: raise ValueError('natural refuge replay/full-state mismatch')
    observation = assess_refuge(first['steps'][:500],first['steps'][500:])
    verify_fingerprints(fingerprints); verified_input(Path(rom))
    report = {'schema_version':1,'source':source,'provenance':provenance,'policy':policy,
        'tool_source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'utility_sha256':fingerprints[str(Path(__file__))], 'steps':len(steps), 'independent_runs':2,
        'full_states_equal':True,'observation':observation,
        'trace_sha256':hashlib.sha256((out/'run-a/trace.json').read_bytes()).hexdigest(),
        'limits':['One naturally executed shore route at observed level4; not every bear/airborne/multi-threat geometry',
                  'No natural death/record-swap or complete-game acceptance; no MSX ROM produced']}
    (out/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,default=ROOT/'references/roms/frostbite.bin')
    parser.add_argument('--preparation-summary',type=Path,default=ROOT/'outputs/reference-traces/summary.json')
    parser.add_argument('--stella',default='stella')
    parser.add_argument('--output',type=Path,default=ROOT/'outputs/reference-refuge/summary.json')
    args=parser.parse_args(argv)
    try:
        verified_input(args.rom)
        parent=ROOT/'outputs/reference-refuge';parent.mkdir(parents=True,exist_ok=True)
        out=Path(tempfile.mkdtemp(prefix='capture-',dir=parent))/'raw'
        report=capture_refuge(args.rom,args.preparation_summary,out,args.stella)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,indent=2)+'\n')
        print(f'Natural refuge route passed: {report["observation"]}; raw evidence {out}')
        return 0
    except (OSError,ValueError,KeyError,TypeError,StopIteration,subprocess.SubprocessError) as error:
        print(f'Natural refuge capture failed: {error}',file=sys.stderr)
        return 1


if __name__=='__main__':sys.exit(main())
