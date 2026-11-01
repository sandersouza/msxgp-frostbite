"""Compare every actual visible channel and complete CPU/RAM with the original."""
import argparse
from contextlib import contextmanager
import json
from pathlib import Path

from environment import ROOT
import floe_check
from hazard_build import FILES,OUT
from hazard_catalog import EDGE_XS
from hazard_domain import object_modes,shapes
from hazard_observer_check import cases_for,invariant_cases
from hazard_query import RawContacts
from hazard_truth import FULL_BYTES,contacts,full_record
from reference_state import decode_state
from reference_traces import private_output
from stella_floe import control_pairs
from stella_hazard import digest,fixture,observe

HELPERS=tuple(dict.fromkeys((*FILES,'scripts/hazard_check.py','scripts/hazard_native.tcl','scripts/hazard_query.py',
          'scripts/hazard_observer_check.py','scripts/floe_check.py')))


@contextmanager
def target_scope():
    previous=floe_check.FILES
    try:
        floe_check.FILES=FILES
        yield
    finally:floe_check.FILES=previous


def run_target(out,build_dir,records,expected,additional_helpers=(),**options):
    with target_scope():
        return floe_check.run_target(out,build_dir,records,expected,extra_helpers=(*HELPERS,*additional_helpers),
                                     target_script='scripts/hazard_native.tcl',extra_symbols=('native_call',),**options)


def geometry_cases(base,rom):
    domain=shapes(rom);cases=cases_for(base,domain);invariant,_=invariant_cases(base,domain,control_pairs(rom));cases.extend(invariant)
    edge_start=len(cases)
    for px in EDGE_XS:
        for shape,reflection,copies in object_modes(rom):
            i=len(cases)-edge_start;row=i%4;view=i%228
            ram=bytearray(fixture(base,px,32+i%34+(3-row)*26,(px+i%19-9)%160,shape,copies,reflection,bear_x=(i*17)%160))
            for other in range(4):
                if other==row:continue
                ram[0x23+other]=domain[(i+other*7)%len(domain)];ram[0x58+other]=(i+other)%4
                ram[0x54+other]=(i+other*31)%160;ram[0x11+other]=(ram[0x11+other]&127)|(128 if (i+other)&1 else 0)
            ram[0x6E]=view//38;ram[0x6B]=view%38//2;ram[0x6C]=(view%2)*8+(16 if i&1 else 0);ram[0x6F]=i%8
            ram[0x45]=128 if i%5==0 else 0;ram[0x4B]=(0,2,3,4,15,20)[i%6];ram[0x4D]=(255,0,14,15)[i%4]
            ram[0x6D]=(0,7,135,199)[i%4]
            if i%31==0:ram[0x3F]=128
            cases.append(bytes(ram))
    return cases


def geometry(out,build_dir,reader,binary,initial_path,explore=False,inject='none'):
    out=private_output(out);out.mkdir(parents=True,exist_ok=False)
    initial=Path(initial_path).read_bytes();base=decode_state(initial);rom=(ROOT/'references/roms/frostbite.bin').read_bytes()
    if any(digest(initial_path)!=component.plan['initial_sha256'] for component in (reader.edge,reader.ordinary,reader.shore)):
        raise ValueError('geometry must use the audited source preparation capsule')
    helpers={name:digest(ROOT/name) for name in HELPERS};cases=geometry_cases(base['ram'],rom);expected=[];observations=[]
    for offset in range(0,len(cases),1024):
        batch=cases[offset:offset+1024]
        data,receipt=observe(ROOT/'references/roms/frostbite.bin',binary,initial,batch,out/f'original-{offset:05d}')
        for index,ram in enumerate(batch):
            original=full_record(data[index*FULL_BYTES:(index+1)*FULL_BYTES]);actual_contacts=contacts(original,ram)
            if reader.contacts(ram)!=actual_contacts:raise ValueError(f'raw component oracle differs from actual complete original case{offset+index}')
            expected.append(original)
        observations.append({'start':offset,'cases':len(batch),'receipt':receipt})
    records=b''.join(ram+bytes(base['cpu'][key] for key in ('a','x','y','p','sp')) for ram in cases)
    report,_=run_target(out/'native',build_dir,records,expected,explore=explore,inject=inject)
    if any(digest(ROOT/name)!=sha for name,sha in helpers.items()):raise ValueError('hazard boundary producer changed')
    reader.verify_consumed()
    report.update(full_original_phase_cases=len(cases),declared_neutral_hazard_cases=[],actual_literal_views=228,
                  source_observations=observations,scope='Controlled initial RAM; every actual original row/shore sample and complete visible CPU/all128RAM equals the actual standard MSX1 ROM. No neutral collision substitutions. Not natural play, paced or physical acceptance.')
    (out/'geometry.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True);parser.add_argument('--build-dir',type=Path,default=OUT)
    for name in ('floes','edge','ordinary','shore','binary','initial'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--explore',action='store_true');parser.add_argument('--inject',choices=('none','contact','hazard','shore'),default='none');args=parser.parse_args()
    reader=RawContacts(args.floes,args.edge,args.ordinary,args.shore)
    result=geometry(args.out,args.build_dir,reader,args.binary,args.initial,args.explore,args.inject)
    print(json.dumps({'cases':result['cases'],'full_original_phase_cases':result['full_original_phase_cases'],'max_native_cycles':result['max_native_cycles']}))
