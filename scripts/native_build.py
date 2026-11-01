"""Build the private source-derived native CPU proof cartridge, not a release."""
import hashlib
import json
from pathlib import Path
import subprocess

from environment import ROOT,verified_tool
from reference_inventory import verified_input
from native_codegen import generate,reachable

OUT=ROOT/'outputs/native'
ROM=OUT/'native-contract.rom'
BUILD_FILES=('scripts/native_codegen.py','scripts/native_build.py','src/native_cpu.asm','src/native_contract.asm',
             'scripts/environment.py','scripts/reference_inventory.py','references/manifest.json','references/tools-lock.json','references/mechanics-cases.json')


def build_contract(input_adapter=False,corrupt_port2=False,fast_phase=False,carry_fusion=False):
    source=verified_input(ROOT/'references/roms/frostbite.bin');data=(ROOT/'references/roms/frostbite.bin').read_bytes()
    from native_fast import generate_fast
    if carry_fusion and not fast_phase:raise ValueError('carry fusion requires the proved whole-phase core')
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'core.inc').write_text(generate_fast(data,carry_fusion=carry_fusion) if fast_phase else generate(data));(OUT/'data.bin').write_bytes(data[0xC00:])
    assembler=verified_tool('sjasmplus')
    r=subprocess.run([str(assembler),'--nologo',*(['-DWITH_NATIVE_INPUT'] if input_adapter else []),
        *(['-DINPUT_CORRUPT_PORT2'] if corrupt_port2 else []),f'--inc={ROOT/"src"}',f'--inc={OUT}',f'--raw={ROM}',
        *(['-DFAST_PHASE'] if fast_phase else []),
        f'--sym={OUT/"native.sym"}',f'--lst={OUT/"native.lst"}',str(ROOT/'src/native_contract.asm')],cwd=ROOT,capture_output=True,text=True,timeout=60)
    (OUT/'assembler.log').write_text(r.stdout+r.stderr)
    if r.returncode:raise ValueError('native assembler failed: '+'\n'.join((r.stdout+r.stderr).splitlines()[-12:]))
    artifact=ROM.read_bytes()
    if len(artifact)!=32768 or artifact[:2]!=b'AB' or artifact[16:20]!=b'FBN0':raise ValueError('native contract header/size invalid')
    files=BUILD_FILES+('scripts/native_fast.py','scripts/native_analysis.py')
    if input_adapter:files+=('src/native_input.asm',)
    metadata={'scope':'Private CPU proof, not an offered testable human ROM','source':source,'rom_sha256':hashlib.sha256(artifact).hexdigest(),
        'input_adapter':input_adapter,'corrupt_port2':corrupt_port2,
        'fast_phase':fast_phase,
        'carry_fusion':carry_fusion,
        'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'source_dirty':bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()),
        'source_files':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files},
        'assembler_sha256':hashlib.sha256(assembler.read_bytes()).hexdigest(),'instructions':len(reachable(data))}
    (OUT/'build.json').write_text(json.dumps(metadata,indent=2)+'\n');return metadata


if __name__=='__main__':
    print(json.dumps(build_contract(),indent=2))
