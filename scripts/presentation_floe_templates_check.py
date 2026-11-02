"""Finite source-mask template proof; no native/frame/original-raster verdict."""
import argparse
from functools import reduce
import hashlib
import json
from pathlib import Path

from environment import ROOT
from presentation_fast_model import prepare
from presentation_fixed_floe import strip
from presentation_fixed_floe_check import FILES as BASE_FILES
from presentation_floe_templates import compile_templates,read_template,read_pattern
from presentation_palette import audit_palette
from presentation_source_cases import verify_files
from reference_traces import private_output

FILES=tuple(dict.fromkeys((*BASE_FILES,'scripts/presentation_floe_templates.py','scripts/presentation_floe_templates_check.py')))


def check(out,geometry):
    sha=lambda data:hashlib.sha256(data).hexdigest()
    producer={name:sha((ROOT/name).read_bytes()) for name in FILES}
    geometry=Path(geometry).resolve();config=json.loads((ROOT/'references/presentation-assets-config.json').read_text())
    palette_path=ROOT/config['palette'];palette=audit_palette(palette_path);original=ROOT/'references/roms/frostbite.bin'
    palette_files=sorted(p for p in palette_path.rglob('*') if p.is_file()) if palette_path.is_dir() else [palette_path]
    consumed={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in (original,*palette_files,geometry/'geometry.json',*sorted(geometry.glob('geometry-*.bin')))}
    tables=prepare(original.read_bytes(),palette,geometry);compiled=compile_templates(tables)
    out=private_output(out);out.mkdir(parents=True,exist_ok=False)
    blobs=compiled['files']
    for name,data in blobs.items():(out/name).write_bytes(data)
    cases=0
    for phase in range(8):
        for delta in compiled['deltas']:
            for root in range(160):
                expected=strip(tables,root,delta,88+phase,15)
                wanted={cell:bytes(reduce(int.__or__,(layer['pattern'][y] for layer in layers),0) for y in range(8)) for cell,layers in expected['layers'].items()}
                rendered=read_template(compiled,root,delta,88+phase)
                actual={cell:read_pattern(blobs['pattern-pairs.bin'],blobs['pattern-halves.bin'],identifier) for cell,identifier in rendered.items()}
                if actual!=wanted:raise ValueError(f'finite floe template differs: phase{phase} delta{delta} root{root}')
                cases+=1
        print(f'phase{phase}: {cases} zero-difference whole-strip masks',flush=True)
    if any((out/name).read_bytes()!=data for name,data in blobs.items()):raise ValueError('persisted finite template changed')
    verify_files(consumed)
    if any(sha((ROOT/name).read_bytes())!=value for name,value in producer.items()):raise ValueError('finite template producer changed')
    metadata={k:v for k,v in compiled.items() if k!='files'}
    report={**metadata,'complete':True,'cases':cases,'producer_files':producer,'input_files':consumed,
        'files':{name:sha(data) for name,data in blobs.items()},'bytes':{name:len(data) for name,data in blobs.items()},
        'native_accepted':False,'frame_deadline_accepted':False,
        'scope':'1280 source-mask templates over ten original control-pair deltas, sixteen X phases and eight Y phases; all12800 world translations match the independently walked legacy strip masks. Full logical pattern/half-dictionary identity. Not new original rasters, native integration or frame acceptance.'}
    (out/'check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('complete','cases','patterns','max_slots','bytes')}));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--geometry',type=Path,required=True)
    check(**vars(p.parse_args()))
