"""Reuse native bear masks for exact bulk strips; keep the white fast path."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from build_compact_packet_experiment import digest
from compact_live_probe import CONTROL_SHA
from environment import ROOT,verified_tool
from reference_traces import private_output
from render_build import symbols


def build(base,out):
    base=base.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((base/'build.json').read_bytes());parent=(base/m['rom']['filename']).read_bytes()
    if not m.get('compact_bear_records') or digest(parent)!=m['rom']['sha256']:raise ValueError('bound packed bear records required')
    if any(digest((ROOT/n).read_bytes())!=h for n,h in m['source_files'].items()):raise ValueError('parent source changed')
    proofroot=ROOT/'outputs/compact/issue44-bear-strip-fast-native-01';proof=json.loads((proofroot/'component-result.json').read_bytes())
    if not proof['complete'] or proof['cases']!=210 or proof['oracle_rom_sha256']!=CONTROL_SHA:raise ValueError('complete fast strip proof required')
    for n,h in proof['sources'].items():
        if digest((ROOT/n).read_bytes())!=h:raise ValueError('component source changed')
    codes=(proofroot/'codes.bin').read_bytes();masks=(proofroot/'patterns.bin').read_bytes()
    if digest(codes)!=proof['files']['codes.bin'] or parent[56*16384+0x2900:56*16384+0x2900+len(masks)]!=masks:raise ValueError('shared patterns/recipes changed')
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
    s=symbols(base/'presentation.sym')
    def assemble(name,text):
        p=out/(name+'.asm');p.write_text(text)
        r=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={ROOT/"src"}',f'--raw={out/(name+".bin")}',
            f'--sym={out/(name+".sym")}',str(p)],capture_output=True,text=True)
        (out/(name+'.log')).write_text(r.stdout+r.stderr)
        if r.returncode:raise ValueError('assembly failed: '+(r.stdout+r.stderr)[-1200:])
        return (out/(name+'.bin')).read_bytes()
    fast=assemble('bf-native',' ORG $6A50\ncb_patterns EQU $A900\n INCLUDE "compact_bear_strip_fast.asm"\n ASSERT $ <= $6B54\n')
    asm=[f' ORG ${s["p_template_floe_upload"]:04X}']
    for n in ('t_mapper','ai_bulk_upload'):asm.append(f'{n} EQU ${s[n]:04X}')
    asm += [' PUSH BC',' LD A,57',' CALL t_mapper',' LD A,D',' OR E',' JR NZ,bf_materialize',
            ' POP DE',' LD HL,$AF00',' LD A,57',' JP ai_bulk_upload','bf_materialize:',
            ' LD H,D',' LD L,E']+[' ADD HL,HL']*3
    asm += [' LD DE,$A800',' ADD HL,DE',' LD DE,$C7D0',' LD BC,8',' LDIR',
            ' LD A,56',' CALL t_mapper',' LD HL,$C7D0',' CALL $6A50',
            ' POP DE',' LD HL,$C480',' LD A,56',' JP ai_bulk_upload',f' ASSERT $ <= ${s["p_template_upload_fail"]:04X}']
    bridge=assemble('bf-bridge','\n'.join(asm)+'\n')
    target=bytearray(parent);patches=[]
    def patch(at,b,reason):
        patches.append(dict(offset=at,size=len(b),before_sha256=digest(parent[at:at+len(b)]),after_sha256=digest(b),reason=reason));target[at:at+len(b)]=b
    patch(0x6A50-0x4000,fast,'specialized bear strip composition in retired generic geometry body')
    patch(s['p_template_floe_upload']-0x4000,bridge,'bulk preparation bridge in retired raw-floe uploader')
    at=57*16384+0x2800
    if parent[at:at+4096]!=bytes([255])*4096:raise ValueError('erased replacement prefix required')
    data=bytearray([255])*4096;data[:len(codes)]=codes;data[0x700:0x740]=bytes([255])*64
    patch(at,data,'1680 recipe bytes and certified white strip; share existing56:A900 masks')
    first=112*16384+s['ai_bulk.strip_index']-0x8000
    if parent[first:first+6]!=bytes((0x6F,0x26,0xC5,0x5E,0x23,0x56)):raise ValueError('exact original strip-index reader required')
    first+=6;region=parent[first:first+100];needle=bytes((0xCD,s['ai_bulk_upload']&255,s['ai_bulk_upload']>>8))
    if region.count(needle)!=1:raise ValueError('unique native bulk upload required')
    size=region.index(needle)+3;resume=0x8000+first%16384+size;gate=s['p_template_floe_upload']
    replacement=bytes((0xC1,0xCD,gate&255,gate>>8,0xC3,resume&255,resume>>8))
    patch(first,replacement+bytes([255])*(size-len(replacement)),'new strip builder retains original destination, stream and owner publication')
    remaining=13440
    for b in range(103,110):
        n=min(remaining,2048);patch(b*16384+0x3800,bytes([255])*n,'retired prepared native bulk strips')
        m['compact_retired_graphics']['ranges'].append(dict(bank=b,address=0xB800,size=n,kind='retired native bear bulk strips'));remaining-=n
    if remaining:raise ValueError('complete210-strip retirement required')
    #110/111 already contain lower-RAM collision bootstrap data: keep them.
    if target[110*16384:112*16384]!=parent[110*16384:112*16384]:raise ValueError('contact bootstrap changed')
    pools=m['compact_retired_pools'];row=next(r for r in pools['ranges'] if r['bank']==57)
    if row['size']!=0x3800:raise ValueError('exact retired prefix required')
    row['size']=0x2800;pools['retired_physical_bytes']-=4096
    m['compact_retired_graphics']['retired_physical_bytes']+=13440
    for row in m['contact14']['arena']:
        b=row['bank'];row['packed_sha256']=digest(target[b*16384:(b+1)*16384])
    for n in ('scripts/build_compact_bear_strip.py','scripts/compact_bear_strip_fast_probe.py','src/compact_bear_strip_fast.asm','scripts/compact_bear_strip_probe.py'):
        m['source_files'][n]=digest((ROOT/n).read_bytes())
    m['compact_bear_strip']=dict(parent_rom_sha256=digest(parent),patches=patches,old_strip_bytes=13440,recipe_bytes=1680,
        shared_mask_bytes=3760,white_strip_direct_stream=True,added_scratch_ram=[[0xC7D0,0xC7D8]],
        original_vdp_streams_and_owner_publication_retained=True,mapperless=False,human_test_candidate=False)
    filename='frostbite-compact-bear-strip-internal.rom';(out/filename).write_bytes(target)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    m.update(source_commit=commit,source_dirty=True,version='compact-bear-strip-internal')
    m['complete_source']=dict(commit=commit,working_tree_dirty=True,files=m['source_files'],scope='Shared-mask bulk bear strip integration; full route/cadence check required.')
    m['rom'].update(filename=filename,sha256=digest(target));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    print(dict(rom_sha256=digest(target),recipe_bytes=1680,retired_strip_bytes=13440,non_ff_bytes=sum(v!=255 for v in target)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.base,a.out)
