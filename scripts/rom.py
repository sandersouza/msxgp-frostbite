#!/usr/bin/env python3
"""Build/validate/run the original-free 16 KiB MSX1 diagnostic cartridge."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from environment import ROOT, verified_tool

VERSION='0.0.1-diagnostic'
OUT=ROOT/'outputs/diagnostic'
ROM=OUT/f'frostbite-{VERSION}.rom'


def validate_rom(data):
    problems=[]
    if len(data)!=16384:
        problems.append('size must be exactly 16384 bytes (plain16KiB cartridge)')
    if data[:2]!=b'AB':
        problems.append('missing MSX AB header')
    if len(data)<16 or not 0x4010<=int.from_bytes(data[2:4],'little')<0x8000:
        problems.append('initialization entry must be in cartridge body4000-7FFF')
    if len(data)>=16 and any(data[4:16]):
        problems.append('diagnostic header reserved vectors must be zero')
    if b'FROSTBITE MSX1' not in data or b'DIAGNOSTIC' not in data:
        problems.append('not the identified Frostbite diagnostic')
    return problems


def build():
    assembler=verified_tool('sjasmplus')
    OUT.mkdir(parents=True,exist_ok=True)
    command=[str(assembler),'--nologo',f'--raw={ROM}',f'--lst={OUT/"diagnostic.lst"}',
             f'--sym={OUT/"diagnostic.sym"}',str(ROOT/'src/diagnostic.asm')]
    subprocess.run(command,cwd=ROOT,check=True,timeout=60)
    data=ROM.read_bytes()
    problems=validate_rom(data)
    if problems:
        raise ValueError('; '.join(problems))
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    report={'version':VERSION,'diagnostic':True,'source_commit':commit,'source_dirty':dirty,
            'rom':{'filename':ROM.name,'size':len(data),'sha256':hashlib.sha256(data).hexdigest(),
                   'mapper':'Normal/plain16KiB','load_address':'4000','initialization_address':f'{int.from_bytes(data[2:4],"little"):04X}'},
            'target':{'machine':'MSX1','ram_kib':64,'vram_kib':16,'vdp':'TMS9918-family','expansions':False},
            'assembler':{'path':str(assembler),'sha256':hashlib.sha256(assembler.read_bytes()).hexdigest()},
            'source_files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in (ROOT/'src/diagnostic.asm',Path(__file__),ROOT/'references/tools-lock.json')},
            'acceptance':'Diagnostic only; no Frostbite mechanics, timing or physical hardware acceptance.'}
    (OUT/'build.json').write_text(json.dumps(report,indent=2)+'\n')
    (OUT/'SHA256SUMS').write_text(f'{report["rom"]["sha256"]}  {ROM.name}\n')
    print(f'Built {VERSION}: {len(data)} bytes, SHA-256 {report["rom"]["sha256"]}')
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['build','check','run'])
    parser.add_argument('--rom',type=Path,default=ROM)
    args=parser.parse_args(argv)
    try:
        if args.command=='build':
            build()
        else:
            problems=validate_rom(args.rom.read_bytes())
            if problems:
                raise ValueError('; '.join(problems))
            if args.command=='run':
                subprocess.run(['openmsx','-machine','C-BIOS_MSX1','-cart',str(args.rom.resolve()),'-romtype','Normal'],check=True)
            else:
                print(f'Validated16KiB diagnostic: {args.rom}')
        return 0
    except (OSError,ValueError,subprocess.SubprocessError) as error:
        print(f'ROM operation failed: {error}',file=sys.stderr)
        return 1


if __name__=='__main__':
    sys.exit(main())
