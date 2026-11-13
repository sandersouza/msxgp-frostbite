"""Original F route with prepared-role audits and direct-CGT IO counters."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys

from environment import ROOT
from presentation_fixed_ownership import audit_active,audit_row
from presentation_prepared_ownership import decorate_owners
from presentation_shared_ownership import constructor
from render_build import symbols
from presentation_experiment_evidence import owner_binding,validate_probe


def check(build,out,family,*,audit_only=False):
    meta=json.loads((build/'build.json').read_text());rom=(build/meta['rom']['filename']).read_bytes()
    if 'fixed_clock' in meta:
        raise ValueError('fixed-clock ROM requires an interrupt-driven route, not render-driven F timing')
    if hashlib.sha256(rom).hexdigest()!=meta['rom']['sha256']:raise ValueError('ROM identity mismatch')
    s=symbols(build/'presentation.sym')
    lazy=meta.get('direct_enemy',{}).get('lazy_keys',False)
    width=4214 if lazy else 4182
    from presentation_direct_enemy import resident_geometry
    geometry=resident_geometry(rom,s) if lazy else None
    deltas=list(rom[s['p_template_deltas']-16384:s['p_template_deltas']-16384+10])
    adapter=ROOT/'outputs/presentation/architecture-review-f/route_probe.py'
    if hashlib.sha256(adapter.read_bytes()).hexdigest()!='db9229dc9464646569386f18d88cf493d5b3eb2401a9829030d084da87e0958f':
        raise ValueError('original F input adapter changed')
    original_run=subprocess.run
    def intercepted(args,*a,**kw):
        if isinstance(args,list) and '-script' in args and 'openmsx' in Path(args[0]).name.lower():
            script=Path(args[args.index('-script')+1]);text=script.read_text()
            if 'direct_enemy' in meta:
                from presentation_direct_enemy import declare_ram
                text=declare_ram(text)
                text+=f'''\ndebug set_bp {s['qe_entry']} {{}} {{
 if {{$::tracking}} {{incr ::calls(primitive)}}
 begin_probe_cost primitive
}}\n'''
            if 'region_pipeline' in meta:
                from presentation_region_pipeline import declare_ram,ram_code
                text=declare_ram(text,ram_code(meta,rom),'fail_probe')
            text+=f'''
set pkbands [open {{{out/'band-records.bin'}}} wb]
set pkfills [open {{{out/'fill-events.tsv'}}} w]
debug set_bp {s['paced_wait']} {{}} {{
 puts -nonewline $::pkbands "[debug read_block memory 0xC1D1 32][debug read_block memory 0xE5C0 32][debug read_block memory 0xC1F1 8][debug read_block memory 0xC800 768][debug read_block memory 0xCD00 768][debug read_block memory 0xD000 2304][debug read_block memory 0xD900 264][debug read_block memory 0xCCA0 6]"
}}
debug set_bp {s['pk_fill.byte']} {{}} {{if {{$::tracking}} {{incr ::transfer_bytes}}}}
debug set_bp {s['pk_fill']} {{}} {{
 if {{$::tracking}} {{incr ::transfer_calls;incr ::calls(vdp-write);puts $::pkfills "$::index [expr {{[reg BC]>>8}}] [reg DE]"}}
 begin_probe_cost vdp-write
}}
debug set_bp {s['pk_load_entry']} {{}} {{
 if {{$::tracking}} {{incr ::calls(template-load)}}
 begin_probe_cost template-load
}}
'''
            if lazy:text=text.replace('[debug read_block memory 0xCCA0 6]','[debug read_block memory 0xCCA0 6][debug read_block memory 0xE800 32]')
            script.write_text(text)
        return original_run(args,*a,**kw)
    if not audit_only:
        argv=sys.argv;sys.argv=[str(adapter),str(build),str(out),family]
        subprocess.run=intercepted
        try:runpy.run_path(str(adapter),run_name='__main__')
        finally:subprocess.run=original_run;sys.argv=argv
    frames=2253 if family=='ntsc' else 1886
    validate_probe(out,meta['rom']['sha256'],frames)
    captures=(out/'captures.bin').read_bytes();bands=(out/'band-records.bin').read_bytes()
    if len(captures)!=frames*49304 or len(bands)!=frames*width:raise ValueError('incomplete prepared role captures')
    tile=constructor(build)
    for index in range(frames):
        row=captures[index*49304:(index+1)*49304]
        audit_active(row[128:16512],row[16520:32904],row[16512:16520])
        band=bands[index*width:(index+1)*width]
        decorated=decorate_owners(band[72:4182],band[:32],band[32:64],band[64:72],rom,deltas)
        if lazy:
            from presentation_direct_enemy import decorate_actor_owners
            decorated=decorate_actor_owners(decorated,band[4182:],rom,geometry)
        audit_row(decorated,row[32912:49296],tile,templates=True)
    result=dict(complete=True,frames=frames,rom_sha256=meta['rom']['sha256'],
        wrapper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        physical_owner_audits=True,active_full_page_protection=True,direct_fill_io_instrumented=True,
        scope='Original F native input/timing/pixel oracle plus prepared-role audits; all added contact decoding and direct-CGT IO count in whole frame. No original-time/manual/physical acceptance.')
    result.update(owner_binding(out,meta['rom']['sha256'],frames,'prepared'))
    target=out/'prepared-check-v2.json'
    if target.exists():raise ValueError('immutable physical audit receipt already exists')
    target.write_text(json.dumps(result,indent=2)+'\n');print(result)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--family',choices=('ntsc','pal'),required=True)
    parser.add_argument('--audit-only',action='store_true')
    args=parser.parse_args();check(args.build.resolve(),args.out.resolve(),args.family,audit_only=args.audit_only)
