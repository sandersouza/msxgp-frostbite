"""Prove132 generated enemy SGTs against the exact accepted literal atlas."""
import argparse
import hashlib
import json
from pathlib import Path

from compact_live_probe import CONTROL_SHA
from compact_native_fixture import run,sha
from environment import ROOT
from reference_traces import private_output
from render_build import symbols


def assets(build):
    m=json.loads((build/'build.json').read_bytes());rom=(build/m['rom']['filename']).read_bytes();s=symbols(build/'presentation.sym')
    if hashlib.sha256(rom).hexdigest()!=CONTROL_SHA:raise ValueError('sealed accepted control required')
    def read(bank,address,size):return rom[bank*16384+address%16384:bank*16384+address%16384+size]
    mapping=read(1,s['p_geo_row_map_data'],256);roots={value:offset for offset,value in enumerate(mapping) if value<33}
    if set(roots)!=set(range(33)):raise ValueError('complete33-shape aliases required')
    data=dict(glyphs=read(2,s['original_data']+256,256),expansion=read(2,s['p_sprite_expansion_data'],1024),reverse=read(2,s['p_sprite_reverse_data'],256),shapes=bytes(roots[i] for i in range(33)))
    expected=read(255,0x9400,132*32)
    return data,expected


def check(build,out):
    build=build.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    data,expected=assets(build);out.mkdir(parents=True)
    for n,b in data.items():(out/(n+'.bin')).write_bytes(b)
    asm=[' ORG $4000',' DB "AB"',' DW start',' DS 12,0','start:',' DI',' LD SP,$F380','ready:',' JP ready',
         'sx_glyphs EQU $5000','sx_shapes EQU $5200','sx_expansion EQU $5500','sx_reverse EQU $5900',
         ' DS $4100-$,$FF','sx_entry:',' LD A,($C7B4)',' INCLUDE "compact_enemy_sgt.asm"',' ASSERT $ <= $5000']
    for n,address in (('glyphs',0x5000),('shapes',0x5200),('expansion',0x5500),('reverse',0x5900)):
        asm += [f' DS ${address:04X}-$,$FF',f' INCBIN "{out/(n+".bin")}"']
    asm+=[' DS $C000-$,$FF']
    result=run(out,'\n'.join(asm)+'\n',bytes(range(132)),expected,input_address=0xC7B4,input_stride=1,
        output_address=0xC500,output_stride=32,entry_name='sx_entry',end_name='sx_end',writes=((0xC500,0xC51F),))
    names=('src/compact_enemy_sgt.asm','scripts/compact_enemy_sgt_probe.py')
    for n in names:
        p=out/'source'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes())
    result.update(oracle_rom_sha256=CONTROL_SHA,old_literal_atlas_bytes=4224,new_shape_bytes=33,other_data_already_shared=True,
        sources={n:sha(ROOT/n) for n in names},files={p.name:sha(p) for p in out.iterdir() if p.is_file()},
        scope='All33 shapes x2 reflections x2 source parity, exact32-byte SGT and bounded original output/ABI. Whole-game timing remains required.')
    (out/'component-result.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k not in ('sources','files')})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();check(a.build,a.out)
