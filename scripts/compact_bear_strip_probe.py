"""Prove every native bear bulk strip using four compact mask/context codes."""
import argparse
import json
from pathlib import Path

from build_compact_packet_experiment import digest
from compact_bear_tile_probe import assets as tile_assets
from compact_live_probe import CONTROL_SHA
from compact_native_fixture import run,sha
from environment import ROOT
from reference_traces import private_output


def assets(build):
    m=json.loads((build/'build.json').read_bytes());rom=(build/m['rom']['filename']).read_bytes()
    if digest(rom)!=CONTROL_SHA:raise ValueError('sealed accepted control required')
    tiles,_,_,codes=tile_assets(build)
    count=m['bear_native']['bulk_strips'];pool=b''.join(rom[b*16384+0x3800:(b+1)*16384] for b in range(103,112))[:count*64]
    if count!=210 or pool[:64]!=bytes([255])*64:raise ValueError('complete strip domain and white strip0 required')
    records=b''.join(rom[b*16384+0x3800:(b+1)*16384] for b in range(67,79));recipes=[None]*count
    for i in range(m['bear_native']['records']):
        record=records[i*256:(i+1)*256];columns=record[240]
        for theme in range(2):
            for row in range(3):
                slot=theme*3+row;index=int.from_bytes(record[243+slot*2:245+slot*2],'little')
                ids=[int.from_bytes(record[(row*columns+c)*20:(row*columns+c)*20+2],'little') for c in range(columns)]+[0]*(4-columns)
                context=((0,0,1),(4,4,5))[theme][row]
                recipe=b''.join(codes[(n,context)].to_bytes(2,'little') for n in ids)
                if recipes[index] is None:recipes[index]=recipe
    if any(r is None for r in recipes):raise ValueError('uncovered original strip')
    return {**tiles,'codes':b''.join(recipes)},pool


def check(build,out):
    build=build.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    data,expected=assets(build);out.mkdir(parents=True)
    for n,b in data.items():(out/(n+'.bin')).write_bytes(b)
    asm=[' ORG $4000',' DB "AB"',' DW start',' DS 12,0','start:',' DI',' LD SP,$F380','ready:',' JP ready',
         ' DS $4100-$,$FF','bs_entry:',' LD DE,($C7B4)',' INCLUDE "compact_bear_strip.asm"',
         ' ASSERT $ <= $4600',' DS $4600-$,$FF','cb_call:',' INCLUDE "compact_bear_tile.asm"',
         ' ASSERT $ <= $5000',' DS $5000-$,$FF','cb_patterns:',f' INCBIN "{out/"patterns.bin"}"',
         'cb_contexts:',f' INCBIN "{out/"contexts.bin"}"','bs_codes:',f' INCBIN "{out/"codes.bin"}"',' ASSERT $ <= $C000',' DS $C000-$,$FF']
    result=run(out,'\n'.join(asm)+'\n',b''.join(i.to_bytes(2,'little') for i in range(210)),expected,
        input_address=0xC7B4,input_stride=2,output_address=0xC480,output_stride=64,entry_name='bs_entry',end_name='bs_end',
        writes=((0xC480,0xC4BF),(0xC520,0xC537)))
    names=('src/compact_bear_strip.asm','scripts/compact_bear_strip_probe.py','src/compact_bear_tile.asm','scripts/compact_bear_tile_probe.py')
    for n in names:
        p=out/'source'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes())
    result.update(oracle_rom_sha256=CONTROL_SHA,old_strip_bytes=13440,recipe_bytes=1680,
        shared_mask_and_context_bytes=4048,sources={n:sha(ROOT/n) for n in names},files={p.name:sha(p) for p in out.iterdir() if p.is_file()},
        scope='All210 exact original64-byte PGT/CGT strips, bounded scratch and ABI; component only, not whole-frame cadence.')
    (out/'component-result.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k not in ('sources','files')})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();check(a.build,a.out)
