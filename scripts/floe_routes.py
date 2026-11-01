"""Continuous original build/entry/next-level route using only real input pins."""
import argparse
import hashlib
import json
from pathlib import Path

from environment import ROOT
from reference_provenance import COMMON,snapshot_paths,audit_manifest
from reference_state import decode_state
from reference_traces import NEUTRAL,capture_steps,poweron_capsule,private_output
from stella_floe import digest
from trace_compare import validate_trace,compare_traces

CONFIG=ROOT/'references/floe-routes.json'
HELPERS=(*COMMON,'scripts/floe_routes.py','scripts/stella_floe.py','scripts/floe_truth.py',
         'scripts/environment.py','references/tools-lock.json','tools/stella-floe.patch','references/floe-routes.json')


def assess(points,active_start=0):
    construction=entry=next_level=None
    if not points or any(len(point['ram'])!=128 for point in points):raise ValueError('complete continuous natural RAM route required')
    if not 0<=active_start<len(points) or points[active_start]['ram'][0x4B]!=0:raise ValueError('natural route must start at first level')
    for index,point in enumerate(points[active_start:],active_start):
        r=point['ram']
        if construction is None and r[0x4B]==0 and r[0x4D]==15:construction=index
        if construction is not None and entry is None and r[0x4B]==0 and r[0x71]&64 and r[0x64]==0 and r[0x69]==0:entry=index
        if entry is not None and r[0x4B]==1 and r[0x4D]==255 and r[0x64]==27 and r[0x65]==69 and r[0x6A]==0 and r[0x71]==0:
            next_level=index;break
    if construction is None or entry is None or next_level is None or not construction<entry<next_level:
        raise ValueError('construction, actual entry and initialized next-level transition all required')
    if any(point['ram'][0x45]&128 for point in points[active_start:next_level+1]):raise ValueError('route entered terminal/attract state before next level')
    reserve=points[active_start]['ram'][0x4C]
    return {'construction_step':construction,'entry_step':entry,'next_level_step':next_level,
            'initial_reserve':reserve,'final_reserve':points[next_level]['ram'][0x4C],
            'reserve_decrements':sum(b['ram'][0x4C]<a['ram'][0x4C] for a,b in zip(points[active_start:next_level],points[active_start+1:next_level+1])),
            'source_hazards_disabled':False,'ram_or_contact_injections':False}


def route_policy(ram,stage,elapsed):
    x,y=ram[0x66],ram[0x64]
    if stage=='build' and ram[0x4D]==15:stage='shore'
    if stage=='shore' and y==27 and ram[0x6A]==0:stage='door'
    if stage=='door' and 120<=x<=127:stage='enter'
    if stage=='enter' and ram[0x71]&64:stage='bonus'
    if stage=='build':direction=0xDF if (elapsed//120)%2==0 else 0xEF
    elif stage in ('shore','enter'):direction=0xEF
    elif stage=='door':direction=0x7F if x<123 else 0xBF
    else:direction=255
    count=1 if stage=='door' and abs(x-123)<8 else 10
    return stage,[{**NEUTRAL,'swcha':direction} for _ in range(count)]


def capture(out,stella='stella'):
    producer=snapshot_paths(HELPERS);config=json.loads(CONFIG.read_text());out=private_output(out);out.mkdir(parents=True,exist_ok=False)
    rom=ROOT/'references/roms/frostbite.bin';initial,backend=poweron_capsule(rom,out/'poweron',config['seed'],config['riot_timer_preset'],stella)
    preparation=[NEUTRAL]*config['warmup']+[{**NEUTRAL,'swchb':62}]+[NEUTRAL]*config['reset_release']
    trace,current=capture_steps(rom,initial,preparation,out/'prepare',stella)
    points=trace['steps'];inputs=list(preparation);stage='build';elapsed=0
    for batch in range(config['maximum_batches']):
        ram=decode_state(current)['ram']
        if ram[0x4B]==1:break
        if ram[0x45]&128:raise ValueError('natural route reached terminal state')
        stage,steps=route_policy(ram,stage,elapsed)
        segment,current=capture_steps(rom,current,steps,out/f'batch-{batch:03d}',stella)
        for point in segment['steps']:point['index']=len(points);points.append(point)
        inputs.extend(steps);elapsed+=len(steps)
        if batch%12==0:print(f'FLOE_ROUTE_PROGRESS {elapsed} {stage} {ram[0x4D]} {ram[0x4C]}',flush=True)
    result=assess(points,len(preparation)-1)
    combined={**trace,'policy':{'boundary':'PCF019 every original interval from controlled power-on and real Reset',
              'route':'first-level build, actual entry, initialized next level','preparation_intervals':len(preparation),
              'ram_injections':{},'source_hazards_disabled':False},'steps':points}
    validate_trace(combined)
    if snapshot_paths(HELPERS)!=producer:raise ValueError('original route producer changed during execution')
    (out/'trace.json').write_text(json.dumps(combined,indent=2)+'\n');(out/'inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
    (out/'final.state').write_bytes(current);(out/'initial.state').write_bytes(initial)
    report={'schema_version':1,**producer,'backend':backend,'steps':len(points),'assessment':result,
            'files':{name:digest(out/name) for name in ('trace.json','inputs.json','initial.state','final.state')},
            'scope':'Unmodified original Stella only; native MSX replay and manual/physical acceptance are separate'}
    (out/'route.json').write_text(json.dumps(report,indent=2)+'\n');return report


def replay(original,out,stella='stella'):
    producer=snapshot_paths(HELPERS)
    original=Path(original);out=private_output(out);out.mkdir(parents=True,exist_ok=False)
    receipt=json.loads((original/'route.json').read_text());audit_manifest(receipt,HELPERS)
    if any(digest(original/name)!=sha for name,sha in receipt['files'].items()):raise ValueError('original route evidence changed')
    initial=(original/'initial.state').read_bytes();inputs=json.loads((original/'inputs.json').read_text())
    expected=json.loads((original/'trace.json').read_text());trace,final=capture_steps(ROOT/'references/roms/frostbite.bin',initial,inputs,out/'raw',stella,expected['policy'])
    differences=compare_traces(expected,trace)
    if differences or final!=(original/'final.state').read_bytes():raise ValueError(f'natural original replay differs: {differences[:3]}')
    if snapshot_paths(HELPERS)!=producer:raise ValueError('original replay producer changed')
    if any(digest(original/name)!=sha for name,sha in receipt['files'].items()):raise ValueError('original evidence changed during replay')
    report={**producer,'steps':len(inputs),'assessment':assess(trace['steps'],expected['policy']['preparation_intervals']-1),'identical_full_cpu_ram_tia_riot_inputs':True,
            'original_route_sha256':digest(original/'route.json'),'replay_trace_sha256':digest(out/'raw/trace.json')}
    (out/'replay.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--replay',type=Path);args=parser.parse_args()
    print(json.dumps(replay(args.replay,args.out) if args.replay else capture(args.out),indent=2))
