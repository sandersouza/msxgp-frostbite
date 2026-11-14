"""Qualify the specialized nine-context bear compositor against all4230 tiles."""
import argparse
import json
from pathlib import Path

from compact_bear_tile_probe import assets
from compact_live_probe import CONTROL_SHA
from compact_native_fixture import run,sha
from environment import ROOT
from reference_traces import private_output


def check(build,out):
    build=build.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    data,inputs,expected,codes=assets(build);out.mkdir(parents=True)
    data['bases']=b''.join(data['contexts'][i*32:i*32+16] for i in range(9))
    for n,b in data.items():(out/(n+'.bin')).write_bytes(b)
    asm=[' ORG $4000',' DB "AB"',' DW start',' DS 12,0','start:',' DI',' LD SP,$F380','ready:',' JP ready',
         ' DS $4100-$,$FF','cb_entry:',' LD DE,($C7B4)',' INCLUDE "compact_bear_tile_fast.asm"',
         ' ASSERT $ <= $5000',' DS $5000-$,$FF','cb_patterns:',f' INCBIN "{out/"patterns.bin"}"',
         'cb_bases:',f' INCBIN "{out/"bases.bin"}"',' ASSERT $ <= $6000',' DS $C000-$,$FF']
    result=run(out,'\n'.join(asm)+'\n',inputs,expected,input_address=0xC7B4,input_stride=2,
        output_address=0xC520,output_stride=16,entry_name='cb_entry',end_name='cb_end',writes=((0xC520,0xC52F),))
    names=('src/compact_bear_tile_fast.asm','scripts/compact_bear_tile_fast_probe.py','scripts/compact_bear_tile_probe.py')
    for n in names:
        p=out/'source'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes())
    result.update(oracle_rom_sha256=CONTROL_SHA,mask_bytes=3760,context_bytes=144,
        sources={n:sha(ROOT/n) for n in names},files={p.name:sha(p) for p in out.iterdir() if p.is_file()},
        scope='All470 masks x9 contexts, exact16-byte tile and bounded original output/ABI. Component only; whole-frame proof required.')
    (out/'component-result.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k not in ('sources','files')})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();check(a.build,a.out)
