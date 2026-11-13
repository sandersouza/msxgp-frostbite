"""Guard startup-expanded grid RAM while retaining the complete game oracle."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from compact_game_probe import check
from compact_grid_name_probe import prepared_data
from compact_live_probe import CONTROL_SHA
from environment import ROOT
from render_build import symbols


def guarded(build,out,mode):
    build=build.resolve();out=out.resolve()
    m=json.loads((build/'build.json').read_bytes())
    if not m.get('compact_grid_experiment',{}).get('expanded_ram_rows'):
        raise ValueError('startup-expanded grid experiment required')
    control=ROOT/'outputs/presentation/credit-reference-at/build-final'
    cm=json.loads((control/'build.json').read_bytes())
    rom=(control/cm['rom']['filename']).read_bytes()
    if hashlib.sha256(rom).hexdigest()!=CONTROL_SHA:raise ValueError('sealed control required')
    assets,_,expected=prepared_data(rom)
    directory=bytes(17+index for index in assets['directory'])
    rows=b''.join(expected[assets['directory'].index(index)*256:assets['directory'].index(index)*256+256]
                  for index in range(22))
    s=symbols(build/'presentation.sym');original_run=subprocess.run
    marker=out/'grid-ram-validated.txt'
    def run(args,*a,**kw):
        if isinstance(args,list) and '-script' in args and 'openmsx' in Path(args[0]).name.lower():
            script=Path(args[args.index('-script')+1]);text=script.read_text()
            text+=f'''
set grid_ram_guard 0
debug set_bp {s['t_main.frame']} {{!$::grid_ram_guard}} {{
 if {{[debug read_block memory 0x1000 160] ne [binary format H* {directory.hex()}]}} {{fail expanded-grid-directory}}
 if {{[debug read_block memory 0x1100 5632] ne [binary format H* {rows.hex()}]}} {{fail expanded-grid-rows}}
 set ::grid_ram_guard 1
 set f [open {{{marker}}} w];puts $f "verified22templates8owners";close $f
}}
debug set_watchpoint write_mem {{0x1000 0x26FF}} {{$::grid_ram_guard}} {{fail immutable-grid-write}}
'''
            script.write_text(text)
        return original_run(args,*a,**kw)
    subprocess.run=run
    try:result=check(build,out,mode)
    finally:subprocess.run=original_run
    if not marker.exists():raise ValueError('expanded RAM was never checked')
    receipt=dict(complete=True,mode=mode,rom_sha256=m['rom']['sha256'],
        directory_bytes=160,expanded_rows_bytes=5632,boot_bytes_equal=True,
        runtime_writes=0,source=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        scope='Exact v30-derived startup RAM bytes plus CPU write guards during unchanged full-route source/pixel/owner checks.')
    (out/'grid-ram-check.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--mode',choices=('ntsc','pal','bear-ntsc','bear-pal'),required=True)
    a=p.parse_args();result=guarded(a.build,a.out,a.mode)
    print({k:result[k] for k in ('complete','family','active_pictures_per_second')})
