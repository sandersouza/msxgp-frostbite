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
    if not m.get('compact_grid_experiment',{}).get('expanded_ram_rows') or digest(parent)!=m['rom']['sha256']:
        raise ValueError('bound startup-grid integration required')
    if any(digest((ROOT/n).read_bytes())!=h for n,h in m['source_files'].items()):raise ValueError('source changed')
    source=ROOT/'outputs/compact/issue44-kernel-full-01'
    proof=json.loads((source/'component-result.json').read_bytes())
    if not proof['complete'] or proof['oracle_rom_sha256']!=CONTROL_SHA:raise ValueError('qualified floe data required')
    assets={n:(source/(n+'.bin')).read_bytes() for n in ('glyphs','directory','footprints','bases')}
    if any(digest(b)!=proof['files'][n+'.bin'] for n,b in assets.items()):raise ValueError('floe assets changed')
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
    data=[' ORG $0100']
    for n,a in (('glyphs',0x0100),('directory',0x0300),('footprints',0x0A00),('bases',0x0F00)):
        data += [f' DS ${a:04X}-$,$FF',f' INCBIN "{out/("cf-"+n+".bin")}"']
    data += [' DS $1000-$,$FF'];blob=assemble('cfi-data','\n'.join(data)+'\n')
    asm=[' DEFINE CF_INPUT_ORIGIN $3300',' ORG $3000','cf_glyphs EQU $0100','cf_directory EQU $0300','cf_footprints EQU $0A00','cf_bases EQU $0F00',
         ' INCLUDE "compact_floe_kernel.asm"',' ASSERT $ <= $3100',' DS $3100-$,$FF']
    for n in ('t_enabled','floe_control_index','core_fault','floe_acquire','floe_bit_masks','floe_viewmask','floe_viewbyte'):asm.append(f'{n} EQU ${s[n]:04X}')
    asm += [' INCLUDE "compact_floe_interior.asm"',' ASSERT $ <= $3300',' DS $3400-$,0']
    code=assemble('cfi-code','\n'.join(asm)+'\n')
    loader=[f' ORG ${s["i_shift2"]:04X}',f't_mapper EQU ${s["t_mapper"]:04X}','cfi_boot:']
    for bank,dest,size in ((110,0x0100,0x800),(111,0x0900,0x700),(46,0x3000,0x400)):
        loader += [f' LD A,{bank}',' CALL t_mapper',' LD HL,$B800',f' LD DE,${dest:04X}',f' LD BC,${size:04X}',' LDIR']
    loader += [' LD A,1',' CALL t_mapper',' LD A,$C3',' LD ($0038),A',' RET',f' ASSERT $ <= ${s["i_shift4"]:04X}']
    gate=assemble('cfi-loader','\n'.join(loader)+'\n')
    target=bytearray(parent);patches=[]
    def patch(at,b,reason):
        target[at:at+len(b)]=b
        patches.append(dict(offset=at,size=len(b),before_sha256=digest(parent[at:at+len(b)]),after_sha256=digest(b),reason=reason))
    for bank in (110,111):
        if parent[bank*16384+0x3800:(bank+1)*16384]!=bytes([255])*2048:raise ValueError('reclaimed contact tail not empty')
    # Bank46's former prepared NAME records are bypassed by the startup-grid gate.
    patch(110*16384+0x3800,blob[:0x800],'bootstrap floe glyphs/directory')
    patch(111*16384+0x3800,blob[0x800:],'bootstrap remaining floe data')
    patch(46*16384+0x3800,code,'bootstrap kernel in retired prepared-grid storage')
    patch(s['i_shift2']-0x4000,gate,'resident lower-RAM copy before IRQ installation')
    start,end=s['i_shifts']-0x4000,s['i_shift2']-0x4000
    needle=bytes.fromhex('3ec3323800')
    if parent[start:end].count(needle)!=1:raise ValueError('unique grid boot hook required')
    at=parent.index(needle,start,end);entry=s['i_shift2']
    patch(at,bytes((0xCD,entry&255,entry>>8,0,0)),'extend native bootstrap')
    at=s['floe_acquire']-0x4000
    if parent[at:at+3]!=bytes.fromhex('3a1dc0'):raise ValueError('literal acquisition prologue changed')
    patch(at,bytes.fromhex('c30031'),'interior acquisition with literal boundary fallback')
    for n in ('scripts/build_compact_floe_interior_experiment.py','src/compact_floe_kernel.asm','src/compact_floe_interior.asm'):
        m['source_files'][n]=digest((ROOT/n).read_bytes())
    for row in m['contact14']['arena']:
        if row['bank'] in (46,110,111):row['packed_sha256']=digest(target[row['bank']*16384:(row['bank']+1)*16384])
    m['compact_floe_interior']=dict(parent_rom_sha256=digest(parent),patches=patches,
        immutable_ram=[[0x0100,0x1000],[0x3000,0x3300]],scratch_ram=[0x3300,0x3307],
        eligibility='t_enabled and playerX9..153; original entry preserved otherwise',
        original_tables_retained=True,mapperless=False,human_test_candidate=False)
    filename='frostbite-compact-floe-interior-internal.rom';(out/filename).write_bytes(target)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True,cwd=ROOT).strip()
    m.update(source_commit=commit,source_dirty=True,version='compact-floe-interior-internal')
    m['complete_source']=dict(commit=commit,working_tree_dirty=True,files=m['source_files'],scope='Unqualified integration experiment.')
    m['rom'].update(filename=filename,sha256=digest(target))
    (out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    print(dict(rom_sha256=digest(target),patches=len(patches),human_test_candidate=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.base,a.out)
