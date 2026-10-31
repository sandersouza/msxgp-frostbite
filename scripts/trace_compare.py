"""Strict source-oracle comparison; no timing/state/input wildcard masks."""
import argparse
import copy
import json
from pathlib import Path
import re
import sys
from reference_state import decode_state


def validate_backend(backend):
    if (not isinstance(backend,dict) or set(backend)!={'name','version','source_contract','binary_sha256'}
            or backend['name']!='Stella' or backend['version']!='7.0'
            or backend['source_contract']!='d55b1aec0d067a4c901a6dcdf81cb8f579685659'
            or not isinstance(backend['binary_sha256'],str)
            or not re.fullmatch('[0-9a-f]{64}',backend['binary_sha256'])):
        raise ValueError('supported structured Stella source identity required')


def validate_policy(policy):
    if (not isinstance(policy,dict) or not policy
            or not any(isinstance(policy.get(key),str) and policy[key] for key in ('boundary','route'))):
        raise ValueError('structured source boundary/route policy required')
    if 'host_seed' in policy and (type(policy['host_seed']) is not int or not 0<=policy['host_seed']<=0xFFFFFFFF):
        raise ValueError('invalid source host seed')


def validate_input(sample):
    if not isinstance(sample,dict) or set(sample)!={'swcha','swchb','fire'}:
        raise ValueError('complete raw controller/console input required')
    if any(type(sample[key]) is not int or not 0<=sample[key]<=255 for key in ('swcha','swchb')):
        raise ValueError('raw input bytes required')
    if not isinstance(sample['fire'],list) or len(sample['fire'])!=2 or any(type(v) is not bool for v in sample['fire']):
        raise ValueError('two explicit boolean fire inputs required')


def validate_trace(trace):
    required = {'schema_version', 'source_sha256', 'backend', 'initial_sha256', 'policy', 'steps'}
    if not isinstance(trace, dict) or set(trace) != required or type(trace['schema_version']) is not int or trace['schema_version'] != 2:
        raise ValueError('missing/unsupported trace schema')
    for name in ('source_sha256', 'initial_sha256'):
        if not isinstance(trace[name], str) or not re.fullmatch('[0-9a-f]{64}', trace[name]):
            raise ValueError(f'invalid {name}')
    validate_backend(trace['backend']);validate_policy(trace['policy'])
    if not isinstance(trace['steps'], list) or not trace['steps']:
        raise ValueError('nonempty ordered steps required')
    for index, step in enumerate(trace['steps']):
        if not isinstance(step, dict) or not {'index','input','state_bytes'} <= step.keys():
            raise ValueError(f'incomplete step {index}')
        if type(step['index']) is not int or step['index'] != index:
            raise ValueError(f'nonsequential step {index}')
        validate_input(step['input'])
        encoded=step['state_bytes']
        if not isinstance(encoded,str) or len(encoded)>8*1024*1024 or not re.fullmatch('(?:[0-9a-f]{2})+',encoded):
            raise ValueError(f'invalid raw state bytes step {index}')
        decoded=decode_state(bytes.fromhex(encoded))
        recorded={key:value for key,value in step.items() if key not in ('index','input','state_bytes')}
        if differences(decoded,recorded,'decoded') or decoded['cpu']['pc']!=0xF019:
            raise ValueError(f'incomplete/inconsistent decoded state step {index}')
        swcha=0
        for port,controller in enumerate(decoded['controllers']):
            for bit,level in enumerate(controller['digital'][:4]):swcha|=int(level)<<(bit+(4 if port==0 else 0))
        observed={'swcha':swcha,'swchb':decoded['switches'],
                  'fire':[not controller['digital'][4] for controller in decoded['controllers']]}
        if observed!=step['input']:raise ValueError(f'observed input mismatch step {index}')


def compare_traces(expected, actual):
    mismatches = []
    for name, trace in (('expected', expected), ('actual', actual)):
        try: validate_trace(trace)
        except (ValueError, TypeError, KeyError, AttributeError) as error: mismatches.append(f'{name}: {error}')
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
    if (not isinstance(trace,dict) or set(trace)!={'schema_version','contract','oracle','steps'}
            or type(trace['schema_version']) is not int or trace['schema_version'] != 1
            or trace['contract'] != 'frostbite/source-logical/F019/v1'):
        raise ValueError('unsupported logical oracle contract')
    oracle = trace['oracle']
    if not isinstance(oracle,dict) or set(oracle)!={'source_backend','policy','source_sha256','initial_sha256'}:
        raise ValueError('complete logical source provenance required')
    validate_backend(oracle['source_backend']);validate_policy(oracle['policy'])
    for name in ('source_sha256','initial_sha256'):
        if not re.fullmatch('[0-9a-f]{64}', oracle[name]): raise ValueError('invalid logical source identity')
    if not isinstance(trace['steps'],list) or not trace['steps']: raise ValueError('empty logical oracle')
    for index, point in enumerate(trace['steps']):
        if not isinstance(point,dict) or set(point)!={'index','source_phase_pc','input','cpu','ram','collision_inputs'}:
            raise ValueError('incomplete logical point')
        if type(point['index']) is not int or point['index'] != index or type(point['source_phase_pc']) is not int or point['source_phase_pc'] != 0xF019:
            raise ValueError('logical order/phase mismatch')
        ram = point['ram']
        if not isinstance(ram,list) or len(ram) != 128 or any(type(v) is not int or not 0 <= v <= 255 for v in ram): raise ValueError('invalid logical RAM')
        if set(point['cpu']) != {'a','x','y','p','sp'} or any(type(v) is not int or not 0<=v<=255 for v in point['cpu'].values()):
            raise ValueError('invalid logical source-register mapping')
        validate_input(point['input'])
        if differences(collision_inputs(ram),point['collision_inputs'],'collision'): raise ValueError('logical collision inconsistency')


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
