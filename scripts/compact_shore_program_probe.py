"""Native doubled-glyph shore mask programs against the complete host domain."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from compact_hazard_edge import expanded_bear_byte,shore_program
from compact_native_fixture import run,sha
from environment import ROOT
from hazard_domain import bear_modes
from original_graphics import SOURCE_SHA256
from reference_traces import private_output


def check(out,limit=None):
    if limit is not None and (type(limit)is not int or limit<=0):raise ValueError('positive case limit required')
    out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    original=(ROOT/'references/roms/frostbite.bin').read_bytes()
    if hashlib.sha256(original).hexdigest()!=SOURCE_SHA256:raise ValueError('canonical original required')
    reps,_=bear_modes(original);glyphs=[]
    if len(reps)!=3:raise ValueError('three qualified bear aliases required')
    for pose in reps:
        offset=original[0xEE7+pose];raw=original[0xD00+offset:0xD00+offset+19]
        if len(raw)!=19 or any(raw[:2]):raise ValueError('qualified bear rows required')
        glyphs.extend((raw,bytes(int(f'{v:08b}'[::-1],2) for v in raw)))
    doubled=b''.join(expanded_bear_byte(v).to_bytes(2,'little') for glyph in glyphs for v in glyph)
    samples=b''.join((0x8000>>i).to_bytes(2,'little') for i in range(16))
    selectors=b''.join(((0x8000>>min(12,k))|sum(1<<(15-c) for c in range(12,k))).to_bytes(2,'little') for k in range(15))
    names=('scripts/compact_shore_program_probe.py','scripts/compact_native_fixture.py','scripts/compact_hazard_edge.py','src/compact_shore_program.asm')
    sources={n:sha(ROOT/n) for n in names}
    out.mkdir(parents=True)
    for n in names:
        p=out/'source'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes())
    for n,data in (('glyphs',doubled),('samples',samples),('selectors',selectors)):(out/(n+'.bin')).write_bytes(data)
    inputs=bytearray();expected=bytearray()
    count=153600 if limit is None else min(limit,153600)
    for mode,glyph in enumerate(glyphs):
        for px in range(160):
            for bx in range(160):
                if len(inputs)//3>=count:break
                inputs.extend((mode,px,bx));expected.extend(v for row in shore_program(glyph,px,bx) for v in row)
    asm=[' ORG $4000',' DB "AB"',' DW start',' DS 12,0','start:',' DI',' LD SP,$F380','ready:',' JP ready',
         'ws_glyphs EQU $5000','ws_samples EQU $5100','ws_selectors EQU $5120',
         ' DS $4100-$,$FF',' INCLUDE "compact_shore_program.asm"',' ASSERT $ <= $5000']
    for n,address in (('glyphs',0x5000),('samples',0x5100),('selectors',0x5120)):
        asm += [f' DS ${address:04X}-$,$FF',f' INCBIN "{out/(n+".bin")}"']
    asm += [' DS $C000-$,$FF']
    result=run(out,'\n'.join(asm)+'\n',inputs,expected,input_address=0xC780,input_stride=3,
        output_address=0xC800,output_stride=90,entry_name='ws_build',end_name='ws_end',
        writes=((0xC7A0,0xC7BF),(0xC800,0xC859)))
    if sources!={n:sha(ROOT/n) for n in names}:raise ValueError('source changed during proof')
    result.update(original_sha256=SOURCE_SHA256,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        sources=sources,complete_native_horizontal_domain=count==153600,doubled_glyph_bytes=len(doubled),
        data_bytes=len(doubled)+len(samples)+len(selectors),rows=18,scratch_bytes=32,
        scope='Standalone exact shore mask compiler over six modes x160playerX x160bearX; no query integration or cadence claim.',
        files={p.name:sha(p) for p in out.iterdir() if p.is_file()})
    (out/'component-result.json').write_text(json.dumps(result,indent=2)+'\n')
    print({k:result[k] for k in ('complete','cases','code_bytes','cycles_including_call_and_jump','complete_native_horizontal_domain')})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--limit',type=int)
    a=p.parse_args();check(a.out,a.limit)
