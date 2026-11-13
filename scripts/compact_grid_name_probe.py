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
    if hashlib.sha256(rom).hexdigest()!=CONTROL_SHA:raise ValueError('sealed v30 required')
    def read(bank,address,count):
        at=bank*16384+address-0x8000;return rom[at:at+count]
    pool=[];directory=bytearray();inputs=bytearray();expected=bytearray()
    bases=bytes((25,9,35,19,89,73,99,83));waters=bytes((129,129,130,130)*2)
    for phase in range(160):
        normalized=[]
        for owner in range(8):
            raw=read(45+2*(phase//16)+(phase%16)//8,0xB800+((phase%8)*8+owner)*32,32)
            if raw[30:]!=bytes(2):raise ValueError('prepared trailer differs')
            row=bytes(v-bases[owner] if bases[owner]<=v<bases[owner]+8 else 8 if v==waters[owner] else 255 for v in raw[:30])
            if max(row)>8:raise ValueError('unexpected tile outside compact alphabet')
            normalized.append(row);inputs.extend((phase,owner));expected.extend(raw)
        if len(set(normalized))!=1:raise ValueError('owner geometry differs')
        row=normalized[0];packed=bytes(a*16+b for a,b in zip(row[::2],row[1::2]))
        if packed not in pool:pool.append(packed)
        directory.append(pool.index(packed))
    if len(pool)!=22:raise ValueError('template count differs')
    return dict(rows=b''.join(pool),directory=directory,bases=bases,waters=waters),inputs,expected


def check(build,out):
    build=Path(build).resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    metadata=(build/'build.json').read_bytes();m=json.loads(metadata);rompath=build/m['rom']['filename'];rom=rompath.read_bytes()
    if sha(rompath)!=CONTROL_SHA:raise ValueError('sealed v30 required')
    if any(sha(ROOT/n)!=h for n,h in m['source_files'].items()):raise ValueError('baseline source differs')
    names=('scripts/compact_native_fixture.py','scripts/compact_grid_name_probe.py','src/compact_grid_name.asm')
    source={n:sha(ROOT/n) if (ROOT/n).exists() else None for n in names};out.mkdir(parents=True)
    for n in names:
        if (ROOT/n).exists():
            p=out/'source'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes())
    assets,inputs,expected=prepared_data(rom)
    for n,b in assets.items():(out/(n+'.bin')).write_bytes(b)
    asm=[' ORG $4000',' DB "AB"',' DW start',' DS 12,0','start:',' DI',' LD SP,$F380','ready:',' JP ready',
         'cg_rows EQU $5000','cg_directory EQU $5200','cg_bases EQU $5300','cg_waters EQU $5310',
         ' DS $4100-$,$FF',' INCLUDE "compact_grid_name.asm"',' ASSERT $ <= $5000']
    for n,address in (('rows',0x5000),('directory',0x5200),('bases',0x5300),('waters',0x5310)):
        asm += [f' DS ${address:04X}-$,$FF',f' INCBIN "{out/(n+".bin")}"']
    asm.append(' DS $C000-$,$FF')
    result=run(out,'\n'.join(asm)+'\n',inputs,expected,input_address=0xC7F0,input_stride=2,
        output_address=0xC200,output_stride=32,entry_name='cg_build',end_name='cg_end',writes=((0xC200,0xC21F),(0xC7F2,0xC7F3)))
    if source!={n:sha(ROOT/n) for n in names}:raise ValueError('source changed')
    if (build/'build.json').read_bytes()!=metadata or sha(rompath)!=CONTROL_SHA:raise ValueError('control changed')
    if any(sha(ROOT/n)!=h for n,h in m['source_files'].items()):raise ValueError('baseline changed')
    result.update(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        sources=source,oracle_rom_sha256=CONTROL_SHA,complete_prepared_domain=True,normalized_data_bytes=490,
        owner_table_bytes=16,replaced_prepared_bytes=40960,scratch_bytes=2,output_buffer_bytes=32,
        files={p.name:sha(p) for p in out.iterdir() if p.is_file()},
        scope='All160phase x8page/lane owner rows, all32bytes; unlinked constructor, no integration allocation or cadence claim.')
    (out/'component-result.json').write_text(json.dumps(result,indent=2)+'\n');print(result);return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();check(a.build,a.out)
