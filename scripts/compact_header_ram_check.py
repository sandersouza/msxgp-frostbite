"""Verify the cold preload and forbid runtime writes to resident HUD bytes."""
import argparse
import json
from pathlib import Path
import subprocess

from build_compact_packet_experiment import digest
import compact_resident_retirement_check


def check(build,out,mode):
    build=build.resolve();out=out.resolve();m=json.loads((build/'build.json').read_bytes());node=m.get('compact_header_ram',{})
    if not node.get('initializers'):raise ValueError('explicit header preload required')
    rows=[]
    for r in node['initializers']:
        data=(build/r['file']).read_bytes()
        if digest(data)!=r['sha256'] or len(data)!=r['size']:raise ValueError('bound header initializer changed')
        rows.append((r['ram_address'],data))
    original_run=subprocess.run;marker=out/'header-ram-validated.txt';counts=out/'header-hot-calls.txt'
    def run(args,*a,**kw):
        if mode!='matrix' and isinstance(args,list) and '-script' in args and 'openmsx' in Path(args[0]).name.lower():
            p=Path(args[args.index('-script')+1]);text=p.read_text();finish='\n  exit;return'
            if text.count(finish)!=1:raise ValueError('unique natural route completion required')
            text=text.replace(finish,f'\n  set f [open {{{counts}}} w];puts $f $::header_hot_calls;close $f'+finish,1)
            body='\n'.join(f' if {{[debug read_block memory {address} {len(data)}] ne [binary format H* {data.hex()}]}} {{fail header-preload-{address}}}' for address,data in rows)
            text+=f'''
set header_ram_guard 0
set header_hot_calls 0
debug set_bp {node['bootstrap_final_ret']} {{!$::header_ram_guard}} {{
{body}
 set ::header_ram_guard 1
 set f [open {{{marker}}} w];puts $f "exact boot preload";close $f
}}
debug set_watchpoint read_mem {node['hot_entry']} {{$::header_ram_guard}} {{incr ::header_hot_calls}}
'''
            for address,data in rows:text+=f'debug set_watchpoint write_mem {{{address} {address+len(data)-1}}} {{$::header_ram_guard}} {{fail immutable-header-write}}\n'
            p.write_text(text)
        return original_run(args,*a,**kw)
    subprocess.run=run
    try:compact_resident_retirement_check.check(build,out,mode)
    finally:subprocess.run=original_run
    calls=int(counts.read_text()) if mode!='matrix' and counts.exists() else 0
    if mode!='matrix' and (not marker.exists() or calls<=0):raise ValueError('natural route did not exercise validated resident header')
    result=dict(complete=True,mode=mode,rom_sha256=m['rom']['sha256'],boot_RAM_preload_verified=mode!='matrix',
        immutable_runtime_writes=0 if mode!='matrix' else None,hot_constructor_calls=calls,
        cold_matrix_path_retained=mode=='matrix',all_original_and_retirement_oracles_retained=True,producer_sha256=digest(Path(__file__).read_bytes()))
    (out/'header-ram-check.json').write_text(json.dumps(result,indent=2)+'\n');print(result)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--mode',choices=('ntsc','pal','bear-ntsc','bear-pal','matrix'),required=True)
    a=p.parse_args();check(a.build,a.out,a.mode)
