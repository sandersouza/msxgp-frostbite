"""Keep exact legacy geometry as an independent host oracle, never game data."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from build_compact_packet_experiment import digest
from compact_live_probe import CONTROL_SHA
import compact_retired_graphics_check
from environment import ROOT
import presentation_direct_enemy as geometry
from render_build import symbols


def check(build,out,mode):
    build=build.resolve();out=out.resolve();m=json.loads((build/'build.json').read_bytes())
    if m.get('compact_retired_templates',{}).get('validation_geometry_oracle_sha256')!=CONTROL_SHA:raise ValueError('explicit independent geometry oracle required')
    base=ROOT/'outputs/presentation/credit-reference-at/build-final';cm=json.loads((base/'build.json').read_bytes());control=(base/cm['rom']['filename']).read_bytes()
    if digest(control)!=CONTROL_SHA:raise ValueError('immutable geometry control changed')
    s=symbols(build/'presentation.sym');old_geometry=geometry.resident_geometry;old_decorate=geometry.decorate_actor_owners
    expected_geometry=old_geometry(control,symbols(base/'presentation.sym'))
    def resident(*args,**kwargs):return expected_geometry
    def decorate(raw,caches,rom,g):return old_decorate(raw,caches,control,expected_geometry)
    # Existing regular drivers have bound imports; bear driver imports at call
    # time. Replace only these two host-oracle inputs, retaining every audit.
    changed=[]
    for module in tuple(sys.modules.values()):
        if module is None:continue
        for name,old,new in (('resident_geometry',old_geometry,resident),('decorate_actor_owners',old_decorate,decorate)):
            if getattr(module,name,None) is old:changed.append((module,name,old));setattr(module,name,new)
    original_run=subprocess.run
    def run(args,*a,**kw):
        if isinstance(args,list) and '-script' in args and 'openmsx' in Path(args[0]).name.lower():
            p=Path(args[args.index('-script')+1]);text=p.read_text();fail='fail_matrix' if 'proc guard_matrix ' in text else 'fail'
            for n in ('presentation_geometry_lookup','p_template_pattern','p_template_load'):
                text+=f'\ndebug set_bp {s[n]} {{}} {{{fail} retired-generic-entry-{n}}}\n'
            p.write_text(text)
        return original_run(args,*a,**kw)
    subprocess.run=run
    try:compact_retired_graphics_check.check(build,out,mode)
    finally:
        subprocess.run=original_run
        for module,name,old in changed:setattr(module,name,old)
    result=dict(complete=True,mode=mode,rom_sha256=m['rom']['sha256'],geometry_oracle_sha256=CONTROL_SHA,
        generic_entries=0,physical_retirement_guard_retained=True,source_pixels_owners_and_clock_oracles_retained=True,
        producer_sha256=digest(Path(__file__).read_bytes()))
    (out/'retired-template-check.json').write_text(json.dumps(result,indent=2)+'\n');print(result)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--mode',choices=('ntsc','pal','bear-ntsc','bear-pal','matrix'),required=True)
    a=p.parse_args();check(a.build,a.out,a.mode)
