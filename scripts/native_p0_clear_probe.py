"""Exact120-byte P0 clear with original SP and both IFF states preserved."""
import argparse
import json
from pathlib import Path
from compact_native_fixture import run,sha
from environment import ROOT


def check(out):
    if out.exists():raise ValueError('fresh output required')
    out.mkdir(parents=True)
    asm=''' ORG $4000
 DB "AB"
 DW start
 DS 12,0
start:
 DI
 LD SP,$F380
ready:
 JP ready
 DS $4100-$,$FF
clear_entry:
 LD A,($C7B4)
 OR A
 JR Z,.call
 EI
.call:
 CALL np_clear
 LD A,I
 LD A,0
 JP PO,.save
 INC A
.save:
 DI
 LD ($E7F8),A
 RET
 INCLUDE "native_p0_clear.asm"
clear_end:
 DS $C000-$,$FF
'''
    result=run(out,asm,bytes((0,1)),bytes(121)+bytes(120)+b'\x01',input_address=0xC7B4,input_stride=1,
               output_address=0xE780,output_stride=121,entry_name='clear_entry',end_name='clear_end',writes=((0xE780,0xE7F8),))
    result.update(sources={n:sha(ROOT/n) for n in ('scripts/native_p0_clear_probe.py','src/native_p0_clear.asm')},
                  IFF_disabled_and_enabled_preserved=True,clear_bytes=120)
    (out/'component-result.json').write_text(json.dumps(result,indent=2)+'\n');print(result)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    check(p.parse_args().out.resolve())
