"""Complete input-pin replay against the exact progression cartridge."""
import argparse
import json
from pathlib import Path

from hazard_check import run_target
import hazard_paced
import hazard_routes
from progression_build import OUT, FILES, expected_pixels, presentation
import progression_routes
from reference_provenance import audit_manifest
from reference_traces import control_commands, private_output
from stella_floe import digest
from trace_compare import validate_trace

HELPERS = ('scripts/progression_play.py', 'scripts/progression_build.py', 'scripts/progression_native.tcl')
HAZARD_KINDS = ('bear-chase', 'bear-refuge', 'fish-envelope', 'threat-push')


def input_records(inputs, points):
    if not inputs or len(inputs) != len(points):
        raise ValueError('complete original inputs and source points required')
    result = bytearray()
    for sample, point in zip(inputs, points):
        control_commands(sample)
        if (point.get('input') != sample or len(point.get('ram', [])) != 128
                or point['ram'][0x47] not in (0, 1)):
            raise ValueError('original raw input/checkpoint mismatch')
        # Preserve BOTH original nibbles. The actual device harness samples the
        # source-selected controller at every boundary, including inside a turn.
        # An inactive held pin is not silently rewritten in the original trace.
        result.extend((sample['swcha'], sample['swchb'], int(sample['fire'][0]), int(sample['fire'][1])))
    return bytes(result)


def source_helpers(receipt):
    if receipt.get('kind') in progression_routes.KINDS: return progression_routes.HELPERS
    if receipt.get('kind') in HAZARD_KINDS: return hazard_routes.HELPERS
    raise ValueError('known explicit source route contract required')


def assess_receipt(points, receipt):
    source_helpers(receipt)
    if receipt['kind'] in progression_routes.KINDS:
        return progression_routes.assess(points, receipt['kind'], receipt['active_start'])
    return hazard_paced.assess_receipt(points, receipt)


def natural(source, out, build_dir=OUT, explore=False, inject='none'):
    source = Path(source); receipt = json.loads((source / 'route.json').read_text())
    helpers = source_helpers(receipt); audit_manifest(receipt, helpers)
    if receipt.get('clean_start') is not True or any(digest(source / n) != sha for n, sha in receipt['files'].items()):
        raise ValueError('clean immutable original route required')
    trace = json.loads((source / 'trace.json').read_text()); validate_trace(trace); progression_routes.validate_policy(trace['policy'])
    inputs = json.loads((source / 'inputs.json').read_text()); records = input_records(inputs, trace['steps'])
    expected = [{'ram': p['ram'], 'registers': {k: p['cpu'][k] for k in ('a', 'x', 'y', 'p', 'sp')}} for p in trace['steps']]
    report, actual = run_target(out, build_dir, records, expected, natural=True, explore=explore, inject=inject,
        build_files=FILES, target_script='scripts/progression_native.tcl', extra_symbols=('native_return',),
        additional_helpers=(*helpers, *HELPERS))
    points = [{**p, 'index': i} for i, p in enumerate(actual)]
    assessment = assess_receipt(points, receipt)
    if assessment != receipt['assessment']: raise ValueError('actual native progression/turn/terminal milestones differ')
    report.update(assessment=assessment, original_route_sha256=digest(source / 'route.json'),
        scope='Actual MSX1 cold initialization and real keyboard/console sampling of source-selected controller pins. Complete original CPU/all128RAM and explicit milestones match; no source/contact injections. Paced/manual/physical acceptance separate.')
    (private_output(out) / 'natural.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def paced(source, out, build_dir=OUT, family='ntsc', layout=0, width=0, explore=False):
    receipt = json.loads((Path(source) / 'route.json').read_text())
    return hazard_paced.capture(out, build_dir, source, family, explore, layout, width,
        source_helpers=source_helpers(receipt), build_files=FILES, assessor=assess_receipt,
        pixels=expected_pixels, scene_builder=presentation, input_encoder=input_records, additional_helpers=HELPERS)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True); p.add_argument('--out', type=Path, required=True)
    p.add_argument('--build-dir', type=Path, default=OUT); p.add_argument('--paced', action='store_true')
    p.add_argument('--family', choices=('ntsc', 'pal'), default='ntsc')
    p.add_argument('--layout', type=int, choices=(0, 1), default=0); p.add_argument('--width', type=int, choices=(0, 1), default=0)
    p.add_argument('--explore', action='store_true'); p.add_argument('--inject', choices=('none', 'score', 'record', 'player'), default='none')
    args = p.parse_args()
    if args.paced:
        if args.inject != 'none': p.error('paced faults are exercised by the dense benchmark')
        r = paced(args.source, args.out, args.build_dir, args.family, args.layout, args.width, args.explore)
    else: r = natural(args.source, args.out, args.build_dir, args.explore, args.inject)
    print(json.dumps({k: r[k] for k in ('cases', 'source_steps', 'frames', 'max_native_cycles', 'max_busy_cycles', 'assessment') if k in r}, indent=2))
