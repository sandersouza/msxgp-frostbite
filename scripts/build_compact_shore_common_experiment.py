"""Integrate the qualified interior floe kernel; retain literal boundary fallback."""
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
    if not m.get('compact_enemy_common') or digest(parent)!=m['rom']['sha256']:
        raise ValueError('bound startup-grid integration required')
    if any(digest((ROOT/n).read_bytes())!=h for n,h in m['source_files'].items()):raise ValueError('source changed')
    source=ROOT/'outputs/compact/issue44-bear-native-full-01'
    proof=json.loads((source/'component-result.json').read_bytes())
    if not proof['complete'] or proof['oracle_rom_sha256']!=CONTROL_SHA:raise ValueError('qualified shore data required')
    assets={n:(source/(n+'.bin')).read_bytes() for n in ('directory','footprints','glyphs','bases')}
    if any(digest(b)!=proof['files'][n+'.bin'] for n,b in assets.items()):raise ValueError('shore assets changed')
    if assets['glyphs']!=(ROOT/'outputs/compact/issue44-kernel-full-01/glyphs.bin').read_bytes() or assets['bases']!=(ROOT/'outputs/compact/issue44-kernel-full-01/bases.bin').read_bytes():
        raise ValueError('shared player bytes differ')
    s=symbols(base/'presentation.sym');out.mkdir(parents=True)
    for p in base.iterdir():
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
    for n,b in assets.items():(out/('cf-'+n+'.bin')).write_bytes(b)
    def assemble(name,text):
        p=out/(name+'.asm');p.write_text(text)
        r=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={ROOT/"src"}',
            f'--raw={out/(name+".bin")}',f'--sym={out/(name+".sym")}',str(p)],capture_output=True,text=True)
        (out/(name+'.log')).write_text(r.stdout+r.stderr)
        if r.returncode:raise ValueError('assembly failed: '+(r.stdout+r.stderr)[-1200:])
        return (out/(name+'.bin')).read_bytes()
    asm=[' DEFINE CF_INPUT_ORIGIN $3300',' DEFINE CF_ENEMY_ONLY',' DEFINE CF_WITH_BEAR',' ORG $3600',
         'cf_glyphs EQU $0100','cf_bases EQU $0F00','cf_directory EQU $0F10','cf_footprints EQU $37C0',
         ' INCLUDE "compact_floe_kernel.asm"',' ASSERT $ <= $3690',' DS $3690-$,$FF']
    for n in ('t_enabled','hazard_x','hazard_y','hazard_shore_min_y','hazard_lookup'):asm.append(f'{n} EQU ${s[n]:04X}')
    asm += [' INCLUDE "compact_shore_common.asm"',' ASSERT $ <= $37C0',' DS $37C0-$,$FF',
            f' INCBIN "{out/"cf-footprints.bin"}"',' ASSERT $ <= $4000',' DS $4000-$,$FF']
    code=parent[46*16384+0x3800:46*16384+0x4000]+parent[47*16384+0x3800:47*16384+0x4000]
    code=code[:0x600]+assemble('cs-code','\n'.join(asm)+'\n')
    loader=[f' ORG ${s["i_shift2"]:04X}',f't_mapper EQU ${s["t_mapper"]:04X}','cfi_boot:']
    for bank,dest,size in ((110,0x0100,0x800),(111,0x0900,0x700),(46,0x3000,0x800),(47,0x3800,0x800),(48,0x2700,0x240)):
        loader += [f' LD A,{bank}',' CALL t_mapper',' LD HL,$B800',f' LD DE,${dest:04X}',f' LD BC,${size:04X}',' LDIR']
    loader += [' LD A,1',' CALL t_mapper',' LD A,$C3',' LD ($0038),A',' RET',f' ASSERT $ <= ${s["i_shift4"]:04X}']
    gate=assemble('cfi-loader','\n'.join(loader)+'\n')
    target=bytearray(parent);patches=[]
    def patch(at,b,reason):
        target[at:at+len(b)]=b
        patches.append(dict(offset=at,size=len(b),before_sha256=digest(parent[at:at+len(b)]),after_sha256=digest(b),reason=reason))
    patch(48*16384+0x3800,parent[47*16384+0x3800:47*16384+0x3A40],'relocate enemy bootstrap data out of new code tail')
    patch(46*16384+0x3800,code[:0x800],'common contacts first bootstrap page')
    patch(47*16384+0x3800,code[0x800:],'common contacts second bootstrap page')
    patch(111*16384+0x3800+0x610,assets['directory'],'shore directory in existing bootstrap padding')
    patch(s['i_shift2']-0x4000,gate,'resident lower-RAM copy before IRQ installation')
    start=s['hazard_shore']-0x4000;end=s['hazard_row']-0x4000
    needle=bytes((0xCD,s['hazard_lookup']&255,s['hazard_lookup']>>8))
    if parent[start:end].count(needle)!=1:raise ValueError('unique shore query call required')
    patch(parent.index(needle,start,end),bytes.fromhex('cd9036'),'compact shore common-X query with literal edge fallback')
    for n in ('scripts/build_compact_shore_common_experiment.py','src/compact_floe_kernel.asm','src/compact_shore_common.asm'):
        m['source_files'][n]=digest((ROOT/n).read_bytes())
    for row in m['contact14']['arena']:
        if row['bank'] in (46,47,48,111):row['packed_sha256']=digest(target[row['bank']*16384:(row['bank']+1)*16384])
    m['compact_shore_common']=dict(parent_rom_sha256=digest(parent),patches=patches,
        immutable_ram=[[0x0F10,0x0F9A],[0x3600,0x4000]],scratch_ram=[0x3300,0x3307],
        eligibility='shore query with PX25..151 and t_enabled; all other calls preserve literal lookup',
        original_tables_retained=True,mapperless=False,human_test_candidate=False)
    filename='frostbite-compact-shore-common-internal.rom';(out/filename).write_bytes(target)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True,cwd=ROOT).strip()
    m.update(source_commit=commit,source_dirty=True,version='compact-shore-common-internal')
    m['complete_source']=dict(commit=commit,working_tree_dirty=True,files=m['source_files'],scope='Unqualified integration experiment.')
    m['rom'].update(filename=filename,sha256=digest(target))
    (out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    print(dict(rom_sha256=digest(target),patches=len(patches),human_test_candidate=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.base,a.out)
