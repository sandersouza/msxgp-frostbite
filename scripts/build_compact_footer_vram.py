"""Move immutable footer reads to certified unused VRAM tile pairs."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from build_compact_packet_experiment import digest
from compact_footer_vram_probe import assets
from compact_live_probe import CONTROL_SHA
from environment import ROOT,verified_tool
from reference_traces import private_output
from render_build import symbols


def build(base,out):
    base=base.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((base/'build.json').read_bytes());parent=(base/m['rom']['filename']).read_bytes()
    if not m.get('compact_literal_windows') or digest(parent)!=m['rom']['sha256']:raise ValueError('bound literal window stage required')
    if any(digest((ROOT/n).read_bytes())!=h for n,h in m['source_files'].items()):raise ValueError('parent source changed')
    proofroot=ROOT/'outputs/compact/issue44-footer-vram-native-01';proof=json.loads((proofroot/'component-result.json').read_bytes())
    if not proof['complete'] or proof['cases']!=188 or proof['oracle_rom_sha256']!=CONTROL_SHA:raise ValueError('complete188-tile VDP proof required')
    for n,h in proof['sources'].items():
        if digest((ROOT/n).read_bytes())!=h:raise ValueError('footer VRAM component source changed')
    rows,tiles=assets(ROOT/'outputs/presentation/credit-reference-at/build-final');directory=b''.join(r['pattern'].to_bytes(2,'little') for r in rows)
    if digest(directory)!=proof['files']['directory.bin'] or parent[13*16384:13*16384+3008]!=tiles:raise ValueError('footer assets/allocation changed')
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
    s=symbols(base/'presentation.sym')
    def assemble(name,text):
        p=out/(name+'.asm');p.write_text(text)
        r=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={ROOT/"src"}',f'--raw={out/(name+".bin")}',f'--sym={out/(name+".sym")}',str(p)],capture_output=True,text=True)
        (out/(name+'.log')).write_text(r.stdout+r.stderr)
        if r.returncode:raise ValueError('assembly failed: '+(r.stdout+r.stderr)[-1300:])
        return (out/(name+'.bin')).read_bytes(),symbols(out/(name+'.sym'))
    (out/'fv-directory.bin').write_bytes(directory);(out/'fv-tiles.bin').write_bytes(tiles)
    code,q=assemble('fv-bank',f' ORG $B800\nt_restore_interrupts EQU ${s["t_restore_interrupts"]:04X}\n INCLUDE "compact_footer_vram.asm"\n ASSERT $ <= $B900\n DS $B900-$,$FF\nvp_directory:\n INCBIN "{out/"fv-directory.bin"}"\n ASSERT $ <= $C000\n')
    origin=0x560E;limit=0x5790
    asm=[f' ORG ${origin:04X}',f't_mapper EQU ${s["t_mapper"]:04X}',f'p_fast_init EQU ${s["p_fast_init"]:04X}',
         f'vp_store EQU ${q["vp_store"]:04X}',f'vp_read EQU ${q["vp_read"]:04X}',
         'fv_init:',' CALL p_fast_init',' XOR A',' LD ($C7E3),A',' RET',
         'fv_fetch:',' PUSH HL',' LD A,($C7E3)',' CP $A5',' JR Z,.loaded',' CALL fv_load','.loaded:',
         ' POP HL',' LD A,62',' CALL t_mapper',' LD A,L',' CALL vp_read',' LD A,13',' JP t_mapper',
         'fv_load:',' XOR A',' LD ($C7E4),A','.tile:',' LD A,13',' CALL t_mapper',' LD A,($C7E4)',' LD L,A',' LD H,0']
    asm+=[' ADD HL,HL']*4
    asm+=[' LD DE,$8000',' ADD HL,DE',' LD DE,$C520',' LD BC,16',' LDIR',' LD A,62',' CALL t_mapper',' LD A,($C7E4)',' CALL vp_store',
          ' LD A,($C7E4)',' INC A',' LD ($C7E4),A',' CP 188',' JR C,.tile',' LD A,$A5',' LD ($C7E3),A',' RET',f' ASSERT $ <= ${limit:04X}']
    bridge,z=assemble('fv-resident','\n'.join(asm)+'\n')
    old_init=bytes((0xC3,s['p_fast_init']&255,s['p_fast_init']>>8));at=s['cache_init']-0x4000
    if parent[at:at+3]!=old_init:raise ValueError('exact original cache initialization entry required')
    first=s['p_template_footer_prepare']-0x4000;last=s['p_template_footer_fail']-0x4000
    old=bytes((0x2A,s['pf_key']&255,s['pf_key']>>8))+bytes([0x29])*4+bytes((0x11,0,0x80,0x19,0xE5))
    if parent[first:last].count(old)!=1:raise ValueError('unique original footer tile-pointer/miss sequence required')
    callsite=first+parent[first:last].index(old);resume=callsite+len(old)-1+0x4000
    replacement=bytes((0x2A,s['pf_key']&255,s['pf_key']>>8,0xCD,z['fv_fetch']&255,z['fv_fetch']>>8,0xC3,resume&255,resume>>8))
    replacement+=bytes([255])*(len(old)-1-len(replacement))
    target=bytearray(parent);patches=[]
    def patch(at,b,reason):
        patches.append(dict(offset=at,size=len(b),before_sha256=digest(parent[at:at+len(b)]),after_sha256=digest(b),reason=reason));target[at:at+len(b)]=b
    if parent[origin-0x4000:origin-0x4000+len(bridge)]!=bytes([255])*len(bridge):raise ValueError('reclaimed resident NAME arena required')
    if parent[62*16384+0x3800:62*16384+0x3800+len(code)]!=bytes([255])*len(code):raise ValueError('erased prepared NAME tail required')
    patch(origin-0x4000,bridge,'lazy cold footer upload, exact miss reader, initialized two-byte owned state')
    patch(s['cache_init']-0x4000,bytes((0xC3,z['fv_init']&255,z['fv_init']>>8)),'initialize the footer VRAM validity flag with the existing cache init')
    patch(62*16384+0x3800,code,'IRQ-policy-safe footer VRAM reader and188 immutable pair addresses')
    patch(callsite,replacement,'same footer miss/PGT/CGT/key publisher reads original tile through VRAM staging')
    graphics=m['compact_retired_graphics'];row=next(r for r in graphics['ranges'] if r['bank']==62 and r['address']==0xB800 and r['size']==2048)
    row['address']+=len(code);row['size']-=len(code);graphics['retired_physical_bytes']-=len(code)
    retired=m['compact_retired_resident'];row=next(r for r in retired['ranges'] if r['address']==origin and r['size']==limit-origin)
    row['address']+=len(bridge);row['size']-=len(bridge);retired['reused_for_resident_code_bytes']+=len(bridge)
    for row in m['contact14']['arena']:
        b=row['bank'];row['packed_sha256']=digest(target[b*16384:(b+1)*16384])
    for n in ('scripts/build_compact_footer_vram.py','scripts/compact_footer_vram.py','scripts/compact_footer_vram_probe.py','src/compact_footer_vram.asm','tests/test_compact_footer_vram.py'):
        m['source_files'][n]=digest((ROOT/n).read_bytes())
    m['compact_footer_vram']=dict(parent_rom_sha256=digest(parent),patches=patches,allocation=rows,footer_tiles_file='fv-tiles.bin',footer_tiles_sha256=digest(tiles),
        stored_vram_bytes=3008,directory_bytes=376,resident_bridge_bytes=len(bridge),validity_flag=0xC7E3,preload_index=0xC7E4,fetch_address=z['fv_fetch'],
        cold_ROM_source=dict(bank=13,address=0x8000,size=3008),resident_runtime_needs_footer_source_copy=False,
        output_scratch=[0xC520,0xC530],new_VRAM_capacity=0,mapperless=False,human_test_candidate=False,
        scope='Native flat link may omit3008-byte runtime footer source; current banked image retains it as a startup-only input. Full-game frozen-VRAM/NAME/ROM-read gates required.')
    filename='frostbite-compact-footer-vram-internal.rom';(out/filename).write_bytes(target)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();m.update(source_commit=commit,source_dirty=True,version='compact-footer-vram-internal')
    m['complete_source']=dict(commit=commit,working_tree_dirty=True,files=m['source_files'],scope='Unused VRAM footer storage; full-picture and timing qualification required.')
    m['rom'].update(filename=filename,sha256=digest(target));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    print(dict(rom_sha256=digest(target),stored_vram_bytes=3008,directory_bytes=376,resident_bridge_bytes=len(bridge)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.base,a.out)
