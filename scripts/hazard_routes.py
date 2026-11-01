"""Explicit source interaction predicates and input-only route acquisition.

Predicates certify their named event sequence; complete source continuity and
native equality have separate mandatory gates. Original states remain private.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from environment import ROOT
from reference_inventory import verified_input
from reference_provenance import COMMON,audit_manifest,snapshot_paths
from reference_routes import assess_refuge,refuge_approach
from reference_state import decode_state
from reference_traces import NEUTRAL,capture_steps,poweron_capsule,private_output
from trace_compare import compare_traces,validate_trace

CONFIG=ROOT/'references/hazard-routes.json'
HELPERS=tuple(dict.fromkeys((*COMMON,'scripts/hazard_routes.py','scripts/reference_routes.py','scripts/environment.py',
                           'references/hazard-routes.json','references/tools-lock.json')))


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_policy(policy):
    if (policy.get('ram_injections')!={} or policy.get('source_hazards_disabled') is not False
            or policy.get('instruction_skipping') is not False or policy.get('raw_input_every_interval') is not True):
        raise ValueError('continuous input-only source policy with enabled hazards required')


def score(ram):
    result=0
    for value in ram[0x48:0x4B]:
        high,low=divmod(value,16)
        if high>9 or low>9:raise ValueError('complete valid source BCD score required')
        result=result*100+high*10+low
    return result


def reserves(ram):return ram[0x4C]+ram[0x52]


def recovery(rows,death,initial):
    for i in range(death+1,len(rows)):
        r=rows[i]
        if (reserves(r)==reserves(initial)-1 and r[0x64]==27 and r[0x65]==69 and r[0x66]==64
                and r[0x6A]==0 and r[0x71]==0 and r[0x67]==0 and r[0x46]==0):return i
    raise ValueError('observed loss and initialized active recovery required')


def assess(points,route_kind,active_start=0,approach_end=None):
    if (len(points)<2 or not 0<=active_start<len(points) or any(len(p.get('ram',[]))!=128 for p in points)
            or [p.get('index') for p in points]!=list(range(len(points)))):
        raise ValueError('complete continuous indexed source RAM checkpoints required')
    rows=[p['ram'] for p in points]
    if any(r[0x45]&128 or r[0x46]&128 for r in rows[active_start:]):raise ValueError('route entered terminal/attract before acceptance')
    initial=rows[active_start]
    if route_kind=='bear-refuge':
        end=approach_end if approach_end is not None else active_start+288
        result=assess_refuge(points[active_start:end],points[end:])
        return {'kind':route_kind,**result,'approach_end':end,'observed_steps':len(points)-active_start}
    if route_kind=='bear-chase':
        contact=next((i for i in range(active_start,len(rows)) if rows[i][0x6D]&128 and rows[i][0x4B]>=3
                      and rows[i][0x64]==27 and rows[i][0x6A]==0 and rows[i][0x71]==0),None)
        if contact is None:raise ValueError('actual grounded shore contact required')
        push=next((i for i in range(contact+1,len(rows)) if rows[i][0x6D]&128 and rows[i][0x71]==0
                   and rows[i][0x66]<rows[i-1][0x66]),None)
        if push is None:raise ValueError('effective bear chase movement required')
        death=next((i for i in range(push+1,len(rows)) if rows[i][0x71]&128),None)
        if death is None:raise ValueError('bear chase death transition required')
        end=recovery(rows,death,initial)
        return {'kind':route_kind,'contact_step':contact,'push_step':push,'death_step':death,'recovery_step':end,
                'initial_reserves_total':reserves(initial),'final_reserves_total':reserves(rows[end]),
                'player_changed':rows[end][0x47]!=initial[0x47]}
    if route_kind=='fish-envelope':
        collection=next((i for i in range(max(1,active_start),len(rows)) if rows[i][0x77]==rows[i-1][0x77]+1),None)
        if collection is None:raise ValueError('observed fish collection required')
        before,r=rows[collection-1],rows[collection]
        removed=[row for row in range(4) if before[0x5C+row]!=r[0x5C+row]]
        if (len(removed)!=1 or r[0x74]!=91 or r[0x67]!=16 or r[0x6A]!=0
                or before[0x11+removed[0]]&3!=1):raise ValueError('source fish segment/envelope entry required')
        row=removed[0];old,new=before[0x5C+row],r[0x5C+row]
        if new&~old or (old^new).bit_count()!=1:raise ValueError('exactly one real fish segment must be removed')
        previous=r;awards=0;end=None
        for i in range(collection+1,len(rows)):
            r=rows[i];expected=previous[0x74]-1
            if expected&31==0:expected=0
            delta=(score(r)-score(previous))%1000000;award=10 if expected&3 else 0
            if r[0x74]!=expected or delta!=award:raise ValueError('fish delayed reward/envelope ordering differs')
            awards+=int(bool(award));previous=r
            if expected==0:end=i;break
        if end is None or awards!=20 or (score(rows[end])-score(rows[collection]))%1000000!=200:
            raise ValueError('complete twenty-award fish envelope required')
        return {'kind':route_kind,'collection_step':collection,'reward_end_step':end,'fish_row':row,'awards':awards,'reward_points':200}
    if route_kind=='threat-push':
        attach=next((i for i in range(max(1,active_start),len(rows)) if rows[i][0x72]<4 and rows[i-1][0x72]>=128),None)
        if attach is None:raise ValueError('observed source threat attachment required')
        row=rows[attach][0x72];r=rows[attach]
        if not r[0x31+row*2]&128 or r[0x11+row]&3==1 or r[0x6A]!=0:raise ValueError('real grounded odd threat contact required')
        push=next((i for i in range(attach+1,len(rows)) if rows[i][0x72]==row and rows[i][0x71]==0
                   and rows[i][0x66]!=rows[i-1][0x66]),None)
        if push is None:raise ValueError('observed attached-row movement required')
        death=next((i for i in range(push+1,len(rows)) if rows[i][0x71]&128),None)
        if death is not None:end=recovery(rows,death,initial);exit_kind='death/recovery'
        else:
            end=next((i for i in range(push+1,len(rows)) if rows[i][0x72]>=128 and rows[i][0x71]==0 and rows[i][0x6A]==0),None);exit_kind='released'
            if end is None:raise ValueError('explicit threat release or death/recovery required')
        return {'kind':route_kind,'attachment_step':attach,'row':row,'push_step':push,'completion_step':end,'exit':exit_kind}
    if route_kind in ('water-death','temperature-death'):
        water=route_kind=='water-death'
        death=next((i for i in range(active_start,len(rows)) if (rows[i][0x71]&128 and rows[i][0x64]>27 and rows[i][0x6A]==0 if water
                   else rows[i][0x71]&16 and rows[i][0x65]==0)),None)
        if death is None:raise ValueError('distinct source water/temperature death entry required')
        end=recovery(rows,death,initial)
        return {'kind':route_kind,'death_step':death,'recovery_step':end,'entry_flag':128 if water else 16}
    raise ValueError('known explicit hazard interaction predicate required')


def prepare_inputs(config,case):
    result=[NEUTRAL]*case['warmup']
    for _ in range(case['variation']):result.extend([{**NEUTRAL,'swchb':61}]+[NEUTRAL]*config['select_release_intervals'])
    return result+[{**NEUTRAL,'swchb':62}]+[NEUTRAL]*config['reset_release_intervals']


def fish_input(ram):
    if ram[0x77] or ram[0x71] or ram[0x67] or ram[0x46]:return dict(NEUTRAL)
    x,y=ram[0x66],ram[0x64];row=fish_row(ram);target=ram[0x54+row];target_y=53+(3-row)*26
    desired=target+3 if ram[0x11+row]&3==1 and 24<=target<=132 else 80
    direction=127 if x<desired-1 else 191 if x>desired+1 else 255
    if ram[0x6A]==0:
        if y<target_y:direction&=223
        elif y>target_y:direction&=239
        elif ram[0x11+row]&3!=1 and 8<=target<=151 and abs(x-target)<24:direction&=239
    player=ram[0x47]
    return {**NEUTRAL,'swcha':direction if player==0 else (direction>>4)|240}


def fish_row(ram):
    candidates=[row for row in range(4) if ram[0x11+row]&3==1]
    return min(candidates,key=lambda row:(not 24<=ram[0x54+row]<=132,abs(53+(3-row)*26-ram[0x64]))) if candidates else 2


def body_batch(kind,ram,remaining):
    if kind!='fish-envelope' or ram[0x77] or ram[0x71] or ram[0x67] or ram[0x46]:return min(10,remaining)
    row=fish_row(ram)
    near=ram[0x6A]==0 and ram[0x11+row]&3==1 and abs(ram[0x66]-ram[0x54+row])<24
    return min(1 if near else 4,remaining)


def finish_producer(producer):
    if any(digest(ROOT/name)!=sha for name,sha in producer['utility_fingerprints'].items()):
        raise ValueError('frozen source route helper closure changed')
    return {'observed_final_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'observed_final_dirty':bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())}


def capture(out,kind,stella='stella'):
    if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip():raise ValueError('clean committed source route start required')
    producer=snapshot_paths(HELPERS);config=json.loads(CONFIG.read_text());case=config['routes'][kind]
    if config['schema_version']!=1 or config['source_sha256']!=verified_input(ROOT/'references/roms/frostbite.bin')['sha256']:
        raise ValueError('exact original source route configuration required')
    if not 1<=case['maximum_intervals']<=5000 or case['variation'] not in range(4):raise ValueError('bounded original route required')
    out=private_output(out);out.mkdir(parents=True,exist_ok=False);rom=ROOT/'references/roms/frostbite.bin'
    initial,backend=poweron_capsule(rom,out/'poweron',case['seed'],config['riot_timer_preset'],stella)
    prep=prepare_inputs(config,case);policy={'host_seed':case['seed'],'variation':case['variation'],'kind':kind,
          'preparation_intervals':len(prep),'ram_injections':{},'source_hazards_disabled':False,'instruction_skipping':False,
          'raw_input_every_interval':True,'boundary':'Unchanged original PCF019 every interval; controlled cold power-on and real Select/Reset',
          'initialization':'poweron_capsule; no active source state or contact writes'}
    validate_policy(policy);points=[];inputs=[];journal=[];current=initial;trace=None;assessment=None
    def segment(samples,label):
        nonlocal current,trace
        path=out/label;trace,current=capture_steps(rom,current,samples,path,stella,policy)
        if trace['backend']!=backend:raise ValueError('original route backend changed')
        for point in trace['steps']:point['index']=len(points);points.append(point)
        inputs.extend(samples);journal.append({'path':label,'intervals':len(samples),'trace_sha256':digest(path/'trace.json'),
                                                'final_sha256':digest(path/'final.state')})
    segment(prep,'prepare');start=len(points)
    if kind=='bear-refuge':
        approach=refuge_approach(case['floe_alignment_wait']);segment(approach+[NEUTRAL]*case['bear_wait'],'refuge')
        assessment=assess(points,kind,start,start+len(approach))
    else:
        body=0;last_error='predicate not reached'
        while body<case['maximum_intervals']:
            r=decode_state(current)['ram'];n=body_batch(kind,r,case['maximum_intervals']-body)
            samples=[fish_input(r) if kind=='fish-envelope' else dict(NEUTRAL) for _ in range(n)]
            segment(samples,f'body-{body:04d}');body+=n
            try:assessment=assess(points,kind,start)
            except ValueError as error:last_error=str(error)
            else:break
            if r[0x45]&128 or r[0x46]&128:break
            if body%100==0:print(f'HAZARD_ROUTE_PROGRESS {kind} intervals={body} X={r[0x66]} Y={r[0x64]} fish={r[0x77]} reserves={reserves(r)}',flush=True)
        if assessment is None:
            (out/'failure.json').write_text(json.dumps({'kind':kind,'intervals':body,'reason':last_error,'journal':journal},indent=2)+'\n')
            raise ValueError(f'bounded original route failed: {kind}: {last_error}; {out}')
    combined={**trace,'initial_sha256':hashlib.sha256(initial).hexdigest(),'steps':points,'policy':policy};validate_trace(combined)
    (out/'trace.json').write_text(json.dumps(combined,indent=2)+'\n');(out/'inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
    (out/'initial.state').write_bytes(initial);(out/'final.state').write_bytes(current);(out/'journal.json').write_text(json.dumps(journal,indent=2)+'\n')
    report={'schema_version':1,**producer,**finish_producer(producer),'clean_start':True,'kind':kind,'backend':backend,'steps':len(points),
            'assessment':assessment,'preparation_intervals':len(prep),'source_initial_rng':points[start]['ram'][2],
            'files':{name:digest(out/name) for name in ('trace.json','inputs.json','initial.state','final.state','journal.json')},
            'scope':'Unmodified original input-only named route, complete source state checkpoints. Native real-device replay, whole-frame timing, manual and physical acceptance are separate.'}
    (out/'route.json').write_text(json.dumps(report,indent=2)+'\n');return report


def replay(original,out,stella='stella'):
    producer=snapshot_paths(HELPERS);original=Path(original);receipt=json.loads((original/'route.json').read_text())
    audit_manifest(receipt,HELPERS)
    if receipt.get('clean_start') is not True:raise ValueError('clean original route producer required')
    if any(digest(original/name)!=sha for name,sha in receipt['files'].items()):raise ValueError('original route evidence changed')
    expected=json.loads((original/'trace.json').read_text());validate_trace(expected);validate_policy(expected['policy'])
    inputs=json.loads((original/'inputs.json').read_text());journal=json.loads((original/'journal.json').read_text())
    if len(inputs)!=len(expected['steps']) or sum(item['intervals'] for item in journal)!=len(inputs):raise ValueError('complete source input/restore journal required')
    out=private_output(out);out.mkdir(parents=True,exist_ok=False);current=(original/'initial.state').read_bytes();points=[];cursor=0;combined=None
    for i,entry in enumerate(journal):
        path=original/entry['path']
        if digest(path/'trace.json')!=entry['trace_sha256'] or digest(path/'final.state')!=entry['final_sha256']:
            raise ValueError('original restore segment changed')
        samples=inputs[cursor:cursor+entry['intervals']];cursor+=len(samples)
        combined,current=capture_steps(ROOT/'references/roms/frostbite.bin',current,samples,out/f'segment-{i:04d}',stella,expected['policy'])
        for point in combined['steps']:point['index']=len(points);points.append(point)
    combined={**combined,'initial_sha256':expected['initial_sha256'],'steps':points};differences=compare_traces(expected,combined)
    if differences or current!=(original/'final.state').read_bytes():raise ValueError('complete original route replay differs: '+str(differences[:3]))
    (out/'trace.json').write_text(json.dumps(combined,indent=2)+'\n');(out/'final.state').write_bytes(current)
    report={**producer,**finish_producer(producer),'complete':True,'steps':len(points),'route_sha256':digest(original/'route.json'),
            'identical_full_cpu_ram_tia_riot_inputs':True,'replay_trace_sha256':digest(out/'trace.json')}
    (out/'replay.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--kind',choices=('bear-refuge','bear-chase','fish-envelope'));parser.add_argument('--replay',type=Path);args=parser.parse_args()
    if not args.replay and not args.kind:parser.error('select a named source route or an existing replay')
    result=replay(args.replay,args.out) if args.replay else capture(args.out,args.kind)
    print(json.dumps({key:result[key] for key in ('steps','assessment') if key in result},indent=2))
