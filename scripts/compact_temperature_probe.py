"""Prove every burst record using exact independent glyph bit planes."""
import argparse
import functools
import hashlib
import json
import operator
from pathlib import Path

from compact_live_probe import CONTROL_SHA
from compact_native_fixture import run,sha
from environment import ROOT
from reference_traces import private_output


def planes(rom):
    records=[rom[(127+i//64)*16384+0x3800+(i%64)*32: (127+i//64)*16384+0x3800+(i%64)*32+32] for i in range(256)]
    tens=[bytes(functools.reduce(operator.and_,(records[t*16+u][n] for u in range(16)),255) for n in range(32)) for t in range(16)]
    units=[bytes(functools.reduce(operator.and_,(records[t*16+u][n] for t in range(16)),255) for n in range(32)) for u in range(16)]
    if any(bytes(a|b for a,b in zip(tens[t],units[u]))!=records[t*16+u] for t in range(16) for u in range(16)):
        raise ValueError('temperature planes are not exact over all256records')
    positions=(0,3,4,5,6,7,8,9,27)
    compact=[bytes(row[n] for n in positions)+bytes(7) for row in tens]
    for t in range(16):
        for u in range(16):
            row=bytearray(units[u])
            for n,value in zip(positions,compact[t]):row[n]|=value
            if row!=records[t*16+u]:raise ValueError('sparse tens plane differs')
    return b''.join(compact),b''.join(units),b''.join(records)


def check(build,out):
    build=build.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((build/'build.json').read_bytes());rom=(build/m['rom']['filename']).read_bytes()
    if hashlib.sha256(rom).hexdigest()!=CONTROL_SHA:raise ValueError('sealed accepted control required')
    out.mkdir(parents=True);tens,units,expected=planes(rom)
    for n,b in (('tens',tens),('units',units)):(out/(n+'.bin')).write_bytes(b)
    asm=[' ORG $4000',' DB "AB"',' DW start',' DS 12,0','start:',' DI',' LD SP,$F380','ready:',' JP ready',
         'ct_tens EQU $5000','ct_units EQU $5100',' DS $4100-$,$FF','ct_entry:',' LD A,($C7B0)',
         ' INCLUDE "compact_temperature.asm"',' ASSERT $ <= $5000',' DS $5000-$,$FF',f' INCBIN "{out/"tens.bin"}"',
         f' INCBIN "{out/"units.bin"}"',' DS $C000-$,$FF']
    result=run(out,'\n'.join(asm)+'\n',bytes(range(256)),expected,input_address=0xC7B0,input_stride=1,
        output_address=0xC480,output_stride=32,entry_name='ct_entry',end_name='ct_end',writes=((0xC480,0xC49F),))
    result.update(oracle_rom_sha256=CONTROL_SHA,prepared_bytes=8192,plane_bytes=768,
        sources={n:sha(ROOT/n) for n in ('src/compact_temperature.asm','scripts/compact_temperature_probe.py')},
        files={p.name:sha(p) for p in out.iterdir() if p.is_file()})
    (out/'component-result.json').write_text(json.dumps(result,indent=2)+'\n');print(result)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();check(a.build,a.out)
