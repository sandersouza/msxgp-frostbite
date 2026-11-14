"""Prove shared literal mask windows for all tiles and bulk strips."""
import argparse
import json
from pathlib import Path

from compact_bear_tile_probe import assets as tile_assets
from compact_bear_strip_probe import assets as strip_assets
from compact_byte_windows import pack_windows,restore_windows,bear_lookup,strip_lookup
from compact_live_probe import CONTROL_SHA
from compact_native_fixture import run,sha
from environment import ROOT
from reference_traces import private_output


def check(build,out,mode):
    build=build.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    if mode=='tile':
        data,inputs,expected,_=tile_assets(build);code=bear_lookup((ROOT/'src/compact_bear_tile_fast.asm').read_text())
        data['bases']=b''.join(data['contexts'][i*32:i*32+16] for i in range(9))
        entry=['cb_entry:',' LD DE,($C7B4)'];end='cb_end';name='cb_entry';address=0xC520;size=16;writes=((0xC520,0xC52F),)
    else:
        data,expected=strip_assets(build);code=strip_lookup((ROOT/'src/compact_bear_strip_fast.asm').read_text())
        inputs=b''.join(i.to_bytes(2,'little') for i in range(210))
        entry=['bf_entry:',' LD HL,($C7B4)',' ADD HL,HL',' ADD HL,HL',' ADD HL,HL',' LD DE,bf_codes',' ADD HL,DE']
        end='bf_end';name='bf_entry';address=0xC480;size=64;writes=((0xC480,0xC4BF),)
    patterns=data['patterns'];values=[patterns[i:i+8] for i in range(0,len(patterns),8)];packed=pack_windows(values)
    if restore_windows(packed)!=values:raise ValueError('literal window reconstruction failed')
    data['directory']=packed['offsets'];data['pool']=packed['pool'];out.mkdir(parents=True)
    for n,b in data.items():(out/(n+'.bin')).write_bytes(b)
    asm=[' ORG $4000',' DB "AB"',' DW start',' DS 12,0','start:',' DI',' LD SP,$F380','ready:',' JP ready',
         ' DS $4100-$,$FF',*entry,code,' ASSERT $ <= $5000',' DS $5000-$,$FF',
         'cw_directory:',f' INCBIN "{out/"directory.bin"}"','cw_pool:',f' INCBIN "{out/"pool.bin"}"']
    for key,label in (('bases','cb_bases'),('codes','bf_codes')):
        if key in data:asm+=[label+':',f' INCBIN "{out/(key+".bin")}"']
    asm+=[' ASSERT $ <= $C000',' DS $C000-$,$FF']
    result=run(out,'\n'.join(asm)+'\n',inputs,expected,input_address=0xC7B4,input_stride=2,
        output_address=address,output_stride=size,entry_name=name,end_name=end,writes=writes)
    names=('scripts/compact_bear_windows_probe.py','scripts/compact_byte_windows.py','src/compact_bear_tile_fast.asm','src/compact_bear_strip_fast.asm','scripts/compact_bear_tile_probe.py','scripts/compact_bear_strip_probe.py')
    for n in names:
        p=out/'source'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes())
    result.update(mode=mode,oracle_rom_sha256=CONTROL_SHA,old_literal_bytes=len(patterns),new_pool_bytes=len(packed['pool']),directory_bytes=len(packed['offsets']),
        sources={n:sha(ROOT/n) for n in names},files={p.name:sha(p) for p in out.iterdir() if p.is_file()},
        scope='Literal-window native lookups with all original prepared tile/strip outputs, ABI and bounded writes; component only.')
    (out/'component-result.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k not in ('sources','files')})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--mode',choices=('tile','strip'),required=True)
    a=p.parse_args();check(a.build,a.out,a.mode)
