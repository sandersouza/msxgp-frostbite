"""Separate local all-window observer; the frozen floe backend stays intact."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from environment import ROOT
from hazard_truth import FULL_BYTES,full_record
from reference_state import decode_state
from reference_traces import private_output,run_debugger
from stella_floe import HELPERS as FLOE_HELPERS,PATCH as FLOE_PATCH,REVISION,UPSTREAM,digest
from stella_floe import fixture as floe_fixture

PATCH=ROOT/'tools/stella-hazard.patch'
HELPERS=(*FLOE_HELPERS,'scripts/stella_hazard.py','scripts/hazard_truth.py','tools/stella-hazard.patch')


def helper_identity():
    return {name:digest(ROOT/name) for name in HELPERS}


def fixture(base,player_x,y,object_x,shape,nusiz,reflection=False,bear_x=None):
    if (type(object_x) is not int or not 0<=object_x<160 or type(shape) is not int or not 0<=shape<=248
            or type(nusiz) is not int or not 0<=nusiz<=3 or type(reflection) not in (int,bool) or reflection not in (0,1)
            or bear_x is not None and (type(bear_x) is not int or not 0<=bear_x<160)):
        raise ValueError('declared original object coordinate/shape/copy/reflection required')
    result=bytearray(floe_fixture(base,player_x,y,64,(0,128)))
    result[0x54:0x58]=bytes([object_x])*4
    result[0x58:0x5C]=bytes([nusiz])*4
    result[0x23:0x27]=bytes([shape])*4
    for row in range(4):result[0x11+row]=(base[0x11+row]&127)|(128 if reflection else 0)
    if bear_x is not None:result[0x68]=bear_x
    return bytes(result)


def validate_observation(data,log,count):
    if type(count) is not int or count<1:raise ValueError('complete nonempty hazard observation required')
    if re.findall(r'^FROSTBITE_HAZARDS_COMPLETE (\d+)$',log,re.M)!=[str(count)] or len(data)!=count*FULL_BYTES:
        raise ValueError('missing/duplicate hazard marker or incomplete all-window records')
    for offset in range(0,len(data),FULL_BYTES):full_record(data[offset:offset+FULL_BYTES])
    return count


def build(directory):
    directory=private_output(directory)
    if directory.exists():raise ValueError('use a fresh immutable hazard backend directory')
    directory.parent.mkdir(parents=True,exist_ok=True)
    caches=(ROOT/'outputs/floes/observer-source',ROOT/'outputs/floes/stella-source')
    source=next((str(path) for path in caches if (path/'.git').exists()),UPSTREAM)
    subprocess.run(['git','clone',source,str(directory)],check=True,timeout=180)
    subprocess.run(['git','checkout',REVISION],cwd=directory,check=True,timeout=30)
    for patch in (FLOE_PATCH,PATCH):
        subprocess.run(['git','apply','--check',str(patch)],cwd=directory,check=True,timeout=30)
        subprocess.run(['git','apply',str(patch)],cwd=directory,check=True,timeout=30)
    commands=[['./configure','--disable-sound','--disable-joystick','--disable-png','--disable-zip',
               '--disable-cheats','--enable-debugger','--enable-release'],['make','-j4']]
    with (directory/'frostbite-build.log').open('w') as log:
        for command in commands:subprocess.run(command,cwd=directory,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=600)
    result={'upstream':UPSTREAM,'revision':REVISION,'patches':{str(p.relative_to(ROOT)):digest(p) for p in (FLOE_PATCH,PATCH)},
            'binary_sha256':digest(directory/'stella'),'helpers':helper_identity(),'commands':commands,
            'source_diff_sha256':hashlib.sha256(subprocess.check_output(['git','diff'],cwd=directory)).hexdigest(),
            'purpose':'Local all-window observation only; no original interpreter in MSX ROM','upstream_license':'GPL-2.0'}
    (directory/'frostbite-hazard-observer.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def observe(rom,binary,initial,cases,out):
    if not cases or any(len(case)!=128 for case in cases):raise ValueError('complete nonempty128-byte hazard fixtures required')
    decode_state(initial);before=helper_identity();binary_hash=digest(binary)
    out=private_output(out);out.mkdir(parents=True,exist_ok=False)
    (out/'initial.state').write_bytes(initial);(out/'cases.bin').write_bytes(b''.join(cases))
    names=('FROSTBITE_PROBE_INPUT','FROSTBITE_PROBE_OUTPUT','FROSTBITE_PROBE_ROI')
    previous={name:os.environ.get(name) for name in names}
    try:
        os.environ[names[0]]=str(out/'cases.bin');os.environ[names[1]]=str(out/'results.bin');os.environ.pop(names[2],None)
        _,backend=run_debugger(rom,'loadState 0\nhazardProbe\nexitRom\n',out/'raw',initial,stella=str(binary))
    finally:
        for name,value in previous.items():
            if value is None:os.environ.pop(name,None)
            else:os.environ[name]=value
    data=(out/'results.bin').read_bytes()
    validate_observation(data,(out/'raw/stella.log').read_text(),len(cases))
    if before!=helper_identity() or binary_hash!=digest(binary):raise ValueError('hazard observation producer changed')
    result={'schema_version':1,'mode':'complete nine-window visible phase','cases':len(cases),'backend':backend,
            'upstream_revision':REVISION,'helpers':before,
            'producer_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'producer_dirty':bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()),
            'files':{name:digest(out/name) for name in ('initial.state','cases.bin','results.bin','raw/stella.log')}}
    (out/'observation.json').write_text(json.dumps(result,indent=2)+'\n')
    return data,result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=('build',))
    parser.add_argument('--directory',type=Path,default=ROOT/'outputs/hazards/observer-source')
    args=parser.parse_args();print(json.dumps(build(args.directory),indent=2))
