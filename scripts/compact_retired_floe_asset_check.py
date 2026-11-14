"""Independent original raw-floe namespace after removing target-only copies."""
import argparse
import json
from pathlib import Path
import sys

from build_compact_packet_experiment import digest
from compact_live_probe import CONTROL_SHA
import compact_retired_template_check
from environment import ROOT
import presentation_constructors


def check(build,out,mode):
    build=build.resolve();out=out.resolve();m=json.loads((build/'build.json').read_bytes());node=m.get('compact_retired_floe_assets',{})
    if node.get('validation_raw_floe_oracle_sha256')!=CONTROL_SHA:raise ValueError('explicit original floe oracle required')
    base=ROOT/'outputs/presentation/credit-reference-at/build-final';cm=json.loads((base/'build.json').read_bytes());control=(base/cm['rom']['filename']).read_bytes()
    if digest(control)!=CONTROL_SHA:raise ValueError('immutable floe control changed')
    packed=cm['template_assets'];section=packed['sections']['floe_patterns'];data=b''.join(control[b*16384:(b+1)*16384] for b in packed['physical_banks'])
    raw=data[section['offset']:section['offset']+section['size']]
    if digest(raw)!=node['original_floe_patterns_sha256'] or len(raw)!=packed['floe_patterns']*8:raise ValueError('original raw-ID namespace changed')
    floes=[raw[i:i+8] for i in range(0,len(raw),8)];old=presentation_constructors.construct
    def construct(*args,**kwargs):
        if 'floe_patterns' in kwargs:kwargs['floe_patterns']=floes
        return old(*args,**kwargs)
    changed=[]
    for module in tuple(sys.modules.values()):
        if module is not None and getattr(module,'construct',None) is old:changed.append(module);module.construct=construct
    try:compact_retired_template_check.check(build,out,mode)
    finally:
        for module in changed:module.construct=old
    result=dict(complete=True,mode=mode,rom_sha256=m['rom']['sha256'],raw_floe_oracle_sha256=CONTROL_SHA,
        original_floe_patterns_sha256=digest(raw),logical_raw_id_domain=packed['floe_patterns'],
        all_physical_retirement_and_source_pixel_owner_clock_guards_retained=True,producer_sha256=digest(Path(__file__).read_bytes()))
    (out/'retired-floe-assets-check.json').write_text(json.dumps(result,indent=2)+'\n');print(result)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--mode',choices=('ntsc','pal','bear-ntsc','bear-pal','matrix'),required=True)
    a=p.parse_args();check(a.build,a.out,a.mode)
