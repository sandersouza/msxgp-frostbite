"""Real-key cold replay of a verified original input-only interaction route."""
import argparse
import json
from pathlib import Path

from hazard_build import OUT
from hazard_check import run_target
from hazard_routes import HELPERS as SOURCE_HELPERS,assess,validate_policy
from reference_provenance import audit_manifest
from reference_traces import private_output
from stella_hazard import digest
from trace_compare import validate_trace


def input_records(inputs,points):
    if len(inputs)!=len(points):raise ValueError('complete original real-device input route required')
    result=bytearray()
    for i,(sample,point) in enumerate(zip(inputs,points)):
        if point['input']!=sample or len(sample['fire'])!=2:raise ValueError('original raw inputs differ from source checkpoints')
        player=points[i-1]['ram'][0x47] if i else 0
        # Both original joysticks are represented. One physical keyboard serves
        # the active player; the inactive original controller must stay neutral.
        if player not in (0,1) or sample['fire'][1-player]:raise ValueError('active-player keyboard route required')
        if player==0 and sample['swcha']&15!=15 or player==1 and sample['swcha']&240!=240:
            raise ValueError('inactive controller must remain neutral in keyboard route')
        result.extend((sample['swcha'],sample['swchb'],int(sample['fire'][0]),int(sample['fire'][1])))
    return bytes(result)


def natural(source,out,build_dir=OUT,explore=False,inject='none'):
    source=Path(source);receipt=json.loads((source/'route.json').read_text());audit_manifest(receipt,SOURCE_HELPERS)
    if receipt.get('clean_start') is not True or any(digest(source/name)!=sha for name,sha in receipt['files'].items()):
        raise ValueError('clean immutable original source route required')
    trace=json.loads((source/'trace.json').read_text());validate_trace(trace);validate_policy(trace['policy'])
    inputs=json.loads((source/'inputs.json').read_text());records=input_records(inputs,trace['steps'])
    expected=[{'ram':point['ram'],'registers':{key:point['cpu'][key] for key in ('a','x','y','p','sp')}} for point in trace['steps']]
    report,actual=run_target(out,build_dir,records,expected,natural=True,explore=explore,inject=inject,
                             additional_helpers=('scripts/hazard_play.py',*SOURCE_HELPERS))
    points=[{**point,'index':i} for i,point in enumerate(actual)]
    assessment=assess(points,receipt['kind'],receipt['preparation_intervals'],receipt['assessment'].get('approach_end'))
    if assessment!=receipt['assessment']:raise ValueError('actual native interaction sequence differs from original')
    report.update(assessment=assessment,original_route_sha256=digest(source/'route.json'),
                  scope='Actual standard MSX1 cold initialization and physical keyboard/console inputs; all source CPU/all128RAM checkpoints and named interaction predicate match. No canonical source-state/contact injections. Paced/manual/physical evidence is separate.')
    out=private_output(out);(out/'natural.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--build-dir',type=Path,default=OUT);parser.add_argument('--explore',action='store_true')
    parser.add_argument('--inject',choices=('none','rng','row_priority','sticky'),default='none');args=parser.parse_args()
    result=natural(args.source,args.out,args.build_dir,args.explore,args.inject);print(json.dumps({'cases':result['cases'],'assessment':result['assessment']}))
