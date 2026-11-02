"""Finite floe capacity over all roots, signed motion deltas and Y phases.

These are algebra cases using original-derived masks, not new original rasters.
"""
import argparse
import hashlib
import json
from pathlib import Path

from environment import ROOT
from presentation_fixed_floe import strip
from presentation_fixed_check import FILES as BASE_FILES
from presentation_fast_model import prepare
from presentation_palette import audit_palette
from presentation_source_cases import verify_files
from reference_traces import private_output

FILES=tuple(dict.fromkeys((*BASE_FILES,'scripts/presentation_fixed_floe_check.py')))


def run(out,geometry):
    sha=lambda data:hashlib.sha256(data).hexdigest()
    producers={name:sha((ROOT/name).read_bytes()) for name in FILES}
    config=json.loads((ROOT/'references/presentation-assets-config.json').read_text());palette_path=ROOT/config['palette'];palette=audit_palette(palette_path)
    geometry=Path(geometry).resolve();original=ROOT/'references/roms/frostbite.bin'
    palette_inputs=sorted(p for p in palette_path.rglob('*') if p.is_file()) if palette_path.is_dir() else [palette_path]
    inputs={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in (original,*palette_inputs,geometry/'geometry.json',*sorted(geometry.glob('geometry-*.bin')))}
    tables=prepare(original.read_bytes(),palette,geometry);out=private_output(out);out.mkdir(parents=True,exist_ok=False)
    maximum=0;argmax=None;counts={};cases=0
    for phase in range(8):
        for delta in range(-11,20):
            for root in range(160):
                try:rendered=strip(tables,root,delta,88+phase,15)
                except ValueError as error:
                    (out/'failure.json').write_text(json.dumps({'phase':phase,'delta':delta,'root':root,'error':str(error)},indent=2)+'\n')
                    raise
                count=len(rendered['keys']);cases+=1;counts[count]=counts.get(count,0)+1
                if count>maximum:maximum=count;argmax={'phase':phase,'delta':delta,'root':root}
        print(f'phase{phase}: {cases} algebra cases, max{maximum}/16 slots',flush=True)
    verify_files(inputs)
    if any(sha((ROOT/name).read_bytes())!=value for name,value in producers.items()):raise ValueError('finite floe capacity producer changed')
    result={'complete':True,'cases':cases,'max_slots':maximum,'argmax':argmax,'histogram':counts,'producer_files':producers,'input_files':inputs,
        'native_accepted':False,'frame_deadline_accepted':False,
        'scope':'39680 pure floe geometry/key-capacity cases: all160 roots, signed delta-11..19 and all8 Y phases. Not additional original rasters or native/frame acceptance.'}
    (out/'check.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'complete':True,'cases':cases,'max_slots':maximum}));return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--geometry',type=Path,required=True)
    run(**vars(p.parse_args()))
