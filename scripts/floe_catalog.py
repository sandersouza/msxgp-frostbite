"""Capture the complete original-clock floe domain into ignored local evidence.

Each P0 X, floe X and legal NUSIZ pair is measured, with all 228 literal views
and both source latch channels. Deduplication is byte-exact after capture.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from environment import ROOT
from floe_truth import roi_record, validate_row
from reference_inventory import verified_input
from reference_state import decode_state
from reference_traces import private_output
from stella_floe import control_pairs,digest,fixture,helper_identity,observe

YS=(0,*range(45,78))


def validate_partitions(parts,controls):
    cursor=0;count=0
    for part in sorted(parts,key=lambda value:value['start']):
        a,b=part['start'],part['stop']
        if type(a) is not int or type(b) is not int or a!=cursor or not a<b<=160 or part['cases']!=(b-a)*len(YS)*controls*160:
            raise ValueError('complete nonoverlapping160-X partition receipts required')
        cursor=b;count+=part['cases']
    if cursor!=160:raise ValueError('complete160-X catalog required')
    return count


def intern_rows(rows):
    pool=[];lookup={};indices=[]
    for row in rows:
        validate_row(row);row=bytes(row)
        if row not in lookup:lookup[row]=len(pool);pool.append(row)
        indices.append(lookup[row])
    return pool,indices


def producer():
    return {**helper_identity(),'scripts/floe_catalog.py':digest(__file__)}


def worker(args):
    start,stop,out_string,binary_string,initial_string,controls,identity=args
    out=Path(out_string);binary=Path(binary_string);initial=Path(initial_string).read_bytes()
    base=decode_state(initial)['ram'];rom=ROOT/'references/roms/frostbite.bin'
    directory=out/f'worker-{start:03d}-{stop:03d}';directory.mkdir(exist_ok=False)
    receipts=[];count=0
    for px in range(start,stop):
        target=directory/f'player-{px:03d}.truth'
        with target.open('wb') as stream:
            for offset in range(0,len(YS),4):
                ys=YS[offset:offset+4]
                cases=[fixture(base,px,y,fx,pair) for y in ys for pair in controls for fx in range(160)]
                data,receipt=observe(rom,binary,initial,cases,directory/f'px-{px:03d}-y-{offset:02d}',roi=True)
                rows=[]
                for index,case in enumerate(cases):
                    record=roi_record(data[index*78:(index+1)*78]);row=record['truth']
                    actual=7|(128 if row[0]&1 else 0)|(64 if row[29]&1 else 0)
                    if actual!=record['actual']:raise ValueError('actual-view original latch disagrees with sidecar')
                    rows.append(row)
                stream.write(b''.join(rows));count+=len(cases)
                receipts.append({'path':str((directory/f'px-{px:03d}-y-{offset:02d}'/'observation.json').relative_to(out)),
                                 'sha256':digest(directory/f'px-{px:03d}-y-{offset:02d}'/'observation.json')})
                if producer()!=identity:raise ValueError('catalog producer changed during capture')
        print(f'FLOE_CATALOG_PROGRESS {px+1} {start} {stop} {count}',flush=True)
    result={'start':start,'stop':stop,'cases':count,'receipts':receipts,
            'profiles':{path.name:digest(path) for path in directory.glob('player-*.truth')}}
    (directory/'partition.json').write_text(json.dumps(result,indent=2)+'\n');return result


def capture(out,binary,initial_path,workers=4):
    if type(workers) is not int or not 1<=workers<=4:raise ValueError('one to four independent bounded workers required')
    original=verified_input(ROOT/'references/roms/frostbite.bin');rom=(ROOT/'references/roms/frostbite.bin').read_bytes()
    initial=Path(initial_path).read_bytes();state=decode_state(initial)
    if state['cpu']['pc']!=0xF019:raise ValueError('complete original F019 capsule required')
    if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip():raise ValueError('clean committed capture producer required')
    out=private_output(out);out.mkdir(parents=True,exist_ok=False)
    binary=Path(binary).resolve();owned_binary=out/'stella';shutil.copyfile(binary,owned_binary);owned_binary.chmod(0o755)
    (out/'initial.state').write_bytes(initial);controls=control_pairs(rom);identity=producer()
    plan={'schema_version':1,'original':original,'producer_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
          'helpers':identity,'binary_sha256':digest(owned_binary),'initial_sha256':digest(out/'initial.state'),
          'player_x':list(range(160)),'floe_x':list(range(160)),'ys':YS,'controls':controls,'views':228,
          'channels':'P0/P1-or-M1 bit7 and M1/P1 bit6; both with electrical low bits07',
          'ram_injections':'Declared controlled geometry fixtures, not a natural route','expected_cases':160*len(YS)*len(controls)*160}
    (out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    jobs=[(i*160//workers,(i+1)*160//workers,str(out),str(owned_binary),str(out/'initial.state'),controls,identity) for i in range(workers)]
    with ProcessPoolExecutor(max_workers=workers) as executor:parts=list(executor.map(worker,jobs))
    count=validate_partitions(parts,len(controls))
    if producer()!=identity or digest(owned_binary)!=plan['binary_sha256']:raise ValueError('producer/backend identity drift')
    result={**plan,'cases':count,'partitions':parts,'complete':True}
    (out/'catalog.json').write_text(json.dumps(result,indent=2)+'\n');return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--binary',type=Path,required=True);parser.add_argument('--initial',type=Path,required=True)
    parser.add_argument('--workers',type=int,default=4);args=parser.parse_args()
    result=capture(args.out,args.binary,args.initial,args.workers);print(json.dumps({'cases':result['cases'],'complete':result['complete']}))
