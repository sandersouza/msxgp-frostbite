"""Map current native migration consumers; coverage is not a liveness proof."""
import argparse
import json
from pathlib import Path
import subprocess

from compact_candidate_live_probe import candidate_observer
from compact_inventory import read_trace
from compact_live_probe import instrument_harness,sha
from native_name_palette_trial_check import check
from render_build import symbols


def probe(build,out,mode):
    build,out=build.resolve(),out.resolve()
    m=json.loads((build/'build.json').read_bytes());artifact=build/m['rom']['filename']
    if sha(artifact)!=m['rom']['sha256']:raise ValueError('bound source required')
    s=symbols(build/'presentation.sym');rom=artifact.read_bytes();old_run=subprocess.run
    def run(args,*a,**kw):
        if isinstance(args,list) and '-script' in args and 'openmsx' in Path(args[0]).name.lower():
            p=Path(args[args.index('-script')+1])
            observer=candidate_observer(out,int.from_bytes(rom[2:4],'little'),s,mode)
            p.write_text(instrument_harness(p.read_text(),observer,mode));kw['timeout']=1200
        return old_run(args,*a,**kw)
    subprocess.run=run
    try:check(build,out,mode)
    finally:subprocess.run=old_run
    phases=read_trace((out/'rom-reads.tsv').read_text(),len(rom))
    banks={bank:{phase:sum(bank*16384<=a<(bank+1)*16384 for a in values) for phase,values in phases.items()}
           for bank in range(256)}
    result=dict(complete=True,mode=mode,rom_sha256=m['rom']['sha256'],coverage_is_lower_bound=True,
                banks={b:v for b,v in banks.items() if any(v.values())},producer_sha256=sha(Path(__file__)),
                scope='Original source/RGB/physical owner/IRQ oracles retained; exact physical reads, no unobserved byte classified dead.')
    (out/'native-flat-live-set.json').write_text(json.dumps(result,indent=2)+'\n');print(result)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--mode',choices=('ntsc','pal','bear-ntsc','bear-pal','matrix'),required=True)
    a=p.parse_args();probe(a.build,a.out,a.mode)
