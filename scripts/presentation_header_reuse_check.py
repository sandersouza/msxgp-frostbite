"""Directed renderer-only blank, header identity and palette transitions."""
import argparse,hashlib,json
from pathlib import Path
from environment import ROOT
import presentation_matrix_check as matrix
from presentation_model import describe,pixels
from presentation_prepared_check import check

def exercise(build,out):
    original=(ROOT/'references/roms/frostbite.bin').read_bytes()
    bundle=matrix.collect_source();base=bytearray(bundle['cases'][228]['ram'])
    base[0x3f]&=127;base[0x6b]=base[0x70]=0
    cases=[]
    def add(name,ram):
        sample=dict(name=name,ram=list(ram),family='directed-header-palette')
        sample['raster']=pixels(original,describe(original,sample));cases.append(sample)
    # Three repeats visit both physical pages and then the previous page again.
    variants=[]
    for blank in (False,True,False,True,False):
        r=bytearray(base);r[0x3f]=(r[0x3f]&127)|(128 if blank else 0)
        variants.append(('blank-'+str(blank),r))
    for address,value in ((0x48,0x12),(0x49,0x34),(0x4a,0x56),(0x65,0x21),
                          (0x4c,2),(0x4b,19),(0x4b,20),(0x4b,19),(0x47,1),
                          (0x6b,6),(0x6b,0),(0x70,7),(0x70,0)):
        base[address]=value;variants.append((f'field-{address:02x}-{value}',bytearray(base)))
    for index,(name,r) in enumerate(variants):
        for repeat in range(3):add(f'{index}-{name}-{repeat}',r)
    raw=b''.join(bytes(c['ram']) for c in cases)
    synthetic={**bundle,'cases':cases,'families':{'directed-header-palette':len(cases)},
        'source_receipt_sha256':hashlib.sha256(raw).hexdigest(),'unmapped_startup':0}
    collect=matrix.collect_source;matrix.collect_source=lambda:synthetic
    try:result=check(build,out,len(cases))
    finally:matrix.collect_source=collect
    result['domain']='Synthetic renderer transitions derived from original source case228; not gameplay timing.'
    result['directed_cases_sha256']=hashlib.sha256(raw).hexdigest()
    result['directed_producer_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (out/'check.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();exercise(a.build.resolve(),a.out.resolve())
