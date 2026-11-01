"""Independent full original phases versus actual cartridge progression cases."""
import argparse
import json
from pathlib import Path

from environment import ROOT
from floe_model import visible_state
from floe_reference import visible_reference
from progression_build import OUT, FILES
from hazard_check import run_target
from hazard_query import RawContacts
from native_contract import compare, reference, run_contract
from progression_cases import phase_cases, primitive_cases, validate_primitive, validate_phase
from reference_state import decode_state
from stella_floe import digest

HELPERS = ('scripts/progression_cases.py', 'scripts/progression_check.py',
           'scripts/floe_reference.py', 'scripts/floe_model.py')


def primitives(explore=False):
    rom = (ROOT / 'references/roms/frostbite.bin').read_bytes()
    cases = primitive_cases()
    for case in cases:
        validate_primitive(case, reference(rom, case))
    return run_contract(cases, explore=explore)


def check(out, build_dir, reader, initial_path, explore=False):
    base = decode_state(Path(initial_path).read_bytes())
    rom = (ROOT / 'references/roms/frostbite.bin').read_bytes()
    records = bytearray()
    expected, summary = [], []
    for name, ram in phase_cases(base['ram']):
        contacts = reader.contacts(ram)
        visible = visible_reference(rom, ram, base['cpu'], contacts)
        compare(visible, visible_state(rom, ram, base['cpu'], contacts))
        console = int(name.split('-')[1], 16) if name.startswith('console-') else 63
        case = {'id': name, 'start': 'F476', 'stops': ['F019'],
                'registers': visible['registers'],
                'ram': {f'{i + 128:02X}': f'{v:02X}' for i, v in enumerate(visible['ram'])},
                'mmio': {'0280': 'FF', '0282': f'{console:02X}', '0284': '00', '000C': '8C', '000D': '8C'},
                'limit': 12000}
        want = reference(rom, case)
        validate_phase(name, ram, want['ram'])
        records.extend(ram)
        records.extend(base['cpu'][key] for key in ('a', 'x', 'y', 'p', 'sp'))
        records.extend((255, console, 0))
        expected.append(want)
        summary.append({'id': name, 'ram': {f'{a:02X}': want['ram'][a - 128]
            for a in (*range(0xC5, 0xD4), 0xE5, 0xE7, 0xF1, 0xF4)}})
    reader.verify_consumed()
    report, _ = run_target(out, build_dir, bytes(records), expected,
        step_fixture=True, explore=explore, additional_helpers=HELPERS, build_files=FILES)
    report.update(scenarios=summary, initial_sha256=digest(initial_path),
        scope='Declared controlled RAM fixtures; actual source-clock contacts and complete original CPU/all128RAM versus actual MSX1 native phase. Continuous play and paced/manual/physical acceptance are separate.')
    (Path(out) / 'progression.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--primitives', action='store_true')
    p.add_argument('--out', type=Path)
    p.add_argument('--build-dir', type=Path, default=OUT)
    for name in ('floes', 'edge', 'ordinary', 'shore', 'initial'):
        p.add_argument('--' + name, type=Path)
    p.add_argument('--explore', action='store_true')
    args = p.parse_args()
    if args.primitives:
        primitives(args.explore)
    else:
        if any(getattr(args, n) is None for n in ('out', 'floes', 'edge', 'ordinary', 'shore', 'initial')):
            p.error('full-phase check requires output, audited catalogs and initial capsule')
        r = check(args.out, args.build_dir, RawContacts(args.floes, args.edge, args.ordinary, args.shore), args.initial, args.explore)
        print(json.dumps({'cases': r['cases'], 'max_native_cycles': r['max_native_cycles']}))
