"""Independent source-to-physical-VRAM blue-floe/sea visibility regression.

Unlike whole mapped-image comparison this oracle never asks palette_map what
the two gameplay colors should be. Original source98 must stay visibly blue5;
source90 sea remains blue4. Consume actual immutable complete VDP captures.
"""
import argparse
import hashlib
import json
from pathlib import Path

from environment import ROOT
from graphics_mapping import map_x,map_y
from presentation_check import decode_target
from presentation_source_cases import collect,verify_files,FILES as SOURCE_FILES
from reference_provenance import audit_manifest
from reference_traces import private_output

FILES=tuple(dict.fromkeys((*SOURCE_FILES,'scripts/presentation_contrast_check.py','scripts/presentation_check.py')))
CAPTURE_BYTES=16392


def verify_colors(source,target):
    if len(source)!=160*210 or len(target)!=256*192:raise ValueError('complete original and actual target pixels required')
    counts={'touched_ice_source_pixels':0,'sea_source_pixels':0}
    for y in range(210):
        ty=map_y(y)
        if ty is None:continue
        for x in range(160):
            code=source[y*160+x]
            if code not in (0x90,0x98):continue
            wanted=4 if code==0x90 else 5;name='sea' if code==0x90 else 'touched-ice'
            left=ty*256+map_x(x);right=ty*256+map_x(x+1)
            if target[left:right]!=bytes([wanted])*(right-left):raise ValueError(f'{name} color/visibility differs at source({x},{y}): expected{wanted}, actual{list(target[left:right])}')
            counts['sea_source_pixels' if code==0x90 else 'touched_ice_source_pixels']+=1
    return counts


def check(matrix,out):
    sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();producer={name:sha(ROOT/name) for name in FILES}
    matrix=Path(matrix).resolve();report=json.loads(matrix.read_text())
    if (report.get('complete')is not True or report.get('cases')!=2115 or report.get('domain')!='all-source'
        or report.get('component')!='full-scene' or report.get('different_frames')!=0):raise ValueError('whole source-backed actual matrix required')
    audit_manifest(report['producer'],tuple(report['producer']['utility_fingerprints']))
    capture_path=matrix.parent/'captures.bin'
    if sha(capture_path)!=report['artifacts']['captures.bin']:raise ValueError('actual VDP capture changed')
    data=capture_path.read_bytes()
    if len(data)!=(1+2*2115)*CAPTURE_BYTES:raise ValueError('whole matrix physical capture required')
    domain=collect()
    if domain['source_receipt_sha256']!=report['source_report_sha256']:raise ValueError('original source authority differs')
    out=private_output(out);out.mkdir(parents=True,exist_ok=False);rows=[];totals={'touched_ice_source_pixels':0,'sea_source_pixels':0}
    for index,sample in enumerate(domain['cases']):
        raw=data[(index*2+2)*CAPTURE_BYTES:(index*2+3)*CAPTURE_BYTES]
        target=decode_target(raw[:16384],raw[16384:])
        try:counts=verify_colors(sample['raster'],target)
        except ValueError as error:raise ValueError(f'contrast case{index} {sample["id"]}: {error}') from error
        rows.append({'index':index,'id':sample['id'],**counts})
        for key,value in counts.items():totals[key]+=value
    if not totals['touched_ice_source_pixels'] or not totals['sea_source_pixels']:raise ValueError('both gameplay colors must actually be exercised')
    verify_files(domain['files'])
    if any(sha(ROOT/name)!=value for name,value in producer.items()) or sha(capture_path)!=report['artifacts']['captures.bin']:raise ValueError('contrast producers/captures changed')
    result={'complete':True,'cases':2115,**totals,'colors':{'sea':{'source':144,'tms':4},'touched_ice':{'source':152,'tms':5}},'rom_sha256':report['rom_sha256'],'matrix_sha256':sha(matrix),
        'captures_sha256':sha(capture_path),'producer_files':producer,'source_receipt_sha256':domain['source_receipt_sha256'],
        'rows':rows,'scope':'Independent fixed sea4/touched-ice5 semantic contrast on every actually observed source90/98 pixel against physical VDP captures. Original rasters unchanged; no source-state, cadence, listening or hardware acceptance.'}
    (out/'check.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('complete','cases',*totals)}));return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('matrix','out'):p.add_argument('--'+name,type=Path,required=True)
    check(**vars(p.parse_args()))
