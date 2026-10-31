"""Strict source-oracle comparison; no timing/state/input wildcard masks."""
import re


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
    if not isinstance(expected, dict) or not isinstance(actual, dict):
        return ['trace: objects required']
    visit(expected, actual, 'trace')
    return sorted(mismatches)
