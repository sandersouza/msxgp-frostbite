"""Prove every accepted normal P0 pattern through the absolute source-mask path."""
import argparse
import json
from pathlib import Path
from compact_native_fixture import run,sha
from compact_live_probe import CONTROL_SHA
from native_graphic_grammar import p0
from environment import ROOT
from reference_traces import private_output


def check(build,out):
    build=build.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((build/'build.json').read_bytes());rom=(build/m['rom']['filename']).read_bytes()
    if sha(build/m['rom']['filename'])!=m['rom']['sha256']:raise ValueError('bound source required')
    original=ROOT/'outputs/presentation/credit-reference-at/build-final';cm=json.loads((original/'build.json').read_bytes());r=(original/cm['rom']['filename']).read_bytes()
    if sha(original/cm['rom']['filename'])!=CONTROL_SHA:raise ValueError('immutable accepted P0 source oracle required')
    expected=r[149*16384+0x3800:150*16384]+r[148*16384+0x3A60:148*16384+0x3B20]
    if expected!=(build/'player-band-patterns.bin').read_bytes() or len(expected)!=2240:raise ValueError('all70 patterns required')
    expansion=rom[2*16384+0x3300:2*16384+0x3700];g=p0(expected,expansion)
    offsets=[int.from_bytes(g['directory'][i:i+2],'little') for i in range(0,140,2)]
    directory=b''.join(((v&32768)|((v&32767)+0x5100)).to_bytes(2,'little') for v in offsets)
    out.mkdir(parents=True)
    for name,data in dict(rows=g['rows'],directory=directory,expansion=expansion).items():(out/(name+'.bin')).write_bytes(data)
    asm=''' ORG $4000
 DB "AB"
 DW start
 DS 12,0
start:
 DI
 LD SP,$F380
ready:
 JP ready
 DS $4100-$,$FF
np0_entry:
 LD A,($C7B4)
 INCLUDE "native_p0_pattern_fast.asm"
 ASSERT $ <= $5000
 DS $5000-$,$FF
np0_directory:
'''+f' INCBIN "{out/"directory.bin"}"\n DS $5100-$,$FF\nnp0_rows:\n INCBIN "{out/"rows.bin"}"\n DS $6000-$,$FF\nnp0_expansion:\n INCBIN "{out/"expansion.bin"}"\n DS $C000-$,$FF\n'
    result=run(out,asm,bytes(range(70)),expected,input_address=0xC7B4,input_stride=1,output_address=0xC500,
               output_stride=32,entry_name='np0_entry',end_name='np0_end',writes=((0xC500,0xC51F),))
    result.update(original_P0_patterns=70,absolute_pointer_phase_bit=True,oracle_rom_sha256=CONTROL_SHA,
                  sources={n:sha(ROOT/n) for n in ('scripts/native_p0_fast_probe.py','src/native_p0_pattern_fast.asm','scripts/native_graphic_grammar.py')})
    (out/'component-result.json').write_text(json.dumps(result,indent=2)+'\n');print(result)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('build','out'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();check(a.build,a.out)
