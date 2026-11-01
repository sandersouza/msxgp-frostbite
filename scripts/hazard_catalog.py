"""Capture bounded, source-clock contact components with frozen producers.

Component completeness is distinct from complete gameplay/native acceptance.
Original-derived raw cases, profiles and backends remain local and ignored.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import shutil
import subprocess

from environment import ROOT
from floe_truth import roi_record,sample
from hazard_domain import bear_modes,object_modes,shapes
from reference_inventory import verified_input
from reference_provenance import audit_manifest,snapshot_paths
from reference_routes import source_reset_checkpoint
from reference_state import decode_state
from reference_traces import private_output
from stella_hazard import HELPERS as OBSERVER_HELPERS,digest,fixture,observe,verified_backend

EDGE_XS=(*range(9),*range(152,160))
ROW_YS=(0,*range(32,66))
SHORE_YS=(0,*range(4,57))
HELPERS=tuple(dict.fromkeys((*OBSERVER_HELPERS,'scripts/hazard_domain.py','scripts/hazard_catalog.py','scripts/reference_routes.py')))


def capture_plan(kind,rom,players=None):
    domain=shapes(rom);reps,aliases=bear_modes(rom)
    if kind=='edge':
        full_players=list(EDGE_XS);ys=list(ROW_YS);coordinates=list(range(160))
        modes=[{'shape':shape,'reflection':reflection,'nusiz':copies} for shape,reflection,copies in object_modes(rom)]
    elif kind=='ordinary':
        full_players=list(range(9,152));ys=list(ROW_YS);coordinates=list(range(-7,8))
        modes=[{'shape':shape,'reflection':reflection,'nusiz':0} for shape in domain for reflection in (False,True)]
    elif kind=='shore':
        full_players=list(range(160));ys=list(SHORE_YS);coordinates=list(range(160))
        modes=[{'bear_pose':pose,'reflection':reflection} for pose in reps for reflection in (False,True)]
    elif kind=='aliases':
        full_players=list(range(9,152));ys=list(ROW_YS);coordinates=list(range(160));modes=[{'nusiz':count} for count in range(4)]
    else:raise ValueError('unknown original contact component')
    selected=full_players if players is None else list(players)
    if (not selected or any(type(px) is not int or px not in full_players for px in selected)
            or selected!=sorted(set(selected))):raise ValueError('unique ordered player coordinates in the declared component required')
    per_player=len(ys)*len(modes)*len(coordinates)
    return {'schema_version':1,'kind':kind,'player_x':selected,'full_player_x':full_players,'ys':ys,'coordinates':coordinates,
            'modes':modes,'shapes':domain,'bear_pose_aliases':aliases,'cases_per_player':per_player,
            'expected_cases':len(selected)*per_player,'complete_component_domain':selected==full_players,
            'profile_order':'Y, mode, coordinate; each record has both228-bit channels'}


def validate_partitions(parts,plan):
    cursor=0;count=0
    for part in sorted(parts,key=lambda item:item['start']):
        start,stop=part['start'],part['stop']
        if (type(start) is not int or type(stop) is not int or start!=cursor or not start<stop<=len(plan['player_x'])
                or part['cases']!=(stop-start)*plan['cases_per_player']):
            raise ValueError('complete nonoverlapping contact component partitions required')
        cursor=stop;count+=part['cases']
    if cursor!=len(plan['player_x']) or count!=plan['expected_cases']:raise ValueError('complete declared player domain required')
    return count


def make_case(plan,base,px,y,mode_index,coordinate):
    mode=plan['modes'][mode_index];kind=plan['kind']
    if kind=='shore':
        ram=bytearray(fixture(base,px,y,64,plan['shapes'][0],0,bear_x=coordinate))
        ram[0x6F]=mode['bear_pose'];ram[0x6C]=16 if mode['reflection'] else 0
        return bytes(ram)
    if kind=='aliases':
        shape=plan['shapes'][(px+y+coordinate+mode['nusiz'])%len(plan['shapes'])]
        return fixture(base,px,y,coordinate,shape,mode['nusiz'],bool((px^coordinate^y)&1))
    x=(px-coordinate)%160 if kind=='ordinary' else coordinate
    return fixture(base,px,y,x,mode['shape'],mode['nusiz'],mode['reflection'])


def producer():
    return {name:digest(ROOT/name) for name in HELPERS}


def worker(args):
    start,stop,out_string,plan,identity=args
    out=Path(out_string);initial=(out/'initial.state').read_bytes();base=decode_state(initial)['ram']
    binary=out/'stella';directory=out/f'worker-{start:03d}-{stop:03d}';directory.mkdir(exist_ok=False)
    count=0;profiles={};receipts=[]
    for px in plan['player_x'][start:stop]:
        path=directory/f'player-{px:03d}.truth'
        with path.open('wb') as stream:
            for yi,y in enumerate(plan['ys']):
                entries=[(mode,coordinate) for mode in range(len(plan['modes'])) for coordinate in plan['coordinates']]
                for offset in range(0,len(entries),8192):
                    chosen=entries[offset:offset+8192]
                    cases=[make_case(plan,base,px,y,mode,coordinate) for mode,coordinate in chosen]
                    target=directory/f'px-{px:03d}-y-{yi:02d}-batch-{offset:05d}'
                    data,receipt=observe(ROOT/'references/roms/frostbite.bin',binary,initial,cases,target,
                                         roi=plan['kind']!='shore',shore=plan['kind']=='shore')
                    for index in range(len(cases)):
                        record=roi_record(data[index*78:(index+1)*78])
                        if sample(record['truth'],0)!=record['actual']:raise ValueError('source actual view differs from contact sidecar')
                        stream.write(record['truth'])
                    count+=len(cases)
                    receipts.append({'path':str((target/'observation.json').relative_to(out)),
                                     'sha256':digest(target/'observation.json'),'player_x':px,'y_index':yi,'offset':offset,'cases':len(cases)})
                    if producer()!=identity:raise ValueError('committed source helper closure changed during capture')
                print(f'HAZARD_CATALOG_PROGRESS {plan["kind"]} player={px} y={yi+1}/{len(plan["ys"])} cases={count}',flush=True)
        if path.stat().st_size!=plan['cases_per_player']*58:raise ValueError('partial source profile')
        profiles[path.name]=digest(path)
    result={'start':start,'stop':stop,'cases':count,'profiles':profiles,'receipts':receipts}
    (directory/'partition.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def capture(out,binary,initial_path,workers=4,kind='edge',players=None,exploratory=False):
    if type(workers) is not int or not 1<=workers<=4:raise ValueError('one to four bounded source workers required')
    original=verified_input(ROOT/'references/roms/frostbite.bin');rom=(ROOT/'references/roms/frostbite.bin').read_bytes()
    plan=capture_plan(kind,rom,players)
    if not plan['complete_component_domain'] and not exploratory:raise ValueError('partial domains must be explicitly exploratory')
    dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    if dirty and not exploratory:raise ValueError('clean committed source producer required at capture start')
    snapshot=snapshot_paths(HELPERS);backend=verified_backend(binary)
    if backend.get('producer_dirty') is not False:raise ValueError('clean recorded observer build required')
    audit_manifest({'tool_source_commit':backend['producer_commit'],'utility_fingerprints':backend['helpers']},OBSERVER_HELPERS)
    initial=Path(initial_path).read_bytes();state=decode_state(initial)
    prepared,provenance=source_reset_checkpoint(ROOT/'outputs/reference-traces/summary.json')
    if initial!=prepared or state['cpu']['pc']!=0xF019:raise ValueError('verified active original preparation capsule required')
    out=private_output(out);out.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(binary,out/'stella');(out/'stella').chmod(0o755)
    shutil.copyfile(Path(binary).parent/'frostbite-hazard-observer.json',out/'frostbite-hazard-observer.json')
    (out/'initial.state').write_bytes(initial)
    plan={**plan,'source':original,'producer_commit':snapshot['tool_source_commit'],'helpers':snapshot['utility_fingerprints'],
          'producer_dirty_at_start':dirty,'exploratory':bool(exploratory),'binary_sha256':digest(out/'stella'),
          'backend_build':backend,'backend_build_sha256':digest(out/'frostbite-hazard-observer.json'),
          'initial_sha256':digest(out/'initial.state'),'preparation':provenance,
          'ownership':'Controlled original RAM geometry; no natural-play claim; frozen committed source helper closure'}
    (out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    workers=min(workers,len(plan['player_x']));size=len(plan['player_x'])
    jobs=[(i*size//workers,(i+1)*size//workers,str(out),plan,snapshot['utility_fingerprints']) for i in range(workers)]
    with ProcessPoolExecutor(max_workers=workers) as pool:parts=list(pool.map(worker,jobs))
    count=validate_partitions(parts,plan)
    if producer()!=snapshot['utility_fingerprints'] or digest(out/'stella')!=plan['binary_sha256']:
        raise ValueError('source producer/backend changed during capture')
    result={**plan,'cases':count,'partitions':parts,'complete':True}
    (out/'catalog.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kind',choices=('edge','ordinary','shore','aliases'),default='edge')
    parser.add_argument('--out',type=Path,required=True);parser.add_argument('--workers',type=int,default=4)
    parser.add_argument('--binary',type=Path,default=ROOT/'outputs/hazards/observer-shore-source/stella')
    parser.add_argument('--initial',type=Path,default=ROOT/'outputs/floes/catalog-issue11-b/initial.state')
    parser.add_argument('--players',help='Explicit comma-separated exploratory player subset')
    parser.add_argument('--exploratory',action='store_true');args=parser.parse_args()
    selected=None if args.players is None else [int(item) for item in args.players.split(',')]
    report=capture(args.out,args.binary,args.initial,args.workers,args.kind,selected,args.exploratory)
    print(json.dumps({key:report[key] for key in ('kind','complete','complete_component_domain','exploratory','cases','producer_commit')}))
