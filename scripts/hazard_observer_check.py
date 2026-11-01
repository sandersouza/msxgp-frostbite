"""Compare nine-window sidecars with real latches and unchanged original CPU.

This controlled source check is not a natural route, MSX acceptance or a
complete geometry catalog. Raw original bytes remain in the ignored output.
"""
import argparse
import json
from pathlib import Path
import random
import subprocess

from environment import ROOT
from floe_model import visible_state
from hazard_truth import FULL_BYTES,contacts,full_record
from native_contract import compare
from reference_inventory import verified_input
from reference_state import decode_state
from reference_traces import private_output,run_debugger
from stella_floe import observe as observe_floes
from stella_hazard import HELPERS,digest,fixture,helper_identity,observe

CHECK_HELPERS=(*HELPERS,'scripts/hazard_observer_check.py','scripts/floe_model.py','scripts/native_contract.py')


def shapes(rom):
    result=set()
    for kind in range(4):
        for frame in range(256):
            index=kind*2
            if not frame&(16 if index==6 else 8):index+=1
            low=rom[0xD0A+index]
            if index>=2:
                phase=(frame>>3)&31
                if phase>=16:phase^=31
                low=(low+rom[0xDC2+phase])&255
            if low>248:raise ValueError('legal object graphic crosses an unmodeled page')
            result.add(low)
    return sorted(result)


def cases_for(base,domain):
    rng=random.Random(1201);cases=[]
    positions=(0,1,7,8,64,151,158,159)
    def add(px,y,ox,shape,copies,reflection,view):
        ram=bytearray(fixture(base,px,y,ox,shape,copies,reflection,bear_x=rng.choice((0,15,16,64,151,159))))
        ram[0x6E]=view//38;ram[0x6B]=view%38//2;ram[0x6C]=(view%2)*8+(16 if len(cases)&1 else 0)
        ram[0x6F]=len(cases)%8;ram[0x70]=len(cases)%4
        ram[0x6D]=135 if len(cases)%7==0 else 0
        if len(cases)%31==0:ram[0x3F]=128
        cases.append(bytes(ram))
    for view in range(228):
        add(positions[view%8],rng.randrange(256),rng.randrange(160),domain[view%len(domain)],view%4,bool(view&1),view)
    for y in range(256):
        for px in positions:
            for copies in range(4):
                index=len(cases)
                add(px,y,rng.randrange(160),domain[index%len(domain)],copies,bool(index&1),index%228)
    for shape in domain:
        for copies in range(4):
            for reflection in (False,True):
                for ox in (0,8,64,159):
                    index=len(cases)
                    add(positions[index%8],34+index%46,ox,shape,copies,reflection,index%228)
    return cases


def check(out,binary,initial_path,original_binary='stella',old_binary=None):
    out=private_output(out);out.mkdir(parents=True,exist_ok=False)
    source=verified_input(ROOT/'references/roms/frostbite.bin');rom=(ROOT/'references/roms/frostbite.bin').read_bytes()
    initial=Path(initial_path).read_bytes();base=decode_state(initial)
    helpers={name:digest(ROOT/name) for name in CHECK_HELPERS}
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    domain=shapes(rom);cases=cases_for(base['ram'],domain)
    chunks=[];observations=[]
    for offset in range(0,len(cases),1024):
        data,receipt=observe(ROOT/'references/roms/frostbite.bin',binary,initial,cases[offset:offset+1024],out/f'full-{offset:05d}')
        chunks.append(data);observations.append({'start':offset,'stop':min(offset+1024,len(cases)),'receipt':receipt})
    data=b''.join(chunks)
    records=[full_record(data[i*FULL_BYTES:(i+1)*FULL_BYTES]) for i in range(len(cases))]
    for index,(ram,record) in enumerate(zip(cases,records)):
        acquired=contacts(record,ram)
        if acquired['rows']!=record['ram'][0x30:0x38]:raise ValueError(f'actual row latch differs at case{index}')
        compare(visible_state(rom,ram,base['cpu'],acquired),record)
        if ram[0x3F]&128 and (any(row!=7 for row in acquired['rows']) or acquired['shore']!=7):
            raise ValueError('blanked source acquired new collisions')
    unmodified=[]
    for index in range(0,224,7):
        ram=cases[index];capsule=bytearray(initial);offset=base['_offsets']['ram'];capsule[offset:offset+128]=ram
        states,backend=run_debugger(ROOT/'references/roms/frostbite.bin',
            'loadState 0\nsaveState 1\nrunToPc $f476\nsaveState 2\nexitRom\n',out/f'original-{index:04d}',bytes(capsule),stella=original_binary)
        before=decode_state(states[1]);after=decode_state(states[2])
        if bytes(before['ram'])!=ram:raise ValueError('independent original before-RAM mismatch')
        compare(records[index],{'ram':after['ram'],'registers':{key:after['cpu'][key] for key in ('a','x','y','p','sp')}})
        unmodified.append({'case':index,'backend':backend,'before_sha256':digest(out/f'original-{index:04d}'/'settings/state/Frostbite (1983) (Activision).st1'),
                           'after_sha256':digest(out/f'original-{index:04d}'/'settings/state/Frostbite (1983) (Activision).st2')})
    old_count=0
    if old_binary is not None:
        old,old_receipt=observe_floes(ROOT/'references/roms/frostbite.bin',old_binary,initial,cases[:64],out/'old-floe')
        for index,record in enumerate(records[:64]):
            reduced=b''.join(record['truth'][row] for row in (0,2,4,6))+record['ram']+bytes(record['registers'].values())+record['glyph']
            if reduced!=old[index*384:(index+1)*384]:raise ValueError('old floe observation protocol changed')
        old_count=64
    if helpers!={name:digest(ROOT/name) for name in CHECK_HELPERS}:raise ValueError('hazard checker helpers changed')
    result={'schema_version':1,'complete':True,'source':source,'producer_commit':commit,'producer_dirty':dirty,
            'helpers':helpers,'binary_sha256':digest(binary),'initial_sha256':digest(initial_path),
            'cases':len(cases),'actual_views':228,'object_shapes':len(domain),'nusiz_values':[0,1,2,3],
            'independent_unmodified_phases':unmodified,'old_floe_compatibility_cases':old_count,'observations':observations,
            'scope':'Controlled all-window source verification only; complete catalog/natural routes/native target/hardware remain pending'}
    (out/'check.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--binary',type=Path,default=ROOT/'outputs/hazards/observer-source/stella')
    parser.add_argument('--initial',type=Path,default=ROOT/'outputs/floes/catalog-issue11-b/initial.state')
    parser.add_argument('--old-binary',type=Path,default=ROOT/'outputs/floes/catalog-issue11-b/stella')
    args=parser.parse_args();result=check(args.out,args.binary,args.initial,old_binary=args.old_binary)
    print(json.dumps({key:result[key] for key in ('complete','cases','actual_views','object_shapes','old_floe_compatibility_cases')}))
