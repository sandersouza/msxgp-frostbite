"""Reconstruct all prepared grid NAME rows with owner-specific tile IDs."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from compact_live_probe import CONTROL_SHA
from compact_native_fixture import run,sha
from environment import ROOT
from reference_traces import private_output


def prepared_data(rom):
    from compact_grid_name_probe import prepared_data as packed_data
    assets,inputs,expected=packed_data(rom)
    packed=assets['rows'];rows=bytearray()
    for at in range(0,len(packed),15):
        row=[]
        for value in packed[at:at+15]:row.extend((value>>4,value&15))
        rows.extend(255 if value==8 else value for value in row)
        rows.extend(bytes(2))
    assets['rows']=bytes(rows)
    return assets,inputs,expected


def check(build,out):
    build=Path(build).resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    metadata=(build/'build.json').read_bytes();m=json.loads(metadata);rompath=build/m['rom']['filename'];rom=rompath.read_bytes()
    if sha(rompath)!=CONTROL_SHA:raise ValueError('sealed v30 required')
    if any(sha(ROOT/n)!=h for n,h in m['source_files'].items()):raise ValueError('baseline source differs')
    names=('scripts/compact_native_fixture.py','scripts/compact_grid_fast_probe.py','src/compact_grid_fast.asm','scripts/compact_grid_name_probe.py')
    source={n:sha(ROOT/n) if (ROOT/n).exists() else None for n in names};out.mkdir(parents=True)
    for n in names:
        if (ROOT/n).exists():
            p=out/'source'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes())
    assets,inputs,expected=prepared_data(rom)
    for n,b in assets.items():(out/(n+'.bin')).write_bytes(b)
    asm=[' ORG $4000',' DB "AB"',' DW start',' DS 12,0','start:',' DI',' LD SP,$F380','ready:',' JP ready',
         'cg_rows EQU $5000','cg_directory EQU $5400','cg_bases EQU $5500','cg_waters EQU $5510',
         ' DS $4100-$,$FF',' INCLUDE "compact_grid_fast.asm"',' ASSERT $ <= $5000']
    for n,address in (('rows',0x5000),('directory',0x5400),('bases',0x5500),('waters',0x5510)):
        asm += [f' DS ${address:04X}-$,$FF',f' INCBIN "{out/(n+".bin")}"']
    asm.append(' DS $C000-$,$FF')
    result=run(out,'\n'.join(asm)+'\n',inputs,expected,input_address=0xC7F0,input_stride=2,
        output_address=0xC200,output_stride=32,entry_name='cg_build',end_name='cg_end',writes=((0xC200,0xC21F),(0xC7F2,0xC7F3)))
    if source!={n:sha(ROOT/n) for n in names}:raise ValueError('source changed')
    if (build/'build.json').read_bytes()!=metadata or sha(rompath)!=CONTROL_SHA:raise ValueError('control changed')
    if any(sha(ROOT/n)!=h for n,h in m['source_files'].items()):raise ValueError('baseline changed')
    result.update(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        sources=source,oracle_rom_sha256=CONTROL_SHA,complete_prepared_domain=True,normalized_data_bytes=864,
        owner_table_bytes=16,replaced_prepared_bytes=40960,scratch_bytes=0,output_buffer_bytes=32,
        files={p.name:sha(p) for p in out.iterdir() if p.is_file()},
        scope='All160phase x8page/lane owner rows, all32bytes; unlinked constructor, no integration allocation or cadence claim.')
    (out/'component-result.json').write_text(json.dumps(result,indent=2)+'\n');print(result);return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();check(a.build,a.out)
