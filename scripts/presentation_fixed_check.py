"""Compare fixed physical roles with every independently frozen original raster."""
import argparse
import hashlib
import json
from pathlib import Path

from environment import ROOT
from graphics_mapping import map_frame
from presentation_fixed import COUNTS
from presentation_fixed_model import prepare,frame,full_pixels
from presentation_fast_model_check import FILES as BASE_FILES
from presentation_palette import audit_palette
from presentation_source_cases import collect,verify_files
from reference_traces import private_output

FILES=tuple(dict.fromkeys((*BASE_FILES,'scripts/presentation_build.py','scripts/presentation_fixed.py','scripts/presentation_fixed_floe.py','scripts/presentation_fixed_model.py','scripts/presentation_fixed_check.py')))


def run(out,geometry):
    sha=lambda data:hashlib.sha256(data).hexdigest()
    producers={name:sha((ROOT/name).read_bytes()) for name in FILES}
    domain=collect();config=json.loads((ROOT/'references/presentation-assets-config.json').read_text())
    palette_path=ROOT/config['palette'];palette=audit_palette(palette_path);geometry=Path(geometry).resolve()
    palette_inputs=sorted(p for p in palette_path.rglob('*') if p.is_file()) if palette_path.is_dir() else [palette_path]
    inputs={str(path.relative_to(ROOT)):sha(path.read_bytes()) for path in
        (ROOT/'references/roms/frostbite.bin',*palette_inputs,geometry/'geometry.json',*sorted(geometry.glob('geometry-*.bin')))}
    tables=prepare((ROOT/'references/roms/frostbite.bin').read_bytes(),palette,geometry)
    out=private_output(out);out.mkdir(parents=True,exist_ok=False);rows=[];maxima=[0,0,0];max_footer=0;max_floes=[0]*4
    for case in domain['cases']:
        try:rendered=frame(tables,case['ram'])
        except ValueError as error:
            (out/'failure.json').write_text(json.dumps({'id':case['id'],'ram':list(case['ram']),'error':str(error)},indent=2)+'\n')
            raise ValueError(f'{case["id"]}: {error}') from error
        actual=full_pixels(tables,rendered);expected=map_frame(case['raster'],palette)
        different=sum(a!=b for a,b in zip(actual,expected))
        row={key:case[key] for key in ('id','family','ram_sha256','raster_sha256')}
        row.update(dynamic_slots_used=rendered['counts'],footer_slots_used=rendered['footer_count'],different_pixels=different);rows.append(row)
        if different:
            (out/'failure.json').write_text(json.dumps(row,indent=2)+'\n')
            (out/'actual.bin').write_bytes(actual);(out/'expected.bin').write_bytes(expected)
            raise ValueError(f'{case["id"]}: fixed physical roles differ at{different} original pixels')
        maxima=[max(a,b) for a,b in zip(maxima,rendered['counts'])];max_footer=max(max_footer,rendered['footer_count'])
        max_floes=[max(a,b) for a,b in zip(max_floes,rendered.get('floe_slots_used',[0]*4))]
        if len(rows)%100==0:print(f'{len(rows)}/2115 fixed-role images: zero differences',flush=True)
    verify_files(domain['files']);verify_files(inputs)
    if any(sha((ROOT/name).read_bytes())!=value for name,value in producers.items()):raise ValueError('fixed-role proof producers changed')
    result={'complete':True,'source_sha256':domain['source_sha256'],'source_receipt_sha256':domain['source_receipt_sha256'],
        'families':domain['families'],'unmapped_startup':domain['unmapped_startup'],'cases':rows,'reserved_dynamic_slots':COUNTS,
        'max_dynamic_slots_used':maxima,'max_footer_slots_used':max_footer,'max_floe_slots_used':max_floes,'producer_files':producers,'source_files':domain['files'],
        'input_files':inputs,'different_pixels':0,'native_accepted':False,'frame_deadline_accepted':False,
        'scope':'Host fixed-slot capacity/content proof on all original observations. No native integration, frame, audio or human-ROM acceptance.'}
    (out/'check.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:result[key] for key in ('complete','max_dynamic_slots_used','max_footer_slots_used','different_pixels')}));return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--geometry',type=Path,required=True)
    run(**vars(p.parse_args()))
