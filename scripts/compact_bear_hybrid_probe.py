"""Prove all352 hybrid row packets with an exact in-memory stream sink."""
import argparse
import json
from pathlib import Path

from compact_bear_hybrid import pack,unpack
from compact_live_probe import CONTROL_SHA
from compact_native_fixture import run,sha
from environment import ROOT
from reference_traces import private_output


def assets(build):
    m=json.loads((build/'build.json').read_bytes());r=(build/m['rom']['filename']).read_bytes()
    import hashlib
    if hashlib.sha256(r).hexdigest()!=CONTROL_SHA:raise ValueError('sealed accepted control required')
    count=m['bear_hybrid']['program_count']
    programs=[r[(134+i//46)*16384+0x3800+(i%46)*44:(134+i//46)*16384+0x3800+(i%46)*44+44] for i in range(count)]
    data=pack(programs)
    if unpack(data)!=programs:raise ValueError('lossless packing failed')
    return data,b''.join(programs)


def check(build,out):
    build=build.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    data,expected=assets(build);out.mkdir(parents=True)
    for n,b in data.items():(out/(n+'.bin')).write_bytes(b)
    asm=[' ORG $4000',' DB "AB"',' DW start',' DS 12,0','start:',' DI',' LD SP,$F380','ready:',' JP ready',
         ' DS $4100-$,$FF','bh_entry:',' LD HL,$C7B4',' LD DE,$C500','BH_COLOR_OFFSET EQU 16',
         ' INCLUDE "compact_bear_hybrid_row.asm"',
         'vdp_write:',' LD ($C7D0),DE','vdp_stream:',' PUSH DE',' LD DE,($C7D0)',' LD C,B',' LD B,0',' LDIR',' LD ($C7D0),DE',' POP DE',' RET',
         ' ASSERT $ <= $4800',' DS $4800-$,$FF','bh_patterns:',f' INCBIN "{out/"patterns.bin"}"',
         'bh_colors:',f' INCBIN "{out/"colors.bin"}"',' ASSERT $ <= $6000',' DS $C000-$,$FF']
    result=run(out,'\n'.join(asm)+'\n',data['recipes'],expected,input_address=0xC7B4,input_stride=10,
        output_address=0xC500,output_stride=44,entry_name='bh_entry',end_name='bh_end',writes=((0xC500,0xC52B),(0xC7D0,0xC7D1)))
    names=('src/compact_bear_hybrid_row.asm','scripts/compact_bear_hybrid.py','scripts/compact_bear_hybrid_probe.py')
    for n in names:
        p=out/'source'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes())
    result.update(oracle_rom_sha256=CONTROL_SHA,prepared_program_bytes=len(expected),dictionary_bytes=sum(len(x) for x in data.values()),
        sources={n:sha(ROOT/n) for n in names},files={p.name:sha(p) for p in out.iterdir() if p.is_file()},
        scope='All352 row packets: exact four plane streams and12 physical keys, component write/ABI guards; VDP/whole-frame qualification separate.')
    (out/'component-result.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k not in ('sources','files')})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();check(a.build,a.out)
