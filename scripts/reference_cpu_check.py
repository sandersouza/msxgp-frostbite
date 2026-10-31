#!/usr/bin/env python3
"""Compare py65 CPU/RAM results with actual Stella instruction execution."""
import argparse
import hashlib
from importlib.metadata import version
import inspect
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from mechanics_probe import execute_slice, instruction_boundaries
from reference_inventory import ROOT, verified_input
from reference_state import decode_state
from reference_traces import poweron_capsule, private_output, run_debugger, verify_fingerprints


def prepare_cpu_fixture(raw, case):
    if case.get('mmio'): raise ValueError('constant MMIO fixtures are not independent hardware evidence')
    state = decode_state(raw); offsets = state['_offsets']; data = bytearray(raw)
    registers = {'a': 0, 'x': 0, 'y': 0, 'sp': 0xFF, 'p': 0x30}
    for name, value in case.get('registers', {}).items():
        if name not in registers or type(value) is not int or not 0 <= value <= 255:
            raise ValueError('invalid controlled CPU register')
        registers[name] = value
    pc = int(case['start'], 16)
    if not 0xF000 <= pc <= 0xFFFF: raise ValueError('CPU fixture entry outside source window')
    cpu = offsets['cpu']
    for index, name in enumerate(('a', 'x', 'y', 'sp')): data[cpu+index] = registers[name]
    data[cpu+5:cpu+7] = pc.to_bytes(2, 'little')
    p = registers['p']
    bits = [bool(p & (1 << bit)) for bit in (7, 6, 4, 3, 2)] + [not bool(p & 2), bool(p & 1)]
    data[cpu+7:cpu+14] = bytes(0xFE if bit else 1 for bit in bits)
    data[cpu+14] = 0
    ram = offsets['ram']; data[ram:ram+128] = bytes(128)
    for address, value in case.get('ram', {}).items():
        address, value = int(address, 16), int(value, 16)
        if not 0x80 <= address <= 0xFF or not 0 <= value <= 255: raise ValueError('invalid CPU fixture RAM')
        data[ram+address-0x80] = value
    decode_state(bytes(data))
    return bytes(data)


def compare_cpu(expected, actual):
    errors = []
    if set(expected['ram']) != {f'{a:02X}' for a in range(0x80, 0x100)}:
        raise ValueError('independent comparison requires all128 RAM bytes')
    if actual['cpu']['pc'] != int(expected['stop_pc'], 16): errors.append('stop PC differs')
    for name in ('a', 'x', 'y', 'p', 'sp'):
        if expected['registers'][name] != actual['cpu'][name]:
            errors.append(f'CPU {name}: py65={expected["registers"][name]:02X}, Stella={actual["cpu"][name]:02X}')
    for index, value in enumerate(actual['ram']):
        address = f'{index+0x80:02X}'
        if int(expected['ram'][address], 16) != value:
            errors.append(f'RAM {address}: py65={expected["ram"][address]}, Stella={value:02X}')
    return errors


def arithmetic_vectors(data):
    if data[0xB9B:0xB9D] != bytes([0x65, 0xCA]) or data[0xBC5:0xBC7] != bytes([0xE9, 1]):
        raise ValueError('canonical arithmetic instruction contract changed')
    values = (0x00, 0x09, 0x49, 0x50, 0x79, 0x80, 0x99, 0xFF)
    cases = []
    for operation, start, stop in (('adc', 'FB9B', 'FB9D'), ('sbc', 'FBC5', 'FBC7')):
        for a in values:
            for operand in values if operation == 'adc' else (1,):
                for carry in (0, 1):
                    for decimal in (0, 1):
                        cases.append({'id': f'nmos-{operation}-{a:02x}-{operand:02x}-{carry}-{decimal}',
                            'start': start, 'stops': [stop], 'limit': 2,
                            'registers': {'a': a, 'p': 0x20 | carry | (decimal << 3)},
                            'ram': {'CA': f'{operand:02X}'}})
    return cases


