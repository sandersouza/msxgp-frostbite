"""Exact239-pattern proof for P0 shore half-pattern sharing."""
import argparse
import json
from pathlib import Path

from build_compact_packet_experiment import digest
from compact_live_probe import CONTROL_SHA
from compact_native_fixture import run,sha
from environment import ROOT
from reference_traces import private_output


def assets(rom):
    expected=b''.join(rom[b*16384+0x3800:(b+1)*16384] for b in range(123,127))[:239*32]
    halves=[];lookup={};directory=bytearray()
    for i in range(239):
        for h in range(2):
            half=expected[i*32+h*16:i*32+h*16+16]
            if half not in lookup:lookup[half]=len(halves)*16;halves.append(half)
            directory.extend(lookup[half].to_bytes(2,'little'))
    if len(halves)!=232:raise ValueError('complete shore half-pattern domain changed')
    return dict(directory=bytes(directory),halves=b''.join(halves)),expected


def check(build,out):
    build=build.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((build/'build.json').read_bytes());rom=(build/m['rom']['filename']).read_bytes()
    if digest(rom)!=CONTROL_SHA:raise ValueError('sealed accepted control required')
    data,expected=assets(rom);out.mkdir(parents=True)
    for n,b in data.items():(out/(n+'.bin')).write_bytes(b)
    asm=[' ORG $4000',' DB "AB"',' DW start',' DS 12,0','start:',' DI',' LD SP,$F380','ready:',' JP ready',
         ' DS $4100-$,$FF','sp_entry:',' LD A,($C7B4)',' INCLUDE "compact_shore_pattern.asm"',
         ' ASSERT $ <= $5000',' DS $5000-$,$FF','sp_directory:',f' INCBIN "{out/"directory.bin"}"',
         'sp_halves:',f' INCBIN "{out/"halves.bin"}"',' ASSERT $ <= $C000',' DS $C000-$,$FF']
    result=run(out,'\n'.join(asm)+'\n',bytes(range(239)),expected,input_address=0xC7B4,input_stride=1,
        output_address=0xC500,output_stride=32,entry_name='sp_entry',end_name='sp_end',writes=((0xC500,0xC51F),))
    names=('src/compact_shore_pattern.asm','scripts/compact_shore_pattern_probe.py')
    for n in names:
        p=out/'source'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes())
    result.update(oracle_rom_sha256=CONTROL_SHA,old_pattern_bytes=7648,half_bytes=3712,directory_bytes=956,
        sources={n:sha(ROOT/n) for n in names},files={p.name:sha(p) for p in out.iterdir() if p.is_file()},
        scope='Every239 exact32-byte P0 shore pattern, bounded output and ABI; component only.')
    (out/'component-result.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k not in ('sources','files')})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();check(a.build,a.out)
