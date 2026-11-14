"""Reclaim2032 native-bank bytes with a proved row-major source summary."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from build_compact_packet_experiment import digest
import compact_core_loop
from environment import ROOT,verified_tool
import native_write_loop
from reference_traces import private_output
from render_build import symbols


def build(base,out):
    base=base.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((base/'build.json').read_bytes());parent=(base/m['rom']['filename']).read_bytes()
    if not m.get('compact_bear_hybrid') or digest(parent)!=m['rom']['sha256']:raise ValueError('bound hybrid dictionary required')
    if any(digest((ROOT/n).read_bytes())!=h for n,h in m['source_files'].items()):raise ValueError('parent source changed')
    proof=json.loads((ROOT/'outputs/compact/issue44-core-loop-native-01/check.json').read_bytes())
    if not proof['complete'] or proof['cases']!=135168:raise ValueError('complete independent core-loop proof required')
    for n,h in proof['utility_fingerprints'].items():
        if digest((ROOT/n).read_bytes())!=h:raise ValueError('core-loop proof source changed')
    original=(ROOT/'references/roms/frostbite.bin').read_bytes();summary,=native_write_loop.summaries(original)
    if summary['limit']!=17 or len(summary['destinations'])!=6:raise ValueError('exact original summary required')
    s=symbols(base/'presentation.sym');entry=s['core_F5E6'];slow=s['core_F5E6_slow'];end=s['core_F5F6'];out.mkdir(parents=True)
    for p in base.iterdir():
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
    def assemble(name,text):
        text='\n'.join(('    '+line if line and not line[0].isspace() and not line.endswith(':') and ' EQU ' not in line else line) for line in text.splitlines())+'\n'
        p=out/(name+'.asm');p.write_text(text)
        r=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--raw={out/(name+".bin")}',str(p)],capture_output=True,text=True)
        (out/(name+'.log')).write_text(r.stdout+r.stderr)
        if r.returncode:raise ValueError('assembly failed: '+(r.stdout+r.stderr)[-1600:])
        return (out/(name+'.bin')).read_bytes()
    prefix='write_loop_F5E6'
    baseline=[' ORG $'+f'{entry:04X}',f'core_F5F6 EQU ${end:04X}']
    for n in ('mask','a','y',*[f'cell{i}' for i in range(6)]):baseline.append(f'{prefix}_{n} EQU ${s[prefix+"_"+n]:04X}')
    baseline+='\n'.join(native_write_loop.emit_summary(summary,prefix,'core_F5F6','core_F5E6_slow')).splitlines()
    old=assemble('cl-original','\n'.join(baseline)+'\n')
    at=2*16384+entry-0x8000
    if old!=parent[at:at+len(old)] or len(old)!=slow-entry+1:raise ValueError('complete old fast summary must reproduce')
    lines=compact_core_loop.emit_summary(summary,prefix,'core_F5F6','core_F5E6_slow')[:-2]
    body=assemble('cl-packed',f' ORG ${entry:04X}\ncore_F5F6 EQU ${end:04X}\ncore_F5E6_slow EQU ${slow:04X}\n{prefix}_rows EQU $9B00\n'+'\n'.join(lines)+f'\n ASSERT $ <= ${slow:04X}\n DS ${slow:04X}-$,0\n')
    data=compact_core_loop.row_data(summary)
    if len(data)!=272:raise ValueError('seventeen16-byte rows required')
    target=bytearray(parent);patches=[]
    def patch(at,b,reason):
        patches.append(dict(offset=at,size=len(b),before_sha256=digest(parent[at:at+len(b)]),after_sha256=digest(b),reason=reason));target[at:at+len(b)]=b
    patch(at,body,'same source-loop guard/fallback; row-major exact effect summary')
    patch(2*16384+0x1B00,data+bytes([255])*(2304-len(data)),'replace nine256-byte columns with seventeen16-byte rows')
    retired=dict(bank=2,address=0x9B00+len(data),size=2304-len(data),kind='retired padded source write-loop tables')
    m['compact_retired_graphics']['ranges'].append(retired);m['compact_retired_graphics']['retired_physical_bytes']+=retired['size']
    for n in ('scripts/compact_core_loop.py','scripts/compact_core_loop_probe.py','scripts/build_compact_core_loop.py','tests/test_compact_core_loop.py'):
        m['source_files'][n]=digest((ROOT/n).read_bytes())
    m['compact_core_loop']=dict(parent_rom_sha256=digest(parent),patches=patches,old_table_bytes=2304,new_table_bytes=272,reclaimed_bank2_half_open=[0x9C10,0xA400],
        independent_CPU_RAM_cases=135168,all_guard_pairs=65536,original_slow_path_retained=True,mapperless=False,human_test_candidate=False)
    filename='frostbite-compact-core-loop-internal.rom';(out/filename).write_bytes(target)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();m.update(source_commit=commit,source_dirty=True,version='compact-core-loop-internal')
    m['complete_source']=dict(commit=commit,working_tree_dirty=True,files=m['source_files'],scope='Row-major source effect summary, original fallback retained; whole-frame qualification required.')
    m['rom'].update(filename=filename,sha256=digest(target));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    print(dict(rom_sha256=digest(target),new_table_bytes=272,reclaimed_bytes=2032,entry_bytes=len(body)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.base,a.out)
