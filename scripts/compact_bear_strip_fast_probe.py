"""Exact210-strip proof for specialized white-foreground bulk composition."""
import argparse
import json
from pathlib import Path

from compact_bear_strip_probe import assets
from compact_live_probe import CONTROL_SHA
from compact_native_fixture import run,sha
from environment import ROOT
from reference_traces import private_output


def check(build,out):
    build=build.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    data,expected=assets(build);out.mkdir(parents=True)
    for n,b in data.items():(out/(n+'.bin')).write_bytes(b)
    for i in range(210):
        codes=[int.from_bytes(data['codes'][i*8+c*2:i*8+c*2+2],'little') for c in range(4)]
        contexts={n>>9 for n in codes}
        if len(contexts)!=1 or not contexts<={0,1,4,5}:raise ValueError('certified common bulk context required')
    asm=[' ORG $4000',' DB "AB"',' DW start',' DS 12,0','start:',' DI',' LD SP,$F380','ready:',' JP ready',
         ' DS $4100-$,$FF','bf_entry:',' LD HL,($C7B4)',' ADD HL,HL',' ADD HL,HL',' ADD HL,HL',
         ' LD DE,bf_codes',' ADD HL,DE',' INCLUDE "compact_bear_strip_fast.asm"',
         ' ASSERT $ <= $5000',' DS $5000-$,$FF','cb_patterns:',f' INCBIN "{out/"patterns.bin"}"',
         'bf_codes:',f' INCBIN "{out/"codes.bin"}"',' ASSERT $ <= $C000',' DS $C000-$,$FF']
    result=run(out,'\n'.join(asm)+'\n',b''.join(i.to_bytes(2,'little') for i in range(210)),expected,
        input_address=0xC7B4,input_stride=2,output_address=0xC480,output_stride=64,entry_name='bf_entry',end_name='bf_end',writes=((0xC480,0xC4BF),))
    names=('src/compact_bear_strip_fast.asm','scripts/compact_bear_strip_fast_probe.py','scripts/compact_bear_strip_probe.py','scripts/compact_bear_tile_probe.py')
    for n in names:
        p=out/'source'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes())
    result.update(oracle_rom_sha256=CONTROL_SHA,old_strip_bytes=13440,recipe_bytes=1680,shared_mask_bytes=3760,
        sources={n:sha(ROOT/n) for n in names},files={p.name:sha(p) for p in out.iterdir() if p.is_file()},
        scope='Every210 exact64-byte bulk strip, four equal certified contexts, bounded output and ABI; component only.')
    (out/'component-result.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k not in ('sources','files')})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();check(a.build,a.out)
