"""All-channel native work with a declared crowded state and dense visual stress.

Canonical state is seeded once; every following phase must follow its own last
complete CPU/RAM state. Dense scene overlays separately stress the renderer.
"""
import argparse
from contextlib import contextmanager
import copy
import json
from pathlib import Path

from environment import ROOT
import floe_bench as bench
import hazard_build as build
from hazard_check import HELPERS
from hazard_query import RawContacts
from stella_hazard import digest


def dense_initial(initial):
    result=copy.deepcopy(initial);r=result['ram']
    for address,value in {0xCB:4,0xCD:8,0xE4:53,0xE6:64,0xEA:0,0xE7:0,0xED:0,0xF1:0,0xF2:255,
                          0xEE:0,0xEB:0,0xEC:0,0xBF:0}.items():r[address-128]=value
    r[0x58:0x5C]=[3]*4;r[0x5C:0x60]=[7]*4;r[0x11:0x15]=[0,65,2,67]
    r[0x60:0x64]=[16,48,80,112];r[0x54:0x58]=list(r[0x60:0x64]);r[0x23:0x27]=[0]*4
    return result


def mixed_initial(initial):
    result=dense_initial(initial);r=result['ram']
    r[0x58:0x5C]=[0,1,2,3];r[0x5C:0x60]=[1,3,5,7]
    r[0x54:0x58]=[48,64,80,112]
    return result


def source_identity(reader,metadata):
    tables=metadata['tables']
    if digest(reader.floes.directory/'catalog.json')!=tables['floe_catalog_sha256']:raise ValueError('benchmark floe source differs from build')
    for name in ('edge','ordinary','shore'):
        if digest(getattr(reader,name).root/'catalog.json')!=tables['components'][name]['manifest_sha256']:
            raise ValueError('benchmark hazard source differs from build')
    if tables['aliases'].get('complete_geometry') is not True:raise ValueError('complete actual-copy alias proof required')


@contextmanager
def scope(build_dir):
    names=('OUT','ROM','VERSION','FILES','expected_pixels','presentation');previous={n:getattr(bench,n) for n in names}
    try:
        bench.OUT=Path(build_dir).resolve();bench.ROM=bench.OUT/f'frostbite-{build.VERSION}.rom'
        for n in names[2:]:setattr(bench,n,getattr(build,n))
        bench.expected_image.cache_clear()
        yield
    finally:
        for n,v in previous.items():setattr(bench,n,v)
        bench.expected_image.cache_clear()


def capture(build_dir,reader,mixed=False,**options):
    with scope(build_dir):
        r=bench.capture(**options,source_reader=reader,source_identity=source_identity,initial_override=mixed_initial if mixed else dense_initial,
                        additional_helpers=(*HELPERS,'scripts/hazard_bench.py'))
    records=(ROOT/r['directory']/'states.bin').read_bytes();codes=set()
    for index in range(r['source_steps']):
        for offset in (0,133,266):codes.update(records[index*404+offset+5+0x58:index*404+offset+5+0x5C])
    if mixed and codes!={0,1,2,3}:raise ValueError('all four real original NUSIZ codes must be observed')
    r.update(canonical_seed='mixed-counts' if mixed else 'three-copies',canonical_nusiz_codes=sorted(codes))
    r['scope']='Seeded standard MSX1 continuous native all-channel acquisition/core/input state, initially three real copies per row; synthetic dense visual overlays independently stress every completed frame, cache, VRAM spacing, VBlank and four sprite slots. No per-step canonical/contact writes; input-only named routes and manual/physical acceptance are separate.'
    (ROOT/r['directory']/'verified.json').write_text(json.dumps(r,indent=2)+'\n');return r


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build-dir',type=Path,default=build.OUT)
    for n in ('floes','edge','ordinary','shore'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--family',choices=('ntsc','pal'),default='ntsc');p.add_argument('--layout',type=int,choices=(0,1),default=0)
    p.add_argument('--width',type=int,choices=(0,1),default=0);p.add_argument('--transitions',action='store_true');p.add_argument('--explore',action='store_true');p.add_argument('--mixed',action='store_true')
    p.add_argument('--catalog',choices=('dense','counts'),default='dense');p.add_argument('--inject',choices=('none','state','pixel','spacing','guard','sprite','contact','cache'),default='none');args=p.parse_args()
    reader=RawContacts(args.floes,args.edge,args.ordinary,args.shore)
    r=capture(args.build_dir,reader,family=args.family,layout=args.layout,width=args.width,transitions=args.transitions,
              explore=args.explore,catalog=args.catalog,inject=args.inject,mixed=args.mixed)
    print(json.dumps({n:r[n] for n in ('directory','source_steps','max_busy_cycles','frame_budget')}))
