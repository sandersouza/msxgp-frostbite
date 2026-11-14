"""Qualify470 literal masks against every certified prepared bear context."""
import argparse
import json
from pathlib import Path

from build_compact_packet_experiment import digest
from build_bear_native import CONTEXTS
from compact_live_probe import CONTROL_SHA
from compact_native_fixture import run,sha
from environment import ROOT
from presentation_bear_native import raw_pattern
from presentation_fast_model import prepare
from presentation_palette import audit_palette
from presentation_shared_ownership import constructor
from reference_traces import private_output
from render_build import symbols


def assets(build):
    m=json.loads((build/'build.json').read_bytes());rom=(build/m['rom']['filename']).read_bytes();s=symbols(build/'presentation.sym')
    if digest(rom)!=CONTROL_SHA:raise ValueError('sealed accepted control required')
    records=b''.join(rom[b*16384+0x3800:(b+1)*16384] for b in range(67,79));ids=set()
    for i in range(m['bear_native']['records']):
        row=records[i*256:(i+1)*256]
        for n in range(row[240]*row[241]):ids.add(int.from_bytes(row[n*20:n*20+2],'little'))
    ids=sorted(ids)
    if len(ids)!=470:raise ValueError('complete470-mask domain required')
    patterns=b''.join(raw_pattern(rom,m['template_assets']['physical_banks'],s['p_template_pattern_halves_offset'],n,s['p_template_pattern_count']) for n in ids)
    original=(ROOT/'references/roms/frostbite.bin').read_bytes();config=json.loads((ROOT/'references/presentation-assets-config.json').read_bytes())
    tables=prepare(original,audit_palette(ROOT/config['palette']),build/'geometry');contexts=bytearray()
    for bank,bg,clip,color in CONTEXTS:
        at=(bg-128)*8;tile=tables['background']['patterns'][bank][at:at+8]+tables['background']['colors'][bank][at:at+8]
        water=tile==bytes([255])*8+bytes([68])*8
        contexts.extend(tile+bytes((15 if clip else 255,color,int(water)))+bytes(13))
    tile=constructor(build);pool=b''.join(rom[b*16384+0x3800:(b+1)*16384] for b in range(79,102))[:2860*16]
    lookup={pool[i:i+16]:i//16 for i in range(0,len(pool),16)};inputs=bytearray();expected=bytearray();codes={}
    for dense,n in enumerate(ids):
        for context,(bank,bg,clip,color) in enumerate(CONTEXTS):
            result=tile(bank,n.to_bytes(2,'little')+bytes((bg,clip,color,0)))
            index=lookup[result];code=dense|(context<<9);codes[(n,context)]=code
            inputs.extend(code.to_bytes(2,'little'));expected.extend(pool[index*16:index*16+16])
    return dict(patterns=patterns,contexts=bytes(contexts)),bytes(inputs),bytes(expected),codes


def check(build,out):
    build=build.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    data,inputs,expected,codes=assets(build);out.mkdir(parents=True)
    for n,b in data.items():(out/(n+'.bin')).write_bytes(b)
    asm=[' ORG $4000',' DB "AB"',' DW start',' DS 12,0','start:',' DI',' LD SP,$F380','ready:',' JP ready',
         ' DS $4100-$,$FF','cb_entry:',' LD DE,($C7B4)',' INCLUDE "compact_bear_tile.asm"',
         ' ASSERT $ <= $5000',' DS $5000-$,$FF','cb_patterns:',f' INCBIN "{out/"patterns.bin"}"',
         'cb_contexts:',f' INCBIN "{out/"contexts.bin"}"',' ASSERT $ <= $6000',' DS $C000-$,$FF']
    result=run(out,'\n'.join(asm)+'\n',inputs,expected,input_address=0xC7B4,input_stride=2,
        output_address=0xC520,output_stride=16,entry_name='cb_entry',end_name='cb_end',writes=((0xC520,0xC537),))
    names=('src/compact_bear_tile.asm','scripts/compact_bear_tile_probe.py')
    for n in names:
        p=out/'source'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes())
    result.update(oracle_rom_sha256=CONTROL_SHA,prepared_tile_bytes=45760,mask_bytes=3760,context_bytes=288,
        sources={n:sha(ROOT/n) for n in names},files={p.name:sha(p) for p in out.iterdir() if p.is_file()},
        scope='All470 raw masks x9 certified contexts, exact16-byte PGT/CGT and ABI/write guards; component only.')
    (out/'component-result.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k not in ('sources','files')})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();check(a.build,a.out)
