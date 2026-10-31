"""Strict source-oracle comparison; no timing/state/input wildcard masks."""
import argparse
import copy
import json
from pathlib import Path
import re
import sys


def validate_trace(trace):
    required = {'schema_version', 'source_sha256', 'backend', 'initial_sha256', 'policy', 'steps'}
    if not isinstance(trace, dict) or not required <= trace.keys() or type(trace['schema_version']) is not int or trace['schema_version'] != 1:
        raise ValueError('missing/unsupported trace schema')
    for name in ('source_sha256', 'initial_sha256'):
        if not isinstance(trace[name], str) or not re.fullmatch('[0-9a-f]{64}', trace[name]):
            raise ValueError(f'invalid {name}')
    if not trace['backend'] or not isinstance(trace['policy'], dict) or not trace['policy']:
        raise ValueError('backend and explicit policy required')
    if not isinstance(trace['steps'], list) or not trace['steps']:
        raise ValueError('nonempty ordered steps required')
    for index, step in enumerate(trace['steps']):
        if not isinstance(step, dict) or not {'index', 'input', 'cpu', 'ram', 'tia', 'state_sha256'} <= step.keys():
            raise ValueError(f'incomplete step {index}')
        if type(step['index']) is not int or step['index'] != index:
            raise ValueError(f'nonsequential step {index}')
        ram = step['ram']
        if not isinstance(ram, list) or len(ram) != 128 or any(type(v) is not int or not 0 <= v <= 255 for v in ram):
            raise ValueError(f'incomplete/invalid RAM step {index}')
        for register, maximum in (('pc', 65535), ('p', 255)):
            value = step['cpu'].get(register)
            if type(value) is not int or not 0 <= value <= maximum:
                raise ValueError(f'invalid CPU {register} step {index}')
        if not step['tia'] or not isinstance(step['input'], dict) or not step['input']:
            raise ValueError(f'TIA/input evidence required step {index}')
        if not isinstance(step['state_sha256'], str) or not re.fullmatch('[0-9a-f]{64}', step['state_sha256']):
            raise ValueError(f'invalid state hash step {index}')


def compare_traces(expected, actual):
    mismatches = []
    for name, trace in (('expected', expected), ('actual', actual)):
        try: validate_trace(trace)
        except (ValueError, TypeError, AttributeError) as error: mismatches.append(f'{name}: {error}')
    if mismatches: return mismatches
    return differences(expected, actual, 'trace')


def differences(expected, actual, root):
    mismatches = []
    def visit(a, b, path):
        if type(a) is not type(b):
            mismatches.append(f'{path}: type mismatch')
        elif isinstance(a, dict):
            if a.keys() != b.keys(): mismatches.append(f'{path}: key set mismatch')
            for key in a.keys() & b.keys(): visit(a[key], b[key], f'{path}.{key}')
        elif isinstance(a, list):
            if len(a) != len(b): mismatches.append(f'{path}: length {len(a)} != {len(b)}')
            for index, (left, right) in enumerate(zip(a, b)): visit(left, right, f'{path}[{index}]')
        elif a != b:
            mismatches.append(f'{path}: {a!r} != {b!r}')
    visit(expected, actual, root)
    return sorted(mismatches)


def collision_inputs(ram):
    return {'floe_object_samples':ram[0x30:0x38], 'object_row':ram[0x38],
            'floe_row':ram[0x39], 'shore_latch':ram[0x6D]}


def logical_oracle(trace):
    validate_trace(trace)
    result = {'schema_version':1, 'contract':'frostbite/source-logical/F019/v1',
        'oracle':{'source_sha256':trace['source_sha256'], 'initial_sha256':trace['initial_sha256'],
                  'source_backend':copy.deepcopy(trace['backend']), 'policy':copy.deepcopy(trace['policy'])},
        'steps':[]}
    for point in trace['steps']:
        result['steps'].append({'index':point['index'], 'source_phase_pc':point['cpu']['pc'],
            'input':copy.deepcopy(point['input']),
            'cpu':{name:point['cpu'][name] for name in ('a','x','y','p','sp')},
            'ram':point['ram'].copy(), 'collision_inputs':collision_inputs(point['ram'])})
    validate_logical_oracle(result)
    return result


def validate_logical_oracle(trace):
    if trace['schema_version'] != 1 or trace['contract'] != 'frostbite/source-logical/F019/v1':
        raise ValueError('unsupported logical oracle contract')
    oracle = trace['oracle']
    if not oracle['source_backend'] or not oracle['policy']: raise ValueError('logical source provenance required')
    for name in ('source_sha256','initial_sha256'):
        if not re.fullmatch('[0-9a-f]{64}', oracle[name]): raise ValueError('invalid logical source identity')
    if not trace['steps']: raise ValueError('empty logical oracle')
    for index, point in enumerate(trace['steps']):
        if point['index'] != index or point['source_phase_pc'] != 0xF019: raise ValueError('logical order/phase mismatch')
        ram = point['ram']
        if len(ram) != 128 or any(type(v) is not int or not 0 <= v <= 255 for v in ram): raise ValueError('invalid logical RAM')
        if set(point['cpu']) != {'a','x','y','p','sp'} or any(type(v) is not int or not 0<=v<=255 for v in point['cpu'].values()):
            raise ValueError('invalid logical source-register mapping')
        if not point['input'] or point['collision_inputs'] != collision_inputs(ram): raise ValueError('logical input/collision inconsistency')


def compare_logical_oracles(expected, actual):
    errors = []
    for name, trace in (('expected',expected),('actual',actual)):
        try: validate_logical_oracle(trace)
        except (ValueError,TypeError,KeyError,AttributeError) as error: errors.append(f'{name}: {error}')
    return errors or differences(expected,actual,'logical')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command',required=True)
    project = sub.add_parser('project'); project.add_argument('source',type=Path); project.add_argument('output',type=Path)
    compare = sub.add_parser('compare'); compare.add_argument('expected',type=Path); compare.add_argument('actual',type=Path)
    compare.add_argument('--logical',action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.command == 'project':
            from reference_inventory import ROOT
            destination=args.output.resolve()
            if not destination.is_relative_to((ROOT/'outputs').resolve()): raise ValueError('logical/raw state stays in ignored outputs')
            result=logical_oracle(json.loads(args.source.read_text()))
            destination.parent.mkdir(parents=True,exist_ok=True)
            destination.write_text(json.dumps(result,indent=2)+'\n')
            print(f'Projected strict F019 mechanics contract: {destination}')
            return 0
        first=json.loads(args.expected.read_text()); second=json.loads(args.actual.read_text())
        errors=compare_logical_oracles(first,second) if args.logical else compare_traces(first,second)
        if errors: print('\n'.join(errors[:20])); return 1
        print('Complete declared oracle contract matches.');return 0
    except (OSError,ValueError,TypeError,KeyError,AttributeError) as error:
        print(f'Trace comparison failed: {error}',file=sys.stderr);return 1


if __name__=='__main__':sys.exit(main())
