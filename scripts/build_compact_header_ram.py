"""Preload compact HUD fragments into free lower RAM; retain cold rendering."""
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
    if not m.get('compact_bear_resident') or digest(parent)!=m['rom']['sha256']:raise ValueError('bound resident native bear required')
    if any(digest((ROOT/n).read_bytes())!=h for n,h in m['source_files'].items()):raise ValueError('parent source changed')
    s=symbols(base/'presentation.sym');out.mkdir(parents=True)
    for p in base.iterdir():
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
    def assemble(name,text):
        p=out/(name+'.asm');p.write_text(text)
        r=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={ROOT/"src"}',f'--raw={out/(name+".bin")}',
            f'--sym={out/(name+".sym")}',str(p)],capture_output=True,text=True)
        (out/(name+'.log')).write_text(r.stdout+r.stderr)
        if r.returncode:raise ValueError('assembly failed: '+(r.stdout+r.stderr)[-1200:])
        return (out/(name+'.bin')).read_bytes()
    code=assemble('hr-code',' ORG $29A0\nch_fragments EQU $2A00\nch_phases EQU $2F60\n INCLUDE "compact_header.asm"\n ASSERT $ <= $2A00\n')
    loader=assemble('hr-loader','\n'.join([' ORG $BED0',' LD HL,$B900',' LD DE,$2A00',' LD BC,1360',' LDIR',
        ' LD HL,$BE60',' LD DE,$2F60',' LD BC,10',' LDIR',' LD HL,$BE70',' LD DE,$29A0',f' LD BC,{len(code)}',' LDIR',' RET',' ASSERT $ <= $C000'])+'\n')
    if len(code)>0x60 or len(loader)>0x130:raise ValueError('cold payload tail too small')
    source=(ROOT/'src/compact_header_lookup.asm').read_text();old='    LD A,52\n    CALL t_mapper\n    JP $B800'
    if source.count(old)!=1:raise ValueError('unique original header exit required')
    source=source.replace(old,'    LD A,(t_enabled)\n    OR A\n    JP NZ,$29A0\n'+old,1)
    asm=[f' ORG ${s["hy_lookup"]:04X}']
    for n in ('hy_half','hy_col','pt_glyphs','t_mapper','t_enabled'):asm.append(f'{n} EQU ${s[n]:04X}')
    gate=assemble('hr-gate','\n'.join(asm)+'\n'+source+f' ASSERT $ <= ${s["hy_lookup_end"]:04X}\n DS ${s["hy_lookup_end"]:04X}-$,0\n')
    target=bytearray(parent);patches=[]
    def patch(at,b,reason):
        patches.append(dict(offset=at,size=len(b),before_sha256=digest(parent[at:at+len(b)]),after_sha256=digest(b),reason=reason));target[at:at+len(b)]=b
    for address,data in ((0xBE70,code),(0xBED0,loader)):
        at=52*16384+address-0x8000
        if parent[at:at+len(data)]!=bytes([255])*len(data):raise ValueError('empty header cold tail required')
        patch(at,data,'relocated header code/cold copying helper')
    owners=[r for r in m['coherent_x']['auxiliary_code'] if r['ram_address']==s['hy_lookup']]
    if len(owners)!=1:raise ValueError('unique header RAM gate owner required')
    owner=owners[0];at=owner['bank']*16384+owner['rom_address']-0x8000
    patch(at,gate,'clock-enabled header uses lower RAM; cold rendering keeps original bank52')
    old_tail=bytes((0x3E,1,0xCD,s['t_mapper']&255,s['t_mapper']>>8,0x3E,0xC3,0x32,0x38,0,0xC9))
    a=s['i_shift2']-0x4000;b=s['i_shift4']-0x4000
    if parent[a:b].count(old_tail)!=1:raise ValueError('unique lower bootstrap restore/vector tail required')
    at=a+parent[a:b].index(old_tail)
    tail=bytes((0x3E,52,0xCD,s['t_mapper']&255,s['t_mapper']>>8,0xCD,0xD0,0xBE))+old_tail
    if at+len(tail)>b:raise ValueError('bootstrap overlaps live enemy edge gate')
    patch(at,tail,'preload header after native query data, before installing/enabling IRQ')
    initializers=[]
    for name,address,data in (('code',0x29A0,code),('font',0x2A00,parent[52*16384+0x3900:52*16384+0x3900+1360]),('phases',0x2F60,parent[52*16384+0x3E60:52*16384+0x3E6A])):
        filename='hr-'+name+'.bin';(out/filename).write_bytes(data);initializers.append(dict(file=filename,ram_address=address,size=len(data),sha256=digest(data)))
    def refresh(node):
        if isinstance(node,dict):
            if all(k in node for k in ('bank','rom_address','ram_address','size','sha256')):
                start=node['bank']*16384+node['rom_address']-0x8000;node['sha256']=digest(target[start:start+node['size']])
            for v in node.values():refresh(v)
        elif isinstance(node,list):
            for v in node:refresh(v)
    refresh(m)
    for row in m['contact14']['arena']:
        bank=row['bank'];row['packed_sha256']=digest(target[bank*16384:(bank+1)*16384])
    m['source_files']['scripts/build_compact_header_ram.py']=digest(Path(__file__).read_bytes())
    m['compact_header_ram']=dict(parent_rom_sha256=digest(parent),patches=patches,initializers=initializers,
        bootstrap_final_ret=at+0x4000+len(tail)-1,hot_entry=0x29A0,cold_constructor_retained=True,
        immutable_ram_bytes=sum(r['size'] for r in initializers),existing_scratch_only=True,mapperless=False,human_test_candidate=False)
    filename='frostbite-compact-header-ram-internal.rom';(out/filename).write_bytes(target)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    m.update(source_commit=commit,source_dirty=True,version='compact-header-ram-internal')
    m['complete_source']=dict(commit=commit,working_tree_dirty=True,files=m['source_files'],scope='Hot HUD constructor/fragments resident in free lower RAM; cold path preserved.')
    m['rom'].update(filename=filename,sha256=digest(target));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    print(dict(rom_sha256=digest(target),immutable_ram_bytes=m['compact_header_ram']['immutable_ram_bytes'],hot_code_bytes=len(code)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.base,a.out)
