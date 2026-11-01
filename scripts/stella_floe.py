"""Pinned, local-only original-TIA observation backend; never linked into MSX ROMs.

The patch adds 228 literal-player-view sidecars. Original CPU, TIA counters,
ROM, real collision latches and execution ordering remain authoritative.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from environment import ROOT
from floe_truth import FULL_BYTES, ROI_BYTES, full_record, roi_record
from reference_state import decode_state
from reference_traces import private_output, run_debugger

UPSTREAM='https://github.com/stella-emu/stella.git'
REVISION='d55b1aec0d067a4c901a6dcdf81cb8f579685659'
PATCH=ROOT/'tools/stella-floe.patch'
HELPERS=('scripts/stella_floe.py','scripts/floe_truth.py','scripts/reference_traces.py',
         'scripts/reference_state.py','scripts/reference_inventory.py','scripts/environment.py',
         'tools/stella-floe.patch','references/manifest.json')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def helper_identity():
    return {name:digest(ROOT/name) for name in HELPERS}


def build(directory):
    directory=private_output(directory)
    if not directory.exists():
        subprocess.run(['git','clone',UPSTREAM,str(directory)],check=True,timeout=180)
        subprocess.run(['git','checkout',REVISION],cwd=directory,check=True,timeout=30)
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=directory,text=True).strip()
    if revision!=REVISION:raise ValueError('pinned Stella source revision required')
    actual=subprocess.check_output(['git','diff'],cwd=directory)
    patch=PATCH.read_bytes()
    if not actual:
        subprocess.run(['git','apply','--check',str(PATCH)],cwd=directory,check=True,timeout=30)
        subprocess.run(['git','apply',str(PATCH)],cwd=directory,check=True,timeout=30)
    elif actual!=patch:raise ValueError('existing Stella edits differ from the owned observation patch')
    commands=[['./configure','--disable-sound','--disable-joystick','--disable-png','--disable-zip',
               '--disable-cheats','--enable-debugger','--enable-release'],['make','-j4']]
    with (directory/'frostbite-build.log').open('w') as log:
        for command in commands:subprocess.run(command,cwd=directory,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=600)
    binary=directory/'stella'
    metadata={'upstream':UPSTREAM,'revision':REVISION,'patch_sha256':digest(PATCH),
              'binary_sha256':digest(binary),'helpers':helper_identity(),'commands':commands,
              'purpose':'Local electrical observation only; no Atari CPU/TIA interpreter in the MSX cartridge',
              'upstream_license':'GPL-2.0; see upstream License.txt'}
    (directory/'frostbite-observer.json').write_text(json.dumps(metadata,indent=2)+'\n')
    return metadata


def control_pairs(rom):
    if len(rom)!=4096:raise ValueError('complete4096-byte original required')
    return sorted({(0,0)}|{((value<<4)&255,value&240) for value in rom[0xDE0:0xDF0]})


def fixture(base,player_x,y,floe_x,control):
    if len(base)!=128 or type(player_x) is not int or not 0<=player_x<160 or type(y) is not int or not 0<=y<256 or type(floe_x) is not int or not 0<=floe_x<160:
        raise ValueError('complete RAM and declared horizontal/vertical domain required')
    if len(control)!=2 or any(type(v) is not int or v&15 or not 0<=v<=255 for v in control):
        raise ValueError('two NUSIZ high-nibble control bytes required')
    result=bytearray(base)
    values={0xC5:0,0xCB:0,0xCD:255,0xBF:0,0xE4:y,0xE6:player_x,0xEE:0,0xEB:0,0xEC:0,
            0x9C:control[0],0x9D:control[1],**{0x9F+i:floe_x for i in range(4)}}
    for address,value in values.items():result[address-128]=value
    return bytes(result)


def validate_observation(data,log,count,roi):
    if type(count) is not int or count<1:raise ValueError('nonempty complete observation required')
    markers=re.findall(r'^FROSTBITE_PROBE_COMPLETE (\d+)$',log,re.M)
    size=ROI_BYTES if roi else FULL_BYTES
    if markers!=[str(count)] or len(data)!=count*size:
        raise ValueError('missing/duplicate completion marker or partial observation data')
    parser=roi_record if roi else full_record
    for offset in range(0,len(data),size):parser(data[offset:offset+size])
    return count


def observe(rom,binary,initial,cases,out,roi=False):
    if not cases or any(len(case)!=128 for case in cases):raise ValueError('complete nonempty RAM fixtures required')
    before=helper_identity();binary_hash=digest(binary);decode_state(initial)
    out=private_output(out);out.mkdir(parents=True,exist_ok=False)
    (out/'initial.state').write_bytes(initial);(out/'cases.bin').write_bytes(b''.join(cases))
    names=('FROSTBITE_PROBE_INPUT','FROSTBITE_PROBE_OUTPUT','FROSTBITE_PROBE_ROI')
    previous={name:os.environ.get(name) for name in names}
    try:
        os.environ[names[0]]=str(out/'cases.bin');os.environ[names[1]]=str(out/'results.bin')
        if roi:os.environ[names[2]]='1'
        else:os.environ.pop(names[2],None)
        _,backend=run_debugger(rom,'loadState 0\nfloeProbe\nexitRom\n',out/'raw',initial,stella=str(binary))
    finally:
        for name,value in previous.items():
            if value is None:os.environ.pop(name,None)
            else:os.environ[name]=value
    data=(out/'results.bin').read_bytes();log=(out/'raw/stella.log').read_text()
    validate_observation(data,log,len(cases),roi)
    if before!=helper_identity() or binary_hash!=digest(binary):raise ValueError('observation producer changed during capture')
    result={'schema_version':1,'mode':'top-floe ROI' if roi else 'complete visible phase','cases':len(cases),
            'backend':backend,'upstream_revision':REVISION,'helpers':before,
            'files':{name:digest(out/name) for name in ('initial.state','cases.bin','results.bin','raw/stella.log')}}
    (out/'observation.json').write_text(json.dumps(result,indent=2)+'\n')
    return data,result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=('build',))
    parser.add_argument('--directory',type=Path,default=ROOT/'outputs/floes/observer-source')
    args=parser.parse_args();print(json.dumps(build(args.directory),indent=2))
