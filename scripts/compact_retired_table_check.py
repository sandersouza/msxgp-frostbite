"""Guard every retired collision byte, including opcode/data reads during boot."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import compact_game_probe
import compact_grid_ram_check
from render_build import symbols


def check(build,out,mode):
    build=build.resolve();out=out.resolve();m=json.loads((build/'build.json').read_bytes())
    ranges=m.get('compact_retired_pools',{}).get('ranges')
    if not ranges:raise ValueError('declared retired pools required')
    if any(row['address']!=0x8000 for row in ranges):raise ValueError('bank-prefix pools required')
    ends=' '.join(f'{row["bank"]} {row["address"]+row["size"]-1}' for row in ranges)
    rom=(build/m['rom']['filename']).read_bytes();entry=int.from_bytes(rom[2:4],'little')
    s=symbols(build/'presentation.sym');original_run=subprocess.run;marker=out/'retired-guard-armed.txt'
    def run(args,*a,**kw):
        if isinstance(args,list) and '-script' in args and 'openmsx' in Path(args[0]).name.lower():
            path=Path(args[args.index('-script')+1]);text=path.read_text()
            fail='fail_matrix' if 'proc guard_matrix ' in text else 'fail'
            text+=f'''
set pool_guard 0
set pool_watch {{}}
set pool_ends [dict create {ends}]
debug set_bp {entry} {{!$::pool_guard}} {{
 set ::pool_guard 1
 set f [open {{{marker}}} w];puts $f "boot entry armed";close $f
}}
debug set_bp {s['contact_compact']} {{$::pool_guard}} {{{fail} retired-contact-decoder}}
debug set_watchpoint write_mem 0x7000 {{$::pool_guard}} {{
 if {{$::pool_watch ne {{}}}} {{debug remove_watchpoint $::pool_watch;set ::pool_watch {{}}}}
 set bank $::wp_last_value
 if {{[dict exists $::pool_ends $bank]}} {{
  set ::pool_watch [debug set_watchpoint read_mem [list 32768 [dict get $::pool_ends $bank]] {{$::pool_guard}} {{{fail} retired-collision-read}}]
 }}
}}
'''
            path.write_text(text)
        return original_run(args,*a,**kw)
    subprocess.run=run
    try:
        result=(compact_game_probe.check if mode=='matrix' else compact_grid_ram_check.guarded)(build,out,mode)
    finally:subprocess.run=original_run
    if not marker.exists():raise ValueError('retirement guard never armed')
    receipt=dict(complete=True,mode=mode,rom_sha256=m['rom']['sha256'],
        retired_physical_bytes=m['compact_retired_pools']['retired_physical_bytes'],
        guard_starts_at_cartridge_entry=True,forbidden_cpu_fetch_or_data_reads=0,old_decoder_calls=0,
        original_cold_guards_retained=True,producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (out/'retired-table-check.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--mode',choices=('ntsc','pal','bear-ntsc','bear-pal','matrix'),required=True)
    a=p.parse_args();check(a.build,a.out,a.mode)
