"""Compare sparse typed constructors against every frozen original observation.

This host proof does not qualify native execution, frame time or a human ROM.
"""
import argparse
import hashlib
import json
from pathlib import Path

from environment import ROOT
from graphics_mapping import map_frame
from presentation_fast_model import prepare,frame,full_pixels
from presentation_palette import audit_palette
from presentation_source_cases import collect,verify_files,FILES as SOURCE_FILES
from reference_traces import private_output

FILES=tuple(dict.fromkeys((*SOURCE_FILES,'scripts/presentation_fast_model_check.py',
    'scripts/presentation_fast_model.py','scripts/presentation_constructors.py',
    'scripts/presentation_static_assets.py','scripts/presentation_fragments.py',
    'scripts/presentation_check.py','scripts/presentation_palette.py')))


def run(out,geometry):
    sha=lambda data:hashlib.sha256(data).hexdigest()
    producers={name:sha((ROOT/name).read_bytes()) for name in FILES}
    domain=collect();config=json.loads((ROOT/'references/presentation-assets-config.json').read_text())
    palette_path=ROOT/config['palette'];palette=audit_palette(palette_path)
    geometry=Path(geometry).resolve()
    palette_inputs=sorted(path for path in palette_path.rglob('*') if path.is_file()) if palette_path.is_dir() else [palette_path]
    inputs={str(path.relative_to(ROOT)):sha(path.read_bytes())
            for path in (ROOT/'references/roms/frostbite.bin',*palette_inputs,geometry/'geometry.json',*sorted(geometry.glob('geometry-*.bin')))}
    tables=prepare((ROOT/'references/roms/frostbite.bin').read_bytes(),palette,geometry)
    out=private_output(out);out.mkdir(parents=True,exist_ok=False)
    rows=[];maxima=[0,0,0]
    for case in domain['cases']:
        rendered=frame(tables,case['ram']);actual=full_pixels(tables,rendered)
        expected=map_frame(case['raster'],palette)
        mismatches=sum(a!=b for a,b in zip(actual,expected))
        row={key:case[key] for key in ('id','family','ram_sha256','raster_sha256')}
        row.update(counts=rendered['counts'],different_pixels=mismatches)
        rows.append(row)
        if mismatches:
            (out/'failure.json').write_text(json.dumps(row,indent=2)+'\n')
            (out/'actual.bin').write_bytes(actual);(out/'expected.bin').write_bytes(expected)
            raise ValueError(f'{case["id"]}: {mismatches} source pixels differ')
        maxima=[max(old,new) for old,new in zip(maxima,rendered['counts'])]
        if len(rows)%100==0:print(f'{len(rows)}/2115 zero-difference observations',flush=True)
    verify_files(domain['files'])
    verify_files(inputs)
    if any(sha((ROOT/name).read_bytes())!=value for name,value in producers.items()):
        raise ValueError('host constructor producer changed during comparison')
    result={'source_sha256':domain['source_sha256'],'source_receipt_sha256':domain['source_receipt_sha256'],
        'families':domain['families'],'unmapped_startup':domain['unmapped_startup'],
        'cases':rows,'max_distinct_keys_per_bank':maxima,'producer_files':producers,
        'source_files':domain['files'],'input_files':inputs,'different_pixels':0,'native_accepted':False,
        'frame_deadline_accepted':False,
        'scope':'Host typed-constructor proof on controlled/input-only original observations, not native gameplay, timing or human acceptance'}
    (out/'check.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:result[key] for key in ('families','max_distinct_keys_per_bank','different_pixels')}))
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True);parser.add_argument('--geometry',type=Path,required=True)
    run(**vars(parser.parse_args()))
