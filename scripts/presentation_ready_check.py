"""Run unchanged native/IRQ oracles with explicit first-safe-field admission.

The legacy probe keeps its two-field default. This entrypoint verifies the new
ROM contract, installs only its clock-spacing validator, and separately binds
both validation producers. Pixel, owner, original CPU/RAM and IRQ checks remain
the original ones. Existing receipts are never rewritten after boundary binding.
"""
import argparse
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import runpy
import sys

from environment import ROOT
from presentation_fixed_clock import ram_code
import presentation_fixed_clock_probe as legacy
from presentation_ready_clock import clocks
from render_build import symbols


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_admission(build):
    meta = json.loads((build/'build.json').read_text())
    if meta['fixed_clock'].get('minimum_commit_interval_vblanks') != 1:
        raise ValueError('explicit one-field ROM contract required')
    rom = (build/meta['rom']['filename']).read_bytes()
    if hashlib.sha256(rom).hexdigest() != meta['rom']['sha256']:
        raise ValueError('ROM identity differs')
    code = ram_code(meta, rom)
    s = symbols(build/'presentation.sym')
    at = s['t_irq.commit']-4-s['t_prepare_gate']
    if code[at:at+4] != bytes.fromhex('fe013814'):
        raise ValueError('ready-picture admission bytes differ')
    return meta


@contextmanager
def ready_contract(build):
    verify_admission(build)
    prior = legacy.clocks
    legacy.clocks = clocks
    try:
        yield
    finally:
        legacy.clocks = prior


def check(build, out, mode, steps=2252):
    meta = verify_admission(build)
    paths = (Path(__file__).resolve(), ROOT/'scripts/presentation_ready_clock.py')
    producers = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    with ready_contract(build):
        if mode.startswith('boundary-'):
            from presentation_fixed_clock_boundaries import check as boundary
            family = 'pal' if mode == 'boundary-pal' else 'ntsc'
            boundary(build, out, family, expanded=(family == 'pal'),
                     negative_register=(mode == 'boundary-negative'))
        else:
            old_argv = sys.argv
            script = ROOT/'scripts/presentation_native_check.py'
            try:
                sys.argv = [str(script), str(build), str(out), mode, str(steps)]
                runpy.run_path(str(script), run_name='__main__')
            finally:
                sys.argv = old_argv
    if producers != {str(p.relative_to(ROOT)): sha(p) for p in paths}:
        raise ValueError('ready-admission producer changed during verification')
    for p in paths:
        (out/p.name).write_bytes(p.read_bytes())
    receipts = {p.name: sha(p) for p in out.glob('*check.json')}
    if not receipts:
        raise ValueError('underlying verification receipt missing')
    result = dict(complete=True, rom_sha256=meta['rom']['sha256'],
        minimum_commit_interval_vblanks=1, mode=mode, producers=producers,
        receipts=receipts, scope='Actual field indices unchanged. First-safe-field admission only; all native/IRQ oracles retained. Legacy two-field contract remains available.')
    (out/'ready-contract.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build', type=Path)
    parser.add_argument('out', type=Path)
    parser.add_argument('mode', choices=('ntsc','pal','matrix','density','header',
                                       'boundary-ntsc','boundary-pal','boundary-negative'))
    parser.add_argument('steps', type=int, nargs='?', default=2252)
    args = parser.parse_args()
    check(args.build.resolve(), args.out.resolve(), args.mode, args.steps)
