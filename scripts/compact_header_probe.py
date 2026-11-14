"""Qualify five-phase glyph composition against sealed header dictionary bytes."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from compact_live_probe import CONTROL_SHA
from compact_native_fixture import run,sha
from environment import ROOT
from original_graphics import SOURCE_SHA256
from presentation_header_dictionary import project_pair
from presentation_static_assets import header_fragments
from reference_traces import private_output


def dictionary_cases():
    for kind in (1,3):
        for a in range(16):
            for b in range(16):yield a,b,kind
    for kind in (0,2,4):
        for a in range(34):yield a,0,kind
    for a in range(16):yield a,32,3
    for b in (10,33):yield 32,b,1
    for a in (10,33):yield a,10,3
    for b in range(32):yield 10,b,1


def check(build,out):
    build=Path(build).resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    metadata=(build/'build.json').read_bytes();m=json.loads(metadata);rompath=build/m['rom']['filename'];rom=rompath.read_bytes()
    if sha(rompath)!=CONTROL_SHA:raise ValueError('sealed v30 required')
    if any(sha(ROOT/n)!=h for n,h in m['source_files'].items()):raise ValueError('baseline source differs')
    original=(ROOT/'references/roms/frostbite.bin').read_bytes()
    if hashlib.sha256(original).hexdigest()!=SOURCE_SHA256:raise ValueError('original differs')
    names=('scripts/compact_header_probe.py','scripts/compact_native_fixture.py','src/compact_header.asm',
           'scripts/presentation_header_dictionary.py','scripts/presentation_static_assets.py')
    source={n:sha(ROOT/n) if (ROOT/n).exists() else None for n in names};out.mkdir(parents=True)
    for n in names:
        if (ROOT/n).exists():
            p=out/'source'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes())
    raw=b''.join(rom[b*16384+0x3800:(b+1)*16384] for b in (116,117,118))[:5328]
    domain=list(dictionary_cases())
    if len(domain)!=666:raise ValueError('complete header domain differs')
    inputs,expected=bytearray(),bytearray()
    for i,(a,b,kind) in enumerate(domain):
        projected=project_pair(original,a,b,kind)
        if projected!=raw[i*8:i*8+8]:raise ValueError('sealed dictionary differs')
        inputs.extend((a,b,kind));expected.extend(raw[i*8:i*8+8])
    for kind in range(5):
        for a in range(34):
            for b in range(34):inputs.extend((a,b,kind));expected.extend(project_pair(original,a,b,kind))
    fragments=header_fragments(original)
    (out/'fragments.bin').write_bytes(fragments);(out/'phases.bin').write_bytes(bytes((0,255,1,2,3,255,4,0,4,255)))
    asm=[' ORG $4000',' DB "AB"',' DW start',' DS 12,0','start:',' DI',' LD SP,$F380','ready:',' JP ready',
         'ch_fragments EQU $5000','ch_phases EQU $5600',' DS $4100-$,$FF',' INCLUDE "compact_header.asm"',
         ' ASSERT $ <= $5000',' DS $5000-$,$FF',f' INCBIN "{out/"fragments.bin"}"',
         ' DS $5600-$,$FF',f' INCBIN "{out/"phases.bin"}"',' DS $C000-$,$FF']
    result=run(out,'\n'.join(asm)+'\n',inputs,expected,input_address=0xC7B0,input_stride=3,
        output_address=0xC480,output_stride=8,entry_name='ch_build',end_name='ch_end',writes=((0xC480,0xC487),))
    if source!={n:sha(ROOT/n) for n in names}:raise ValueError('source changed')
    if sha(rompath)!=CONTROL_SHA or (build/'build.json').read_bytes()!=metadata:raise ValueError('control changed')
    if any(sha(ROOT/n)!=h for n,h in m['source_files'].items()):raise ValueError('baseline source changed')
    result.update(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),sources=source,
        oracle_rom_sha256=CONTROL_SHA,original_sha256=SOURCE_SHA256,sealed_dictionary_cases=666,
        complete_generic_projection_cases=5780,fragment_data_bytes=len(fragments),phase_bytes=10,replaced_dictionary_bytes=5328,
        scratch_bytes=0,output_buffer_bytes=8,files={p.name:sha(p) for p in out.iterdir() if p.is_file()},
        scope='All666sealed header records and all5kinds x34x34glyph projections; component only, no game integration/cadence claim.')
    (out/'component-result.json').write_text(json.dumps(result,indent=2)+'\n');print(result);return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();check(a.build,a.out)
