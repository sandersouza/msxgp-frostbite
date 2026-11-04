"""Original scene matrix with independent lazy fixed-ice metadata proof."""
import argparse
import json
from pathlib import Path
import runpy
import subprocess
import sys

import presentation_matrix_check as matrix
from presentation_fixed_ownership import audit_row
from presentation_prepared_ownership import decorate_owners
from render_build import symbols

MATRIX_CHECK=matrix.check


def check(build,out,limit=2115):
    meta=json.loads((build/'build.json').read_text());rom=(build/meta['rom']['filename']).read_bytes()
    s=symbols(build/'presentation.sym')
    deltas=list(rom[s['p_template_deltas']-16384:s['p_template_deltas']-16384+10])
    original_run=subprocess.run;old_fixed=matrix.audit_fixed;index=0
    def fixed(raw,vram,tile,**kw):
        nonlocal index
        bands=(out/'band-records.bin').read_bytes()
        if len(bands)!=limit*72:raise ValueError('incomplete saved physical-owner snapshots')
        at=index*72;record=bands[at:at+72];index+=1
        decorated=decorate_owners(raw,record[:32],record[32:64],record[64:],rom,deltas)
        return audit_row(decorated,vram,tile,**kw)
    def run(args,*a,**kw):
        if isinstance(args,list) and '-script' in args and 'openmsx' in Path(args[0]).name.lower():
            script=Path(args[args.index('-script')+1]);text=script.read_text()
            text=text.replace('set captures [open ',f'set pkbands [open {{{out/"band-records.bin"}}} wb]\nset captures [open ',1)
            text=text.replace('incr ::index','puts -nonewline $::pkbands "[debug read_block memory 0xC1D1 32][debug read_block memory 0xE5C0 32][debug read_block memory 0xC1F1 8]"\n        incr ::index')
            text=text.replace('close $::captures;close $::timing;','close $::pkbands;close $::captures;close $::timing;')
            script.write_text(text)
        return original_run(args,*a,**kw)
    subprocess.run=run;matrix.audit_fixed=fixed
    try:result=MATRIX_CHECK(build,out,all_source=True,limit=limit,explore=True)
    finally:subprocess.run=original_run;matrix.audit_fixed=old_fixed
    if index!=limit:raise ValueError('missing prepared role audits')
    result['prepared_band_ownership_accepted']=True
    result['prepared_checker_scope']='Fixed-generation roles and active full-page protection retained; source-packet keys independently reconstructed from saved owner/tuple, obsolete per-tile ice metadata required FF.'
    (out/'check.json').write_text(json.dumps(result,indent=2)+'\n')
    print(dict(complete=result['complete'],cases=result['cases'],different_frames=result['different_frames']))
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--limit',type=int,default=2115);parser.add_argument('--density',action='store_true')
    args=parser.parse_args()
    if args.density:
        from environment import ROOT
        script=ROOT/'outputs/presentation/playfield-m-c/density_matrix.py'
        sys.argv=[str(script),str(args.build.resolve()),str(args.out.resolve())]
        matrix.check=lambda build,out,**kw:check(build,out,kw['limit'])
        runpy.run_path(str(script),run_name='__main__')
    else:check(args.build.resolve(),args.out.resolve(),args.limit)
