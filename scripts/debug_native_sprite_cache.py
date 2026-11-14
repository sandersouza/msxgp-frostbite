"""Read-only PAL cache investigation; deliberately stops before acceptance."""
import argparse
from pathlib import Path
import subprocess
from render_build import symbols
from native_name_palette_trial_check import check


def debug(build,out,mode):
    build,out=build.resolve(),out.resolve();s=symbols(build/'presentation.sym');old_run=subprocess.run
    s['sr_upload']=0x566B  # maintained sr-gates.asm public ABI, not exported in parent symbols
    def run(args,*a,**kw):
        if isinstance(args,list) and '-script' in args and 'openmsx' in Path(args[0]).name.lower():
            p=Path(args[args.index('-script')+1]);t=p.read_text()
            t+=f'''
set sprite_trace [open {{{out/'sprite-debug.tsv'}}} w]
proc sprite_log {{event}} {{
 set n [debug read memory {s['t_commits']}]
 if {{$n<140 || $n>170}} {{return}}
 puts $::sprite_trace "$event $n [debug read memory {s['PAGE']}] [debug read memory {s['p_w_row']}] [debug read memory {s['p_w_group']}] [debug read memory {s['p_w_base']}] [reg AF] [reg HL] [reg DE] [binary encode hex [debug read_block memory 0xE8A0 24]] [binary encode hex [debug read_block VRAM 0x3D60 32]] [binary encode hex [debug read_block memory 0xF023 4]]";flush $::sprite_trace
}}
debug set_bp {s['x_hybrid']} {{}} {{sprite_log hybrid}}
debug set_bp {s['sr_upload']} {{}} {{sprite_log upload}}
debug set_bp {s['t_irq.committed']} {{}} {{sprite_log commit}}
'''
            p.write_text(t);result=old_run(args,*a,**kw)
            if result.returncode:raise RuntimeError('emulator debug capture failed; inspect emulator.log')
            raise RuntimeError('DIAGNOSTIC_TRACE_READY: no acceptance claim')
        return old_run(args,*a,**kw)
    subprocess.run=run
    try:check(build,out,mode)
    finally:subprocess.run=old_run


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--mode',default='pal')
    a=p.parse_args();debug(a.build,a.out,a.mode)
