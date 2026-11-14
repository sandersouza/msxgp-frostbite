"""Relink the verified dirty traversal into reclaimed resident cartridge space."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from build_compact_packet_experiment import digest
from environment import ROOT,verified_tool
from reference_traces import private_output
from render_build import symbols


def build(base,out):
    base=base.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((base/'build.json').read_bytes());parent=(base/m['rom']['filename']).read_bytes()
    if not m.get('compact_retired_resident') or digest(parent)!=m['rom']['sha256']:raise ValueError('bound resident reclamation required')
    if any(digest((ROOT/n).read_bytes())!=h for n,h in m['source_files'].items()):raise ValueError('parent source changed')
    origin,end=0x7408,0x7900
    if parent[origin-0x4000:end-0x4000]!=bytes([255])*(end-origin):raise ValueError('empty reclaimed resident range required')
    s=symbols(base/'presentation.sym');out.mkdir(parents=True)
    for p in base.iterdir():
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
    (out/'symbols.inc').write_text('\n'.join(f'{n} EQU ${v:04X}' for n,v in s.items() if '.' not in n and not n.startswith('aj_'))+'\n')
    source=(ROOT/'src/presentation_dirty_native.asm').read_text()
    def assemble(name,text):
        p=out/(name+'.asm');p.write_text(text)
        r=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={out}',f'--raw={out/(name+".bin")}',
            f'--sym={out/(name+".sym")}',str(p)],capture_output=True,text=True)
        (out/(name+'.log')).write_text(r.stdout+r.stderr)
        if r.returncode:raise ValueError('assembly failed: '+(r.stdout+r.stderr)[-1200:])
        return (out/(name+'.bin')).read_bytes(),symbols(out/(name+'.sym'))
    original,q0=assemble('dr-baseline',source);old_ram=q0['aj_ram_end']-q0['aj_entry']
    at=115*16384+0x3800+q0['aj_entry']-0xE900
    if parent[at:at+old_ram]!=original[:old_ram] or parent[113*16384+0x3800:113*16384+0x3800+len(original)-old_ram]!=original[old_ram:]:
        raise ValueError('unchanged dirty module does not reproduce parent bytes')
    old='    LD A,113\n    CALL t_mapper\n    CALL aj_body\n    LD A,2\n    JP t_mapper'
    if source.count(old)!=1 or source.count('    ORG $B800')!=1:raise ValueError('unique dirty wrapper/body origins required')
    source=source.replace(old,'    CALL aj_body\n    LD A,2\n    RET',1).replace('    ORG $B800',f'    ORG ${origin:04X}',1)
    source+=f'    ASSERT $ <= ${end:04X}\n'
    code,q=assemble('dr-resident',source);ram=q['aj_ram_end']-q['aj_entry'];body=code[ram:]
    if q['aj_entry']!=s['aj_entry'] or len(body)!=len(original)-old_ram or ram>old_ram or q['aj_body']!=origin:
        raise ValueError('resident dirty relink changed public ABI/body size')
    target=bytearray(parent);patches=[]
    def patch(at,b,reason):
        patches.append(dict(offset=at,size=len(b),before_sha256=digest(parent[at:at+len(b)]),after_sha256=digest(b),reason=reason));target[at:at+len(b)]=b
    patch(at,code[:ram]+bytes([255])*(old_ram-ram),'same-address RAM caller without113/2 mapper round trip')
    patch(origin-0x4000,body,'same dirty traversal linked into reclaimed resident directory bytes')
    patch(113*16384+0x3800,bytes([255])*len(body),'retired banked dirty traversal')
    node=m['compact_retired_resident']
    if node['ranges']!=[dict(address=origin,size=end-origin,before_sha256=node['ranges'][0]['before_sha256'])]:
        raise ValueError('exact reclaimed resident allocation required')
    node['ranges']=[dict(address=origin+len(body),size=end-origin-len(body))];node['reused_for_resident_code_bytes']=len(body)
    m['compact_retired_graphics']['ranges'].append(dict(bank=113,address=0xB800,size=len(body),kind='retired banked dirty traversal'))
    m['compact_retired_graphics']['retired_physical_bytes']+=len(body)
    fixed=m['fixed_clock'];start=115*16384+0x3800;fixed['ram_code_sha256']=digest(target[start:start+fixed['ram_code_bytes']])
    for row in m['contact14']['arena']:
        b=row['bank'];row['packed_sha256']=digest(target[b*16384:(b+1)*16384])
    m['source_files']['scripts/build_compact_dirty_resident.py']=digest(Path(__file__).read_bytes())
    m['compact_dirty_resident']=dict(parent_rom_sha256=digest(parent),patches=patches,resident_address=origin,resident_body_bytes=len(body),
        original_module_reproduced=True,removed_mapper_calls_per_prepare=2,public_RAM_entry_unchanged=True,
        remaining_reclaimed_bytes=end-origin-len(body),mapperless=False,human_test_candidate=False)
    m['dirty_native'].update(body_bank=0,body_address=origin,banked_code_bytes=0,resident_body_bytes=len(body))
    s.update({n:v for n,v in q.items() if n.startswith('aj_')});(out/'presentation.sym').write_text('\n'.join(f'{n}: EQU 0x{v:08X}' for n,v in s.items())+'\n')
    filename='frostbite-compact-dirty-resident-internal.rom';(out/filename).write_bytes(target)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    m.update(source_commit=commit,source_dirty=True,version='compact-dirty-resident-internal')
    m['complete_source']=dict(commit=commit,working_tree_dirty=True,files=m['source_files'],scope='First resident relink: exact dirty traversal without its mapper round trip.')
    m['rom'].update(filename=filename,sha256=digest(target));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    print(dict(rom_sha256=digest(target),resident_body_bytes=len(body),remaining_reclaimed_bytes=end-origin-len(body),removed_mapper_calls_per_prepare=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.base,a.out)
