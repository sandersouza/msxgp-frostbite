"""Collect current physical coverage and cold RAM for the native linker audit.

Coverage remains a lower bound, never a dead-code removal certificate.
"""
import argparse
import json
from pathlib import Path
import subprocess

from compact_candidate_live_probe import candidate_observer
from compact_inventory import read_trace
from compact_live_probe import instrument_harness, sha
import compact_grid_window_check
from render_build import symbols


def probe(build, out, mode):
    build, out = build.resolve(), out.resolve()
    m = json.loads((build/'build.json').read_bytes())
    artifact = build/m['rom']['filename']
    if sha(artifact) != m['rom']['sha256']:
        raise ValueError('bound candidate required')
    rom = artifact.read_bytes()
    s = symbols(build/'presentation.sym')
    original_run = subprocess.run

    def run(args, *a, **kw):
        if isinstance(args, list) and '-script' in args and 'openmsx' in Path(args[0]).name.lower():
            p = Path(args[args.index('-script')+1])
            observer = candidate_observer(out, int.from_bytes(rom[2:4], 'little'), s, mode)
            observer += f'''
set flat_saved 0
debug set_bp {s['t_main.frame']} {{!$::flat_saved}} {{
 set ::flat_saved 1
 set f [open {{{out/'initial-memory.bin'}}} wb]
 puts -nonewline $f [debug read_block memory 0 65536];close $f
 set f [open {{{out/'initial-vram.bin'}}} wb]
 puts -nonewline $f [debug read_block VRAM 0 16384];close $f
}}
'''
            p.write_text(instrument_harness(p.read_text(), observer, mode))
            kw['timeout'] = 1200
        return original_run(args, *a, **kw)

    subprocess.run = run
    try:
        compact_grid_window_check.check(build, out, mode)
    finally:
        subprocess.run = original_run
    phases = read_trace((out/'rom-reads.tsv').read_text(), len(rom))
    banks = {}
    for bank in range(256):
        rows = {phase: sum(bank*16384 <= x < (bank+1)*16384 for x in values)
                for phase, values in phases.items()}
        if any(rows.values()):
            banks[bank] = rows
    result = dict(complete=True, mode=mode, rom_sha256=m['rom']['sha256'],
        observed_bytes={k: len(v) for k, v in phases.items()}, banks=banks,
        coverage_is_lower_bound=True, initialized_memory_is_not_runtime_liveness_proof=True,
        inherited_full_game_oracles_retained=True, producer_sha256=sha(Path(__file__)))
    (out/'flat-probe.json').write_text(json.dumps(result, indent=2)+'\n')
    print(result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--mode', choices=('ntsc', 'pal', 'bear-ntsc', 'bear-pal', 'matrix'), required=True)
    args = parser.parse_args()
    probe(args.build, args.out, args.mode)