def check_cpu(rom, cases_path, out, stella='stella'):
    source = verified_input(Path(rom))
    tool_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    if version('py65') != '1.2.0': raise ValueError('reviewed py65 1.2.0 required')
    from py65.devices.mpu6502 import MPU
    utility_paths = [Path(__file__), ROOT/'scripts/mechanics_probe.py', ROOT/'scripts/reference_state.py',
                     ROOT/'scripts/reference_traces.py', Path(cases_path), ROOT/'references/disassembly-map.json',
                     Path(inspect.getfile(MPU))]
    fingerprints = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in utility_paths}
    metadata = json.loads(Path(cases_path).read_text())
    if metadata.get('schema_version') != 1 or metadata.get('source_sha256') != source['sha256']:
        raise ValueError('CPU case source/schema mismatch')
    source_map = json.loads((ROOT/'references/disassembly-map.json').read_text())
    if source_map['source_sha256'] != source['sha256']: raise ValueError('CPU boundary source mismatch')
    data = Path(rom).read_bytes(); boundaries = instruction_boundaries(data, source_map['classification']['code_ranges'])
    selected = [case for case in metadata['cases'] if not case.get('mmio')]
    cases = selected + arithmetic_vectors(data)
    out = private_output(out); out.mkdir(parents=True, exist_ok=False)
    initial, backend = poweron_capsule(rom, out/'poweron', stella=stella)
    results = []
    for index, case in enumerate(cases):
        complete_case = {**case, 'watch': [f'{address:02X}' for address in range(0x80, 0x100)]}
        expected = execute_slice(data, complete_case, boundaries)
        if expected['hardware_reads']: raise ValueError('undeclared CPU-only domain: observed MMIO read')
        fixture = prepare_cpu_fixture(initial, case)
        script = '\n'.join(['base dec', 'loadState 0', 'saveState 0'] + ['step'] * expected['instructions']
                           + ['saveState 1', 'exitRom', ''])
        states, observed_backend = run_debugger(rom, script, out/f'case-{index:04d}', fixture, stella)
        if backend != observed_backend or set(states) != {0, 1}: raise ValueError('CPU backend/checkpoint mismatch')
        actual = decode_state(states[1]); differences = compare_cpu(expected, actual)
        results.append({'id': case['id'], 'instructions': expected['instructions'], 'matched': not differences,
                        'differences': differences, 'stella_state_sha256': actual['state_sha256'],
                        'py65_cpu_ram_sha256': hashlib.sha256(json.dumps(expected, sort_keys=True).encode()).hexdigest()})
        if index % 25 == 0: print(f'Independent CPU check {index+1}/{len(cases)}; mismatches={sum(not r["matched"] for r in results)}', flush=True)
    verify_fingerprints(fingerprints); verified_input(Path(rom))
    report = {'schema_version': 1, 'source': source, 'stella': backend, 'py65': version('py65'),
              'tool_source_commit': tool_commit,
              'py65_cpu_source_sha256': fingerprints[str(Path(inspect.getfile(MPU)))],
              'utility_sha256': fingerprints[str(Path(__file__))],
              'cases_sha256': fingerprints[str(Path(cases_path))],
              'mechanics_cases_checked': len(selected), 'arithmetic_boundary_vectors': len(cases)-len(selected),
              'excluded_constant_mmio_cases': len(metadata['cases'])-len(selected),
              'matched': sum(r['matched'] for r in results), 'total': len(results), 'results': results,
              'limits': ['Controlled CPU/RAM fixtures, not naturally reached states, TIA timing or geometry',
                         'ADC/SBC boundary matrix, not exhaustive opcode/NMOS silicon conformance',
                         'All128 RAM bytes and A/X/Y/P/SP/PC checked after identical instruction count']}
    (out/'summary.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=ROOT/'references/roms/frostbite.bin')
    parser.add_argument('--cases', type=Path, default=ROOT/'references/mechanics-cases.json')
    parser.add_argument('--stella', default='stella')
    parser.add_argument('--output', type=Path, default=ROOT/'outputs/reference-cpu/summary.json')
    args = parser.parse_args(argv)
    try:
        verified_input(args.rom)
        parent = ROOT/'outputs/reference-cpu'; parent.mkdir(parents=True, exist_ok=True)
        out = Path(tempfile.mkdtemp(prefix='capture-', dir=parent))/'raw'
        report = check_cpu(args.rom, args.cases, out, args.stella)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2)+'\n')
        print(f'Independent CPU comparison: {report["matched"]}/{report["total"]}; raw evidence {out}')
        return 0 if report['matched'] == report['total'] else 1
    except (OSError, ValueError, KeyError, TypeError, ImportError, subprocess.SubprocessError) as error:
        print(f'Independent CPU check failed: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__': sys.exit(main())
