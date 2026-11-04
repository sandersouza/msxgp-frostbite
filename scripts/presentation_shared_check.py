"""Run the source matrix with shared-ice physical-reference and RAM audits."""
import argparse
import json
from pathlib import Path
import subprocess
import runpy
import sys

import presentation_matrix_check as matrix
from presentation_fixed_ownership import audit_row
from presentation_shared_ownership import audit_active_references, audit_pool

MATRIX_CHECK = matrix.check

def check(build, out, limit=2115):
    meta = json.loads((build/'build.json').read_text())
    if meta['shared_ice']['ram'] != [0xE800, 0xF240]:
        raise ValueError('explicit shared-pool RAM declaration required')
    original_run = subprocess.run
    def run(args, *a, **kw):
        if isinstance(args, list) and '-script' in args and 'openmsx' in Path(args[0]).name.lower():
            script = Path(args[args.index('-script')+1])
            text = script.read_text()
            text = text.replace('memory 0xE800 0xB40', 'memory 0xF240 0x100')
            text = text.replace('memory 0xE800 [string repeat [binary format c 165] 0xB40]',
                                'memory 0xF240 [string repeat [binary format c 165] 0x100]')
            text = text.replace('[string repeat [binary format c 165] 0xB40]',
                                '[string repeat [binary format c 165] 0x100]')
            text = text.replace('set captures [open ', f'set residency [open {{{out/"residency.bin"}}} wb]\nset captures [open ', 1)
            text = text.replace('incr ::index', 'puts -nonewline $::residency "[debug read_block memory 0xE800 2624][debug read_block memory 0xDE00 512]"\n        incr ::index')
            script.write_text(text)
        return original_run(args, *a, **kw)
    old_active, old_fixed = matrix.audit_active, matrix.audit_fixed
    matrix.audit_active = audit_active_references
    matrix.audit_fixed = lambda *a, **kw: audit_row(*a, **kw, shared_ice=True)
    subprocess.run = run
    try:
        result = MATRIX_CHECK(build, out, all_source=True, limit=limit, explore=True)
    finally:
        subprocess.run = original_run
        matrix.audit_active, matrix.audit_fixed = old_active, old_fixed
    pools = (out/'residency.bin').read_bytes()
    owners = (out/'ownership.bin').read_bytes()
    if len(pools) != limit*3136:
        raise ValueError('incomplete physical residency snapshots')
    audit = [audit_pool(pools[i*3136:i*3136+2624], pools[i*3136+2624:(i+1)*3136],
                       owners[i*4110+1536:i*4110+3840]) for i in range(limit)]
    result['shared_ice_references_accepted'] = True
    result['shared_ice_pool_audit'] = audit
    result['shared_checker_scope'] = 'Original pixels/ABI/IO retained; active protection follows actual NAME references across physical ID pages. F240..F33F remains guarded.'
    (out/'check.json').write_text(json.dumps(result,indent=2)+'\n')
    print(dict(complete=result['complete'],cases=result['cases'],different_frames=result['different_frames']))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--limit', type=int, default=2115)
    parser.add_argument('--density', action='store_true')
    args = parser.parse_args()
    if args.density:
        from environment import ROOT
        script = ROOT/'outputs/presentation/playfield-m-c/density_matrix.py'
        sys.argv = [str(script),str(args.build.resolve()),str(args.out.resolve())]
        matrix.check = lambda build,out,**kw: check(build,out,kw['limit'])
        runpy.run_path(str(script),run_name='__main__')
    else:
        check(args.build.resolve(),args.out.resolve(),args.limit)
