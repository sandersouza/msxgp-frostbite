"""Optional pixel-identical bear sprite prefix from the sealed v24 cartridge."""
import argparse,json,shutil,subprocess
from pathlib import Path
from environment import ROOT,verified_tool
from presentation_band_spike import sha,verified_bytes
from presentation_bear_hybrid import compile_transactions
from render_build import symbols
PARENT='4686698ca7c19cf6db27a8393d70a15297fe982b0f9a68274964233f2355c5be'

def build(base,out,mode='hybrid'):
    base,out=Path(base).resolve(),Path(out).resolve()
    if out.exists()or mode not in('original','hybrid'):raise ValueError('fresh output and declared mode required')
    m=json.loads((base/'build.json').read_text());parent=verified_bytes(base/m['rom']['filename'],PARENT);files=dict(m['source_files'])
    if len(files)!=186 or any(sha((ROOT/n).read_bytes())!=h for n,h in files.items()):raise ValueError('v24 source closure changed')
    if m['fixed_clock']['ram_code_bytes']!=1777 or m['grid24']['name_mode']!='prepared':raise ValueError('exact prepared v24 layout required')
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.name=='geometry':continue
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():shutil.copytree(p,out/p.name)
    (out/'geometry').symlink_to((base/'geometry').resolve(),target_is_directory=True)
    if mode=='original':
        (out/'rollback.json').write_text(json.dumps(dict(complete=True,rom_sha256=PARENT,byte_identical=True),indent=2)+'\n');return m
    assets=compile_transactions(base);s=symbols(base/'presentation.sym');defs={**s,'AN_HUD_CONT':s['presentation_hud_prepare']+3}
    for n,v in assets.items():
        if isinstance(v,bytes):(out/('bear-'+n.replace('_','-')+'.bin')).write_bytes(v)
    registry=b''.join(r['original_ID'].to_bytes(2,'little')+bytes((r['cut'],))for r in assets['registry'])
    (out/'bear-registry.bin').write_bytes(registry)
    (out/'synthetic-registry.json').write_text(json.dumps(assets['registry'],indent=2)+'\n')
    (out/'symbols.inc').write_text('\n'.join(f'{n} EQU ${v:04X}'for n,v in defs.items()if '.'not in n)+'\n');source=ROOT/'src/presentation_bear_hybrid.asm'
    run=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={out}',f'--raw={out/"bear-hybrid.bin"}',f'--sym={out/"bear-hybrid.sym"}',f'--lst={out/"bear-hybrid.lst"}',str(source)],cwd=ROOT,capture_output=True,text=True)
    (out/'bear-hybrid-assembler.log').write_text(run.stdout+run.stderr)
    if run.returncode:raise ValueError(run.stdout+run.stderr)
    q=symbols(out/'bear-hybrid.sym');code=(out/'bear-hybrid.bin').read_bytes();slot=s['w_selected']-s['w_header']
    if slot!=110 or len(code)!=slot+2048 or q['an_ram_end']>s['w_selected']or q['an_body']!=0xb800:raise ValueError('audited RAM/body allocation exceeded')
    rom=bytearray(parent);patches=[];ins=lambda op,v:bytes((op,v&255,v>>8))
    def patch(at,new,expected=None):
        old=bytes(rom[at:at+len(new)])
        if expected is not None and old!=expected:raise ValueError('guarded patch differs')
        if any(at<r['offset']+r['size']and r['offset']<at+len(new)for r in patches):raise ValueError('overlapping patch')
        rom[at:at+len(new)]=new;patches.append(dict(offset=at,size=len(new),before_sha256=sha(old),after_sha256=sha(new)))
    def tails(first,count,payload):
        if len(payload)>count*2048:raise ValueError('safe tail capacity exceeded')
        payload=payload+bytes([255])*(count*2048-len(payload))
        for i in range(count):patch((first+i)*16384+0x3800,payload[i*2048:(i+1)*2048])
    tails(132,1,assets['directory']+assets['sprites']);tails(133,1,assets['records']);tails(134,8,assets['programs'])
    tails(114,1,code[slot:])
    patch(115*16384+0x3800+s['w_header']-0xe900,code[:slot])
    lo=s['presentation_world_prepare']-0x4000;hi=s['p_world_primitive']-0x4000;needle=ins(0xcd,s['ai_entry'])
    if parent.count(needle,lo,hi)!=1:raise ValueError('unique early bear call required')
    patch(parent.index(needle,lo,hi),ins(0xcd,q['an_early']),needle)
    patch(s['presentation_hud_prepare']-0x4000,ins(0xc3,q['an_header']),ins(0x3a,0xf03f))
    for bank in(114,115,*range(132,142)):
        if rom[bank*16384:bank*16384+0x3800]!=parent[bank*16384:bank*16384+0x3800]:raise ValueError('contact14 prefix changed')
    for bank in(*range(116,132),*range(142,162)):assert rom[bank*16384:(bank+1)*16384]==parent[bank*16384:(bank+1)*16384]
    a=115*16384+0x3800
    for lo,hi in((s['w_owner'],s['w_header']),(s['w_selected'],0xeff1)):
        assert rom[a+lo-0xe900:a+hi-0xe900]==parent[a+lo-0xe900:a+hi-0xe900]
    for bank in{p['offset']//16384 for p in patches}:
        name=f'assets-{bank:03d}.bin';blob=bytes(rom[bank*16384:(bank+1)*16384])
        for section in('template_assets','static_presentation'):
            if name in m[section]['files']:m[section]['files'][name]=sha(blob);(out/'template-assets'/name).write_bytes(blob)
    for row in m['contact14']['arena']:
        bank=row['bank'];row['packed_sha256']=sha(rom[bank*16384:(bank+1)*16384])
    m['fixed_clock']['ram_code_sha256']=sha(rom[a:a+1777])
    for p in(Path(__file__),source,ROOT/'scripts/presentation_bear_hybrid.py',ROOT/'scripts/presentation_bear_hybrid_check.py',ROOT/'tests/test_presentation_bear_hybrid.py'):files[str(p.resolve().relative_to(ROOT))]=sha(p.read_bytes())
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    m.update(version='bear-hybrid-an-diagnostic',source_commit=commit,source_dirty=dirty,source_files=files,complete_source=dict(commit=commit,working_tree_dirty=dirty,files=files,scope='Pixel-identical sprite-prefix/tile-suffix bear. Original source mechanics/input/clock/audio unchanged.'))
    m['bear_hybrid']=dict(parent_rom_sha256=PARENT,patches=patches,source_descriptors=512,records=96,record_bytes=22,record_split=[93,3],extra_records_bank=114,extra_records_address=q['an_extra_records'],tile_count=assets['tile_count'],source_pattern_count=assets['source_pattern_count'],synthetic_registry=assets['registry'],synthetic_mask_sha256=sha(assets['new_masks']),sprite_pattern_slots=[[22,23],[46,47]],body_bank=114,directory_sprite_bank=132,record_banks=[133,133],program_banks=[134,141],program_count=assets['program_count'],program_bytes=44,programs_per_bank=46,registry_bank=114,registry_address=q['an_registry'],supported_palettes=[[0,1],[1,15]],reserved_ram_code_bytes_added=0,retired_ram_code_bytes_rewritten=slot,new_ram_allocation_bytes=0,new_vram_bytes=0,mutable_cache=[0xe8b9,0xe8bb],source_geometry_checks=assets['geometry_cases'],scope='Deferred bear after finalSAT, exact critical-line admission, dirty-complete background reuse or forced original rows6..8 restoration and full native fallback; source/graphics unchanged.')
    s.update({n:v for n,v in q.items()if n.startswith('an_')});(out/'presentation.sym').write_text('\n'.join(f'{n}: EQU 0x{v:08X}'for n,v in s.items())+'\n');name='frostbite-bear-hybrid-an.rom';(out/name).write_bytes(rom);m['rom'].update(filename=name,sha256=sha(rom));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n');print(dict(rom_sha256=sha(rom),sources=len(files),RAM_code_bytes=q['an_ram_end']-q['an_early'],body_bytes=q['an_body_end']-q['an_body'],tiles=assets['tile_count']));return m

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--mode',choices=('original','hybrid'),default='hybrid');a=p.parse_args();build(a.base,a.out,a.mode)
