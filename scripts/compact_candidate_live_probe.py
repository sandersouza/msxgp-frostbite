"""Physical coverage for compact candidates, preserving retirement/pixel guards.

Observed bytes remain a lower bound, never permission to prune unseen states.
"""
import argparse
import json
from pathlib import Path
import subprocess

from compact_inventory import read_trace
from compact_live_probe import observer_tcl,instrument_harness,sha
import compact_retired_graphics_check
from render_build import symbols


def probe(build,out,mode):
    build=build.resolve();out=out.resolve();m=json.loads((build/'build.json').read_bytes())
    artifact=build/m['rom']['filename'];rom=artifact.read_bytes();producer=sha(Path(__file__))
    if sha(artifact)!=m['rom']['sha256']:raise ValueError('candidate changed')
    s=symbols(build/'presentation.sym');original_run=subprocess.run
    def run(args,*a,**kw):
        if isinstance(args,list) and '-script' in args and 'openmsx' in Path(args[0]).name.lower():
            p=Path(args[args.index('-script')+1])
            p.write_text(instrument_harness(p.read_text(),observer_tcl(out,int.from_bytes(rom[2:4],'little'),s),mode))
            kw['timeout']=900
        return original_run(args,*a,**kw)
    subprocess.run=run
    try:compact_retired_graphics_check.check(build,out,mode)
    finally:subprocess.run=original_run
    phases=read_trace((out/'rom-reads.tsv').read_text(),len(rom))
    if sha(artifact)!=m['rom']['sha256'] or sha(Path(__file__))!=producer:raise ValueError('producer or candidate changed')
    result=dict(complete=True,mode=mode,rom_sha256=m['rom']['sha256'],producer_sha256=producer,
        observed_bytes={k:len(v) for k,v in phases.items()},observed_union_bytes=len(phases['startup']|phases['runtime']),
        retired_collision_and_graphics_guards_retained=True,coverage_is_lower_bound=True)
    (out/'candidate-live-set.json').write_text(json.dumps(result,indent=2)+'\n');print(result)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--mode',choices=('ntsc','pal','bear-ntsc','bear-pal','matrix'),required=True)
    a=p.parse_args();probe(a.build,a.out,a.mode)
