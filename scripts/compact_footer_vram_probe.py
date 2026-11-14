"""Native188-tile VDP store/read proof in structurally unused SCREEN2 slots."""
import argparse
import hashlib
import json
from pathlib import Path

from compact_footer_vram import allocation
from compact_live_probe import CONTROL_SHA
from compact_native_fixture import run,sha
from environment import ROOT
from reference_traces import private_output


def assets(build):
    m=json.loads((build/'build.json').read_bytes());rom=(build/m['rom']['filename']).read_bytes()
    if hashlib.sha256(rom).hexdigest()!=CONTROL_SHA:raise ValueError('sealed accepted control required')
    section=m['template_assets']['sections']['footer_tiles'];b=m['template_assets']['physical_banks'][section['offset']//16384];at=b*16384+section['offset']%16384
    tiles=rom[at:at+section['size']]
    if len(tiles)!=3008:raise ValueError('all188 footer tiles required')
    rows=allocation(m['profile']['fixed_slot_counts'],m['background']['tiles_per_bank'],m['ice_atlas']['ids'],m['reference_credit']['ids'],188)
    return rows,tiles


def check(build,out):
    build=build.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    rows,tiles=assets(build);out.mkdir(parents=True)
    directory=b''.join(r['pattern'].to_bytes(2,'little') for r in rows);(out/'directory.bin').write_bytes(directory)
    (out/'allocation.json').write_text(json.dumps(rows,indent=2)+'\n')
    inputs=b''.join(bytes((i,))+tiles[i*16:i*16+16] for i in range(188))
    asm=[' ORG $4000',' DB "AB"',' DW start',' DS 12,0','start:',' DI',' LD SP,$F380','ready:',' JP ready',
         ' DS $4100-$,$FF','vp_entry:',' LD HL,$C7B5',' LD DE,$C520',' LD BC,16',' LDIR',' LD A,($C7B4)',' CALL vp_store',
         ' LD HL,$C520',' LD DE,$C521',' LD (HL),$A5',' LD BC,15',' LDIR',' LD A,($C7B4)',' JP vp_read',
         't_restore_interrupts:',' RET',' INCLUDE "compact_footer_vram.asm"',' ASSERT $ <= $5000',' DS $5000-$,$FF',
         'vp_directory:',f' INCBIN "{out/"directory.bin"}"',' DS $C000-$,$FF']
    result=run(out,'\n'.join(asm)+'\n',inputs,tiles,input_address=0xC7B4,input_stride=17,
        output_address=0xC520,output_stride=16,entry_name='vp_entry',end_name='vp_end',writes=((0xC520,0xC52F),))
    names=('scripts/compact_footer_vram.py','scripts/compact_footer_vram_probe.py','src/compact_footer_vram.asm','tests/test_compact_footer_vram.py')
    for n in names:
        p=out/'source'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes())
    result.update(oracle_rom_sha256=CONTROL_SHA,footer_bytes=3008,lookup_bytes=len(directory),whole_game_qualified=False,
        sources={n:sha(ROOT/n) for n in names},files={p.name:sha(p) for p in out.iterdir() if p.is_file()},
        scope='All188 real VDP store/read operations, exact original tiles and RAM/ABI guards. Allocation excludes both fixed generations, backgrounds, atlas, footer and credits; whole-game immutability/NAME proof remains required.')
    (out/'component-result.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k not in ('sources','files')})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();check(a.build,a.out)
