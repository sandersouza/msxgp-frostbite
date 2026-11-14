"""All1280 prepared NAME rows through owner palettes and normalized literals."""
import argparse
import hashlib
import json
from pathlib import Path

from compact_grid_fast_probe import prepared_data
from compact_live_probe import CONTROL_SHA
from compact_native_fixture import run,sha
from environment import ROOT
from reference_traces import private_output


def assets(build):
    m=json.loads((build/'build.json').read_bytes());rom=(build/m['rom']['filename']).read_bytes()
    if hashlib.sha256(rom).hexdigest()!=CONTROL_SHA:raise ValueError('sealed accepted control required')
    data,inputs,expected=prepared_data(rom);rows=data['rows']
    if len(rows)!=704 or set(rows)-set(range(8))-{255}:raise ValueError('22 whole bounded normalized rows required')
    palettes=b''.join(bytes([data['bases'][owner]+i for i in range(8)]+[data['waters'][owner]]) for owner in range(8))
    return dict(directory=data['directory'],rows=rows.replace(b'\xff',b'\x08'),palettes=palettes),inputs,expected


def check(build,out,byte_increments=False):
    build=build.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    data,inputs,expected=assets(build);out.mkdir(parents=True)
    for n,b in data.items():(out/(n+'.bin')).write_bytes(b)
    source='native_grid_palette_fast.asm' if byte_increments else 'compact_grid_palette.asm'
    asm=[' ORG $4000',' DB "AB"',' DW start',' DS 12,0','start:',' DI',' LD SP,$F380','ready:',' JP ready',
         'cg_directory EQU $5000','cg_rows EQU $5100','cg_palettes EQU $5500',
         ' DS $4100-$,$FF',f' INCLUDE "{source}"',' ASSERT $ <= $5000',
         ' DS $5000-$,$FF',f' INCBIN "{out/"directory.bin"}"',' DS $5100-$,$FF',f' INCBIN "{out/"rows.bin"}"']
    for owner in range(8):
        asm += [f' DS ${0x5500+owner*256:04X}-$,$A5',' DB '+','.join(map(str,data['palettes'][owner*9:owner*9+9]))]
    asm+=[' DS $C000-$,$FF']
    result=run(out,'\n'.join(asm)+'\n',inputs,expected,input_address=0xC7F0,input_stride=2,
        output_address=0xC480,output_stride=32,entry_name='cg_build',end_name='cg_end',writes=((0xC480,0xC49F),))
    names=('scripts/native_grid_palette_fast_probe.py','src/'+source,'scripts/compact_grid_fast_probe.py','scripts/compact_grid_name_probe.py')
    for n in names:
        p=out/'source'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes())
    result.update(oracle_rom_sha256=CONTROL_SHA,old_expanded_rows_bytes=5632,normalized_row_bytes=704,palette_bytes=72,directory_bytes=160,
        sources={n:sha(ROOT/n) for n in names},files={p.name:sha(p) for p in out.iterdir() if p.is_file()},
        scope='All160 phase x8 owner rows, exact32-byte output and ABI/write guards. Palette-page holes are not read; whole-frame qualification remains required.')
    (out/'component-result.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k not in ('sources','files')})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--byte-increments',action='store_true')
    a=p.parse_args();check(a.build,a.out,a.byte_increments)
