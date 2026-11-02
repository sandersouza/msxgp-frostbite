"""Host translation proof for the source P0 shoreline cache key, not native timing."""
import argparse
import hashlib
import json
from pathlib import Path

from environment import ROOT
from presentation_model import player
from presentation_source_cases import collect,verify_files,FILES as SOURCE_FILES
from reference_traces import private_output

FILES=tuple(dict.fromkeys((*SOURCE_FILES,'scripts/presentation_player_shore_check.py','scripts/presentation_model.py','src/presentation_player_cache.asm')))


def row_pixels(row,x,reflect):
    result=[]
    for dx in range(8):
        position=x+dx;bit=dx if reflect else 7-dx
        mask=row['prefix_pattern'] if position<row['update_x'] else row['pattern']
        color=row['prefix_color'] if position<row['color_update_x'] else row['color']
        if position>=row['suffix_x']:color=row['suffix_color']
        result.append((bool(mask&(1<<bit)),color if mask&(1<<bit) else None))
    return tuple(result)


def symbolic():
    cases=0
    for x in range(24,84):
        for mask in range(256):
            for reflect in (False,True):
                row={'pattern':mask,'prefix_pattern':mask^255,'color':1,'prefix_color':2,'suffix_color':3,
                     'update_x':22,'color_update_x':22,'suffix_x':91}
                expected=tuple((bool(mask&(1<<(dx if reflect else 7-dx))),1 if mask&(1<<(dx if reflect else 7-dx)) else None) for dx in range(8))
                if row_pixels(row,x,reflect)!=expected:raise ValueError('worst-bound symbolic shoreline row is not translation invariant')
                cases+=1
    return cases


def check(out):
    digest=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    producer={name:digest(ROOT/name) for name in FILES};domain=collect();rom_path=ROOT/'references/roms/frostbite.bin';rom=rom_path.read_bytes()
    samples=[case for case in domain['cases'] if 19<=case['ram'][0x64]<30];unique={}
    for case in samples:
        ram=case['ram'];key=(ram[0x64],ram[0x6B],ram[0x6C]&8,ram[0x6E],ram[0x70],int(ram[0x68]>=150))
        unique.setdefault(key,ram)
    if not unique:raise ValueError('no observed shoreline player states')
    max_prefix=0;min_suffix=256;translations=0;rows_checked=0
    for ram in unique.values():
        description=player(rom,ram);reflect=description['reflect']
        for row in description['rows']:
            prefix=max(row['update_x'],row['color_update_x']);max_prefix=max(max_prefix,prefix);min_suffix=min(min_suffix,row['suffix_x'])
            if prefix>22 or row['suffix_x']<91:raise ValueError('observed source row exceeds proven shoreline bounds')
            expected=tuple((bool(row['pattern']&(1<<(dx if reflect else 7-dx))),row['color'] if row['pattern']&(1<<(dx if reflect else 7-dx)) else None) for dx in range(8))
            for x in range(24,84):
                if row_pixels(row,x,reflect)!=expected:raise ValueError('observed source player changes local shape/color across safe shoreline X')
                rows_checked+=1
        translations+=60
    symbolic_cases=symbolic();verify_files(domain['files'])
    if any(digest(ROOT/name)!=value for name,value in producer.items()):raise ValueError('shoreline proof producers changed')
    out=private_output(out);out.mkdir(parents=True,exist_ok=False)
    report={'complete':True,'source_sha256':digest(rom_path),'source_receipt_sha256':domain['source_receipt_sha256'],'source_files':domain['files'],
        'producer_files':producer,'original_eligible_samples':len(samples),'unique_player_states':len(unique),'derived_translations':translations,
        'derived_row_checks':rows_checked,'symbolic_rows':symbolic_cases,'safe_x':[24,83],'max_prefix_observed':max_prefix,'min_suffix_observed':min_suffix,
        'frame_deadline_accepted':False,'native_accepted':False,
        'scope':'Host translation theorem only. Each source row has at most two byte-address carries before its prefix update, so the prefix is at most16+2*3=22. The earliest suffix cutoff is91 and carries only increase it. X24..83 keeps all eight source pixels outside both races; reflection and target parity remain in the exact cache key. Symbolic all256 masks/both reflections/all60 X plus independently retained original-state row descriptions. No new original raster observations, native cache publication or frame acceptance.'}
    (out/'check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('complete','original_eligible_samples','unique_player_states','derived_translations','symbolic_rows')}));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    check(**vars(p.parse_args()))
