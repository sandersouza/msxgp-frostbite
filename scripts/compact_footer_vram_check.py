"""Retain all oracles; verify frozen footer VRAM and forbid post-preload ROM reads."""
import argparse
import json
from pathlib import Path
import subprocess

from build_compact_packet_experiment import digest
import compact_header_ram_check


def audit_snapshots(path,mode,rows,tiles):
    snap=16392;stride=snap if mode=='matrix' else 128+snap*3
    count=0;forbidden={(r['bank'],r['tile']) for r in rows}
    with path.open('rb') as f:
        while raw:=f.read(stride):
            if len(raw)!=stride:raise ValueError('partial footer snapshot record')
            starts=(0,) if mode=='matrix' else (128,128+snap,128+snap*2)
            for start in starts:
                vram=raw[start:start+16384]
                for i,r in enumerate(rows):
                    if vram[r['pattern']:r['pattern']+8]+vram[r['color']:r['color']+8]!=tiles[i*16:i*16+16]:
                        raise ValueError(f'footer storage mutated at snapshot{count} tile{i}')
                for page in (0x1800,0x1C00):
                    for position,identifier in enumerate(vram[page:page+768]):
                        if (position//256,identifier) in forbidden:
                            raise ValueError(f'footer storage referenced by NAME snapshot{count} page{page:x} position{position}')
                count+=1
    if not count:raise ValueError('no footer VRAM snapshots')
    return count


def check(build,out,mode):
    build=build.resolve();out=out.resolve();m=json.loads((build/'build.json').read_bytes());node=m.get('compact_footer_vram',{})
    if node.get('stored_vram_bytes')!=3008:raise ValueError('explicit native footer VRAM allocation required')
    tiles=(build/node['footer_tiles_file']).read_bytes()
    if digest(tiles)!=node['footer_tiles_sha256']:raise ValueError('bound footer tiles changed')
    original_run=subprocess.run;marker=out/'footer-vram-preloaded.txt';source=out/'footer-vram-expected.bin'
    def run(args,*a,**kw):
        if isinstance(args,list) and '-script' in args and 'openmsx' in Path(args[0]).name.lower():
            p=Path(args[args.index('-script')+1]);text=p.read_text();fail='fail_matrix' if 'proc guard_matrix ' in text else 'fail'
            source.write_bytes(tiles)
            table=' '.join(f'{{{r["pattern"]} {r["color"]}}}' for r in node['allocation'])
            text+=f'''
set footer_rom_watch {{}}
set footer_preloads 0
set f [open {{{source}}} rb];set footer_expected [read $f];close $f
debug set_watchpoint write_mem {node['validity_flag']} {{$::wp_last_value==165}} {{
 set i 0
 foreach pair {{{table}}} {{
  lassign $pair pattern color
  set actual "[debug read_block VRAM $pattern 8][debug read_block VRAM $color 8]"
  if {{$actual ne [string range $::footer_expected [expr {{$i*16}}] [expr {{$i*16+15}}]]}} {{{fail} footer-initial-preload}}
  incr i
 }}
 incr ::footer_preloads
 set f [open {{{marker}}} a];puts $f "exact188-tile preload";close $f
}}
debug set_watchpoint write_mem 0x7000 {{}} {{
 if {{$::footer_rom_watch ne {{}}}} {{debug remove_watchpoint $::footer_rom_watch;set ::footer_rom_watch {{}}}}
 if {{$::wp_last_value==13}} {{
  set ::footer_rom_watch [debug set_watchpoint read_mem {{32768 35775}} {{[debug read memory {node['validity_flag']}]==165}} {{{fail} footer-runtime-ROM-read}}]
 }}
}}
'''
            p.write_text(text)
        return original_run(args,*a,**kw)
    subprocess.run=run
    try:compact_header_ram_check.check(build,out,mode)
    finally:subprocess.run=original_run
    if not marker.exists():raise ValueError('exact cold footer preload never observed')
    snapshots=audit_snapshots(out/'captures.bin',mode,node['allocation'],tiles)
    result=dict(complete=True,mode=mode,rom_sha256=m['rom']['sha256'],exact_VDP_preloads=len(marker.read_text().splitlines()),
        footer_bytes=3008,snapshot_count=snapshots,all_sampled_storage_bytes_immutable=True,both_NAME_pages_never_reference_storage=True,
        post_preload_footer_ROM_reads=0,all_inherited_source_picture_owner_IRQ_retirement_gates_retained=True,
        producer_sha256=digest(Path(__file__).read_bytes()),scope='Cold exact upload plus all capture snapshots and ROM-read guards; no physical-hardware or native loader claim.')
    (out/'footer-vram-check.json').write_text(json.dumps(result,indent=2)+'\n');print(result)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--mode',choices=('ntsc','pal','bear-ntsc','bear-pal','matrix'),required=True)
    a=p.parse_args();check(a.build,a.out,a.mode)
