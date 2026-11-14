"""Native1280-row proof for overlapped pretranslated NAME windows."""
import argparse
import hashlib
import json
from pathlib import Path

from compact_byte_windows import pack_windows,restore_windows
from compact_grid_fast_probe import prepared_data
from compact_live_probe import CONTROL_SHA
from compact_native_fixture import run,sha
from environment import ROOT
from reference_traces import private_output


def assets(build):
    m=json.loads((build/'build.json').read_bytes());rom=(build/m['rom']['filename']).read_bytes()
    if hashlib.sha256(rom).hexdigest()!=CONTROL_SHA:raise ValueError('sealed accepted control required')
    data,inputs,expected=prepared_data(rom);values=[]
    for template in range(22):
        phase=data['directory'].index(template)
        for owner in range(8):
            at=(phase*8+owner)*32;row=bytes(expected[at:at+32])
            if row[30:]!=bytes(2):raise ValueError('only the known two unused suffix bytes may be omitted')
            values.append(row[:30])
    packed=pack_windows(values)
    if restore_windows(packed)!=values:raise ValueError('NAME literal window reconstruction differs')
    if len(packed['pool'])!=4080 or len(packed['offsets'])!=352:raise ValueError('complete176-window domain required')
    return dict(directory=data['directory'],offsets=packed['offsets'],pool=packed['pool']),inputs,bytes(expected)


def check(build,out):
    build=build.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    data,inputs,expected=assets(build);out.mkdir(parents=True)
    for n,b in data.items():(out/(n+'.bin')).write_bytes(b)
    pointers=b''.join((0x5300+int.from_bytes(data['offsets'][i:i+2],'little')).to_bytes(2,'little') for i in range(0,352,2))
    (out/'pointers.bin').write_bytes(pointers)
    asm=[' ORG $4000',' DB "AB"',' DW start',' DS 12,0','start:',' DI',' LD SP,$F380','ready:',' JP ready',
         'gw_directory EQU $5000','gw_index EQU $5100',' DS $4100-$,$FF','gw_entry:',' CALL gw_lookup',' LD DE,$C480',' LD BC,30',' LDIR',
         ' XOR A',' LD (DE),A',' INC DE',' LD (DE),A',' RET',' INCLUDE "compact_grid_window.asm"',
         ' ASSERT $ <= $5000',' DS $5000-$,$FF',f' INCBIN "{out/"directory.bin"}"',' DS $5100-$,$FF',f' INCBIN "{out/"pointers.bin"}"',
         ' DS $5300-$,$FF',f' INCBIN "{out/"pool.bin"}"',' DS $C000-$,$FF']
    result=run(out,'\n'.join(asm)+'\n',inputs,expected,input_address=0xC7F0,input_stride=2,
        output_address=0xC480,output_stride=32,entry_name='gw_entry',end_name='gw_end',writes=((0xC480,0xC49F),))
    names=('scripts/compact_grid_window_probe.py','src/compact_grid_window.asm','scripts/compact_byte_windows.py','scripts/compact_grid_fast_probe.py','scripts/compact_grid_name_probe.py')
    for n in names:
        p=out/'source'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes())
    result.update(oracle_rom_sha256=CONTROL_SHA,old_expanded_rows_bytes=5632,new_window_bytes=4080,pointer_bytes=352,directory_bytes=160,reclaimed_RAM_bytes=1200,
        sources={n:sha(ROOT/n) for n in names},files={p.name:sha(p) for p in out.iterdir() if p.is_file()},
        scope='All160 phase x8 owner windows and the original complete32-byte reference output. Runtime returns a literal30-byte window for the unchanged row copier; component only.')
    (out/'component-result.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k not in ('sources','files')})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();check(a.build,a.out)
