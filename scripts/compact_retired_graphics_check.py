"""Forbid physical reads of superseded graphics while keeping all pool guards."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import subprocess

import compact_retired_table_check


def check(build,out,mode):
    build=build.resolve();out=out.resolve();m=json.loads((build/'build.json').read_bytes())
    ranges=m.get('compact_retired_graphics',{}).get('ranges')
    if not ranges:raise ValueError('declared graphics retirement required')
    by_bank=defaultdict(list)
    for r in ranges:by_bank[r['bank']].append((r['address'],r['address']+r['size']))
    merged={}
    for bank,rows in by_bank.items():
        values=[]
        for a,b in sorted(rows):
            if values and a<=values[-1][1]:values[-1]=(values[-1][0],max(values[-1][1],b))
            else:values.append((a,b))
        merged[bank]=values
    entries=' '.join(str(bank)+' {'+' '.join('{'+str(a)+' '+str(b-1)+'}' for a,b in rows)+'}' for bank,rows in sorted(merged.items()))
    rom=(build/m['rom']['filename']).read_bytes();entry=int.from_bytes(rom[2:4],'little')
    marker=out/'graphics-guard-armed.txt';original_run=subprocess.run
    def run(args,*a,**kw):
        if isinstance(args,list) and '-script' in args and 'openmsx' in Path(args[0]).name.lower():
            path=Path(args[args.index('-script')+1]);text=path.read_text()
            fail='fail_matrix' if 'proc guard_matrix ' in text else 'fail'
            text+=f'''
set graphics_guard 0
set graphics_watches {{}}
set graphics_bank -1
set graphics_ranges [dict create {entries}]
debug set_bp {entry} {{!$::graphics_guard}} {{
 set ::graphics_guard 1
 set f [open {{{marker}}} w];puts $f "boot entry armed";close $f
}}
debug set_watchpoint write_mem 0x7000 {{$::graphics_guard}} {{
 if {{$::graphics_bank!=$::wp_last_value}} {{
  foreach wp $::graphics_watches {{debug remove_watchpoint $wp}}
  set ::graphics_watches {{}};set ::graphics_bank $::wp_last_value
  if {{[dict exists $::graphics_ranges $::graphics_bank]}} {{
   foreach range [dict get $::graphics_ranges $::graphics_bank] {{
    lappend ::graphics_watches [debug set_watchpoint read_mem $range {{$::graphics_guard}} {{{fail} "retired-graphics-read bank=$::graphics_bank address=$::wp_last_address"}}]
   }}
  }}
 }}
}}
'''
            path.write_text(text)
        return original_run(args,*a,**kw)
    subprocess.run=run
    try:result=compact_retired_table_check.check(build,out,mode)
    finally:subprocess.run=original_run
    if not marker.exists():raise ValueError('graphics guard never armed')
    receipt=dict(complete=True,mode=mode,rom_sha256=m['rom']['sha256'],retired_graphics_bytes=m['compact_retired_graphics']['retired_physical_bytes'],
        retired_graphics_cpu_fetch_or_data_reads=0,guard_starts_at_cartridge_entry=True,
        collision_retirement_guard_retained=True,merged_intervals=sum(map(len,merged.values())),producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (out/'retired-graphics-check.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--mode',choices=('ntsc','pal','bear-ntsc','bear-pal','matrix'),required=True)
    a=p.parse_args();check(a.build,a.out,a.mode)
