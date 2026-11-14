"""Forbid resident pointer-directory reads from cartridge entry onward."""
import argparse
import json
from pathlib import Path
import subprocess

from build_compact_packet_experiment import digest
import compact_retired_floe_asset_check


def check(build,out,mode):
    build=build.resolve();out=out.resolve();m=json.loads((build/'build.json').read_bytes());node=m.get('compact_retired_resident',{})
    ranges=node.get('ranges')
    if not ranges:raise ValueError('explicit reclaimed resident ranges required')
    rom=(build/m['rom']['filename']).read_bytes();entry=int.from_bytes(rom[2:4],'little');marker=out/'resident-guard-armed.txt'
    original_run=subprocess.run
    def run(args,*a,**kw):
        if isinstance(args,list) and '-script' in args and 'openmsx' in Path(args[0]).name.lower():
            p=Path(args[args.index('-script')+1]);text=p.read_text();fail='fail_matrix' if 'proc guard_matrix ' in text else 'fail'
            text+=f'''
set resident_retirement_guard 0
debug set_bp {entry} {{!$::resident_retirement_guard}} {{
 set ::resident_retirement_guard 1
 set f [open {{{marker}}} w];puts $f "boot entry armed";close $f
}}
'''
            for row in ranges:
                first=row['address'];end=first+row['size']-1
                if not 0x4000<=first<=end<0x8000:raise ValueError('resident cartridge range required')
                text+=f'debug set_watchpoint read_mem {{{first} {end}}} {{$::resident_retirement_guard}} {{{fail} "retired-resident-read address=$::wp_last_address"}}\n'
            p.write_text(text)
        return original_run(args,*a,**kw)
    subprocess.run=run
    try:compact_retired_floe_asset_check.check(build,out,mode)
    finally:subprocess.run=original_run
    if not marker.exists():raise ValueError('resident guard never armed')
    result=dict(complete=True,mode=mode,rom_sha256=m['rom']['sha256'],reclaimed_resident_bytes=node['reclaimed_bytes'],
        forbidden_resident_cpu_reads=0,cold_entry_guard_armed=True,all_original_oracles_and_retirement_guards_retained=True,
        producer_sha256=digest(Path(__file__).read_bytes()))
    (out/'resident-retirement-check.json').write_text(json.dumps(result,indent=2)+'\n');print(result)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--mode',choices=('ntsc','pal','bear-ntsc','bear-pal','matrix'),required=True)
    a=p.parse_args();check(a.build,a.out,a.mode)
