"""Native all-state lookup proof for the compact enemy occupancy matrix."""
import argparse
import hashlib
import json
from pathlib import Path

from compact_enemy_occupancy import pack,unpack
from compact_live_probe import CONTROL_SHA
from compact_native_fixture import run,sha
from environment import ROOT
from reference_traces import private_output


def assets(build):
    m=json.loads((build/'build.json').read_bytes());r=(build/m['rom']['filename']).read_bytes()
    if hashlib.sha256(r).hexdigest()!=CONTROL_SHA:raise ValueError('sealed accepted control required')
    n=m['world_transactions']['occupancy_bytes']
    if n!=8448:raise ValueError('complete legacy occupancy domain required')
    data=b''.join(r[b*16384+0x3800:(b+1)*16384] for b in range(142,147))[:n]
    result=pack(data)
    if unpack(result)!=data:raise ValueError('occupancy factorization differs')
    return result,data


def check(build,out):
    build=build.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    data,expected=assets(build);out.mkdir(parents=True)
    for n,b in data.items():(out/(n+'.bin')).write_bytes(b)
    asm=[' ORG $4000',' DB "AB"',' DW start',' DS 12,0','start:',' DI',' LD SP,$F380','ready:',' JP ready',
         ' DS $4100-$,$FF','co_entry:',' LD BC,($C7B4)',' CALL co_lookup',' LD A,B',' LD ($C500),A',' RET',
         ' INCLUDE "compact_enemy_occupancy.asm"',' ASSERT $ <= $5000',' DS $5000-$,$FF',
         'co_directory:',f' INCBIN "{out/"directory.bin"}"','co_rows:',f' INCBIN "{out/"rows.bin"}"',' DS $C000-$,$FF']
    inputs=b''.join(bytes((variant,group)) for group in range(66) for variant in range(128))
    result=run(out,'\n'.join(asm)+'\n',inputs,expected,input_address=0xC7B4,input_stride=2,
        output_address=0xC500,output_stride=1,entry_name='co_entry',end_name='co_end',writes=((0xC500,0xC500),))
    names=('scripts/compact_enemy_occupancy.py','scripts/compact_enemy_occupancy_probe.py','src/compact_enemy_occupancy.asm')
    for n in names:
        p=out/'source'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes())
    result.update(oracle_rom_sha256=CONTROL_SHA,old_matrix_bytes=len(expected),new_dictionary_bytes=sum(map(len,data.values())),
        sources={n:sha(ROOT/n) for n in names},files={p.name:sha(p) for p in out.iterdir() if p.is_file()},
        scope='All8448 original group/phaseX/phaseY results, exact descriptor byte and ABI/write guard; component only.')
    (out/'component-result.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k not in ('sources','files')})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();check(a.build,a.out)
