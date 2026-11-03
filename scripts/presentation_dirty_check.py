"""Prove changed source-backed background pixels lie within declared dirty rows."""
import argparse
import hashlib
import json
from pathlib import Path

from environment import ROOT
from presentation_check import decode_target
from presentation_dirty import scene,dirty_rows
from presentation_fast_model import prepare,frame
from presentation_palette import audit_palette
from presentation_source_cases import collect,verify_files,FILES as SOURCE_FILES
from reference_traces import private_output

FILES=tuple(dict.fromkeys((*SOURCE_FILES,'scripts/presentation_dirty.py','scripts/presentation_dirty_check.py',
    'scripts/presentation_fast_model.py','scripts/presentation_check.py','scripts/presentation_constructors.py',
    'scripts/presentation_static_assets.py','scripts/presentation_fragments.py','scripts/presentation_palette.py')))


def check(out,geometry):
    sha=lambda data:hashlib.sha256(data).hexdigest()
    producer={name:sha((ROOT/name).read_bytes()) for name in FILES}
    domain=collect();config=json.loads((ROOT/'references/presentation-assets-config.json').read_text())
    palette=audit_palette(ROOT/config['palette']);original=ROOT/'references/roms/frostbite.bin'
    geometry=Path(geometry).resolve()
    inputs={str(path.relative_to(ROOT)):sha(path.read_bytes()) for path in
        (original,geometry/'geometry.json',*sorted(geometry.glob('geometry-*.bin')))}
    tables=prepare(original.read_bytes(),palette,geometry)
    out=private_output(out);out.mkdir(parents=True,exist_ok=False);histories=[None,None];images=[None,None];rows=[]
    for index,case in enumerate(domain['cases']):
        generation=index&1;state=scene(case['ram'],tables['background']['rng_index'])
        dirty=dirty_rows(histories[generation],state)
        pixels=decode_target(frame(tables,case['ram'])['vram'],bytes((2,0xC2,6,255,3,0x36,7,1)))
        previous=images[generation];changed=set()
        if previous is not None:
            changed={at//2048 for at,(a,b) in enumerate(zip(previous,pixels)) if a!=b}
            if changed-dirty:raise ValueError(f'{case["id"]}: changed pixels escape dirty rows{sorted(changed-dirty)}')
        rows.append({'id':case['id'],'family':case['family'],'generation':generation,'state':list(state),
            'dirty_rows':sorted(dirty),'actual_changed_rows':sorted(changed)})
        histories[generation]=state;images[generation]=pixels
        if (index+1)%100==0:print(f'{index+1}/2115 dirty dependencies cover every changed background pixel',flush=True)
    verify_files(domain['files']);verify_files(inputs)
    if any(sha((ROOT/name).read_bytes())!=value for name,value in producer.items()):raise ValueError('dirty model producer changed during comparison')
    result={'producer_files':producer,'source_files':domain['files'],'input_files':inputs,'cases':rows,
        'source_receipt_sha256':domain['source_receipt_sha256'],'complete':True,
        'scope':'Host dirty-row dependency proof on all2115 source-backed backgrounds. P0/door/logo sprites are owned separately. No native/frame/human-ROM acceptance.'}
    (out/'check.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'cases':len(rows),'complete':True}));return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--geometry',type=Path,required=True)
    check(**vars(p.parse_args()))
