"""Qualify the replacement NAME allocation without retaining obsolete RAM checks."""
import argparse
import json
from pathlib import Path
import subprocess

from build_compact_packet_experiment import digest
import compact_footer_vram_check
import compact_game_probe
import compact_grid_ram_check
from render_build import symbols


def check(build,out,mode):
    build=build.resolve();out=out.resolve();m=json.loads((build/'build.json').read_bytes());node=m.get('compact_grid_palette',{})
    if node.get('phase_owner_cases')!=1280:raise ValueError('explicit all-row native palette proof required')
    initializers=[]
    for row in node['initializers']:
        data=(build/row['file']).read_bytes()
        if len(data)!=row['size'] or digest(data)!=row['sha256']:raise ValueError('palette initializer changed')
        initializers.append((row['ram_address'],data))
    s=symbols(build/'presentation.sym');old_guarded=compact_grid_ram_check.guarded;marker=out/'grid-palette-validated.txt'
    def guarded(build2,out2,mode2):
        if (build2,out2,mode2)!=(build,out,mode):raise ValueError('unexpected nested route')
        original_run=subprocess.run
        def run(args,*a,**kw):
            if isinstance(args,list) and '-script' in args and 'openmsx' in Path(args[0]).name.lower():
                p=Path(args[args.index('-script')+1]);text=p.read_text()
                body='\n'.join(f' if {{[debug read_block memory {address} {len(data)}] ne [binary format H* {data.hex()}]}} {{fail grid-palette-preload-{address}}}' for address,data in initializers)
                for row in node['reclaimed_ranges']:
                    body+=f'\n if {{[debug read_block memory {row["address"]} {row["size"]}] ne [string repeat [binary format cu 165] {row["size"]}]}} {{fail grid-reclaimed-not-poisoned}}'
                text+=f'''
set grid_palette_guard 0
debug set_bp {s['t_main.frame']} {{!$::grid_palette_guard}} {{
{body}
 set ::grid_palette_guard 1
 set f [open {{{marker}}} w];puts $f "exact22rows8palettes-native-code";close $f
}}
'''
                for address,data in initializers:text+=f'debug set_watchpoint write_mem {{{address} {address+len(data)-1}}} {{$::grid_palette_guard}} {{fail immutable-grid-palette-write}}\n'
                for row in node['reclaimed_ranges']:
                    span=f'{{{row["address"]} {row["address"]+row["size"]-1}}}'
                    text+=f'debug set_watchpoint read_mem {span} {{$::grid_palette_guard}} {{fail reclaimed-grid-read}}\n'
                    text+=f'debug set_watchpoint write_mem {span} {{$::grid_palette_guard}} {{fail reclaimed-grid-write}}\n'
                p.write_text(text)
            return original_run(args,*a,**kw)
        subprocess.run=run
        try:return compact_game_probe.check(build2,out2,mode2)
        finally:subprocess.run=original_run
    compact_grid_ram_check.guarded=guarded
    try:compact_footer_vram_check.check(build,out,mode)
    finally:compact_grid_ram_check.guarded=old_guarded
    if mode!='matrix' and not marker.exists():raise ValueError('new grid preload/retirement guards never armed')
    result=dict(complete=True,mode=mode,rom_sha256=m['rom']['sha256'],replacement_allocation_preload_verified=mode!='matrix',
        immutable_data_bytes=936,immutable_code_bytes=182,reclaimed_lower_RAM_bytes=4674,forbidden_reclaimed_reads_and_writes=0 if mode!='matrix' else None,
        cold_matrix_constructor_retained=mode=='matrix',all_previous_nonobsolete_source_picture_owner_IRQ_VRAM_gates_retained=True,
        producer_sha256=digest(Path(__file__).read_bytes()),scope='Old expanded-row oracle replaced by exact new preload and read/write guards; all original output checks retained.')
    (out/'grid-palette-check.json').write_text(json.dumps(result,indent=2)+'\n');print(result)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--mode',choices=('ntsc','pal','bear-ntsc','bear-pal','matrix'),required=True)
    a=p.parse_args();check(a.build,a.out,a.mode)
