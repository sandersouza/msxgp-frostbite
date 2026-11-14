"""Specialize exact bear contexts, recovering timing margin for flat assets."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from build_compact_packet_experiment import digest
from compact_live_probe import CONTROL_SHA
from environment import ROOT,verified_tool
from reference_traces import private_output


def build(base,out):
    base=base.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((base/'build.json').read_bytes());parent=(base/m['rom']['filename']).read_bytes()
    if not m.get('compact_bear_native_bank') or digest(parent)!=m['rom']['sha256']:raise ValueError('bound common core-bank stage required')
    if any(digest((ROOT/n).read_bytes())!=h for n,h in m['source_files'].items()):raise ValueError('parent source changed')
    proofroot=ROOT/'outputs/compact/issue44-bear-fast-native-01';proof=json.loads((proofroot/'component-result.json').read_bytes())
    if not proof['complete'] or proof['cases']!=4230 or proof['oracle_rom_sha256']!=CONTROL_SHA:raise ValueError('all4230 fast context cases required')
    for n,h in proof['sources'].items():
        if digest((ROOT/n).read_bytes())!=h:raise ValueError('fast context producer changed')
    bases=(proofroot/'bases.bin').read_bytes();masks=(proofroot/'patterns.bin').read_bytes()
    if digest(bases)!=proof['files']['bases.bin'] or parent[56*16384+0x2900:56*16384+0x2900+3760]!=masks:raise ValueError('shared mask/base bytes changed')
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
    asm=' ORG $A800\ncb_patterns EQU $A900\ncb_bases EQU $B7B0\n INCLUDE "compact_bear_tile_fast.asm"\n ASSERT $ <= $A900\n'
    (out/'bc-fast.asm').write_text(asm)
    r=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={ROOT/"src"}',f'--raw={out/"bc-fast.bin"}',str(out/'bc-fast.asm')],capture_output=True,text=True)
    (out/'bc-fast.log').write_text(r.stdout+r.stderr)
    if r.returncode:raise ValueError('fast context assembly failed: '+(r.stdout+r.stderr)[-1000:])
    code=(out/'bc-fast.bin').read_bytes();target=bytearray(parent);patches=[]
    def patch(at,b,reason):
        patches.append(dict(offset=at,size=len(b),before_sha256=digest(parent[at:at+len(b)]),after_sha256=digest(b),reason=reason));target[at:at+len(b)]=b
    patch(56*16384+0x2800,code,'same constructor entry with specialized exact context painting')
    patch(56*16384+0x37B0,bases+bytes([255])*144,'nine16-byte base tiles replace nine padded32-byte contexts')
    m['compact_retired_graphics']['ranges'].append(dict(bank=56,address=0xB840,size=144,kind='retired padded native bear context bytes'))
    m['compact_retired_graphics']['retired_physical_bytes']+=144
    for row in m['contact14']['arena']:
        b=row['bank'];row['packed_sha256']=digest(target[b*16384:(b+1)*16384])
    for n in ('scripts/build_compact_bear_fast.py','scripts/compact_bear_tile_fast_probe.py','src/compact_bear_tile_fast.asm'):
        m['source_files'][n]=digest((ROOT/n).read_bytes())
    m['compact_bear_fast']=dict(parent_rom_sha256=digest(parent),patches=patches,complete_component_cases=4230,code_bytes=len(code),old_context_bytes=288,new_context_bytes=144,
        original_entry_and_shared_masks_retained=True,output_writes_only=[0xC520,0xC530],mapperless=False,human_test_candidate=False)
    filename='frostbite-compact-bear-fast-internal.rom';(out/filename).write_bytes(target)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();m.update(source_commit=commit,source_dirty=True,version='compact-bear-fast-internal')
    m['complete_source']=dict(commit=commit,working_tree_dirty=True,files=m['source_files'],scope='Exact specialized native bear painting; whole-frame qualification required.')
    m['rom'].update(filename=filename,sha256=digest(target));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    print(dict(rom_sha256=digest(target),code_bytes=len(code),context_bytes=144))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.base,a.out)
