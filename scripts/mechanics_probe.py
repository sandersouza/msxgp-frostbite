#!/usr/bin/env python3
"""Bounded CPU-slice research with declared MMIO, not a TIA/gameplay emulator."""
import argparse
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import sys

from reference_inventory import MANIFEST, ROOT, load_manifest, verified_input


class SliceBus:
    """6507 address decode; hardware samples are constant, writes only recorded."""
    def __init__(self, rom, samples):
        if len(rom) != 4096:
            raise ValueError('slice bus requires 4096 ROM bytes')
        self.rom = rom
        self.ram = bytearray(128)
        self.samples = samples
        self.reads = []
        self.writes = []

    @staticmethod
    def decode(address, write=False):
        address &= 0x1fff
        if address & 0x1000:
            return 'rom', address & 0xfff
        if not address & 0x80:
            return 'hardware', address & (0x3f if write else 0x0f)
        if not address & 0x200:
            return 'ram', address & 0x7f
        return 'hardware', 0x280 | (address & (0x1f if write else 0x07))

    def __getitem__(self, address):
        kind, offset = self.decode(address)
        if kind == 'rom':
            return self.rom[offset]
        if kind == 'ram':
            return self.ram[offset]
        if offset not in self.samples:
            raise ValueError(f'undeclared hardware read {offset:04X}')
        value = self.samples[offset]
        self.reads.append({'address': f'{offset:04X}', 'value': f'{value:02X}'})
        return value

    def __setitem__(self, address, value):
        kind, offset = self.decode(address, write=True)
        if kind == 'rom':
            raise ValueError(f'ROM write {address:04X}')
        if kind == 'ram':
            self.ram[offset] = value
        else:
            self.writes.append({'address': f'{offset:04X}', 'value': f'{value:02X}'})


def instruction_boundaries(data, ranges):
    from py65.devices.mpu6502 import MPU
    from py65.disassembler import Disassembler
    if len(data) != 4096:
        raise ValueError('boundary decode requires 4096 bytes')
    memory = bytearray(65536)
    memory[0xf000:] = data
    disassembler = Disassembler(MPU(memory=memory))
    boundaries = set()
    for first, last in ranges:
        pc, end = int(first, 16), int(last, 16) + 1
        if not 0xf000 <= pc < end <= 0x10000:
            raise ValueError('invalid code range')
        while pc < end:
            size, mnemonic = disassembler.instruction_at(pc)
            if mnemonic.startswith('???') or pc + size > end:
                raise ValueError('invalid code range decoding')
            boundaries.add(pc)
            pc += size
    return boundaries


def execute_slice(data, case, boundaries=None):
    # Import only after CLI canonical verification; unit fixtures can call directly.
    from py65.devices.mpu6502 import MPU
    bus = SliceBus(data, {int(k, 16): int(v, 16) for k, v in case.get('mmio', {}).items()})
    for address, value in case.get('ram', {}).items():
        address = int(address, 16)
        if not 0x80 <= address <= 0xff:
            raise ValueError('initial RAM address outside 80-FF')
        bus[address] = int(value, 16)
    start = int(case['start'], 16)
    stops = {int(value, 16) for value in case['stops']}
    if not 0 <= start <= 65535 or not stops or any(not 0 <= v <= 65535 for v in stops):
        raise ValueError('slice requires valid start/stops')
    if boundaries is not None and not ({start} | stops) <= boundaries:
        raise ValueError(f"{case['id']}: start/stop is not a reviewed instruction boundary")
    cpu = MPU(memory=bus, pc=start)
    for name, value in case.get('registers', {}).items():
        if name not in ('a', 'x', 'y', 'p', 'sp') or type(value) is not int or not 0 <= value <= 255:
            raise ValueError('invalid initial CPU register')
        setattr(cpu, name, value)
    limit = case.get('limit', 10000)
    if type(limit) is not int or not 1 <= limit <= 100000:
        raise ValueError('instruction limit must be 1-100000')
    steps = 0
    while cpu.pc not in stops:
        if boundaries is not None and cpu.pc not in boundaries:
            raise ValueError(f"{case['id']}: execution left reviewed instruction boundaries at {cpu.pc:04X}")
        if steps >= limit:
            raise ValueError(f"{case['id']}: instruction limit {limit} exceeded")
        cpu.step()
        steps += 1
    watch = case.get('watch', list(case.get('ram', {})))
    if any(not 0x80 <= int(address, 16) <= 0xff for address in watch):
        raise ValueError('watch address outside 80-FF')
    result = {'id': case['id'], 'stop_pc': f'{cpu.pc:04X}', 'instructions': steps,
              'registers': {name: getattr(cpu, name) for name in ('a', 'x', 'y', 'p', 'sp')},
              'ram': {address.upper(): f'{bus[int(address, 16)]:02X}' for address in watch},
              'hardware_reads': bus.reads, 'hardware_writes': bus.writes}
    for address, expected in case.get('expect', {}).get('ram', {}).items():
        actual = bus[int(address, 16)]
        if actual != int(expected, 16):
            raise ValueError(f"{case['id']}: expected RAM[{address}]={expected}, observed {actual:02X}")
    for name, expected in case.get('expect', {}).get('registers', {}).items():
        if result['registers'][name] != expected:
            raise ValueError(f"{case['id']}: expected {name}={expected}, observed {result['registers'][name]}")
    if 'stop_pc' in case.get('expect', {}) and result['stop_pc'] != case['expect']['stop_pc']:
        raise ValueError(f"{case['id']}: unexpected stop {result['stop_pc']}")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path)
    parser.add_argument('--manifest', type=Path, default=MANIFEST)
    parser.add_argument('--cases', type=Path, default=ROOT / 'references/mechanics-cases.json')
    parser.add_argument('--output', type=Path, default=ROOT / 'outputs/mechanics/report.json')
    args = parser.parse_args(argv)
    try:
        rom = args.rom or ROOT / load_manifest(args.manifest)['input']['path']
        identity = verified_input(rom, args.manifest)
        backend = version('py65')
        if backend != '1.2.0':
            raise ValueError('requires reviewed py65 1.2.0; see requirements-reference.txt')
        cases_data = args.cases.read_bytes()
        cases = json.loads(cases_data)
        if cases.get('schema_version') != 1 or cases.get('source_sha256') != identity['sha256']:
            raise ValueError('case schema/source identity mismatch')
        data = rom.read_bytes()
        map_data = (ROOT / 'references/disassembly-map.json').read_bytes()
        source_map = json.loads(map_data)
        if source_map.get('source_sha256') != identity['sha256']:
            raise ValueError('disassembly map source identity mismatch')
        boundaries = instruction_boundaries(data, source_map['classification']['code_ranges'])
        results = [execute_slice(data, case, boundaries) for case in cases['cases']]
        verified_input(rom, args.manifest)
        report = {'schema_version': 1, 'source': identity, 'backend': {'py65': backend},
                  'utility_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  'cases_sha256': hashlib.sha256(cases_data).hexdigest(),
                  'disassembly_map_sha256': hashlib.sha256(map_data).hexdigest(),
                  'scope': 'Bounded CPU slices with explicit constant hardware inputs; no TIA, timers, bus cycles or reachable-state proof.',
                  'results': results}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + '\n')
        print(f'Passed {len(results)} bounded source CPU probes; report {args.output}')
        return 0
    except (OSError, ValueError, KeyError, TypeError, ImportError) as error:
        print(f'Mechanics probe failed: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
