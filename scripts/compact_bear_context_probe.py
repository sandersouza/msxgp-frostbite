"""Prove the sparse bear context lookup over every original1024-byte index."""
import argparse
import json
from pathlib import Path

from build_compact_packet_experiment import digest
from compact_live_probe import CONTROL_SHA
from compact_native_fixture import run,sha
from environment import ROOT
from reference_traces import private_output


def check(build,out,fast=False):
    build=build.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((build/'build.json').read_bytes());rom=(build/m['rom']['filename']).read_bytes()
    if digest(rom)!=CONTROL_SHA:raise ValueError('sealed accepted control required')
    expected=rom[102*16384+0x3C00:103*16384];values=[(i,v) for i,v in enumerate(expected) if v!=255]
    if len(values)!=9 or sorted(v for i,v in values)!=list(range(9)):raise ValueError('nine certified context entries required')
    entries=b''.join(i.to_bytes(2,'little')+bytes((v,)) for i,v in values)
    out.mkdir(parents=True);(out/'entries.bin').write_bytes(entries)
    module='src/compact_bear_context_branch.asm' if fast else 'src/compact_bear_context.asm'
    asm=[' ORG $4000',' DB "AB"',' DW start',' DS 12,0','start:',' DI',' LD SP,$F380','ready:',' JP ready',
         ' DS $4100-$,$FF','cx_entry:',' LD HL,($C7B4)',' CALL cx_find_context',' LD ($C7C0),A',' RET',
         f' INCLUDE "{Path(module).name}"','cx_entries:',f' INCBIN "{out/"entries.bin"}"',' DS $C000-$,$FF']
    result=run(out,'\n'.join(asm)+'\n',b''.join(i.to_bytes(2,'little') for i in range(1024)),expected,
        input_address=0xC7B4,input_stride=2,output_address=0xC7C0,output_stride=1,entry_name='cx_entry',end_name='cx_end',writes=((0xC7C0,0xC7C0),))
    names=(module,'scripts/compact_bear_context_probe.py')
    for n in names:
        p=out/'source'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes())
    result.update(oracle_rom_sha256=CONTROL_SHA,old_context_bytes=1024,sparse_entry_bytes=0 if fast else 27,branch_selector=fast,
        sources={n:sha(ROOT/n) for n in names},files={p.name:sha(p) for p in out.iterdir() if p.is_file()},
        scope='All1024 original context addresses including1015 misses; exact byte/ABI/bounded writes, component only.')
    (out/'component-result.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k not in ('sources','files')})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--fast',action='store_true');a=p.parse_args();check(a.build,a.out,a.fast)
