"""Add certified immutable white-ice tables to the sealed border diagnostic."""
import argparse,json,shutil,subprocess
from pathlib import Path
from environment import ROOT,verified_tool
from presentation_band_spike import sha,verified_bytes
from presentation_ice_atlas import compile_atlas
from render_build import symbols

PARENT='26260606e1ecbdeed0a8c0d3ae7ef4eb37658341da3a0ab02cd52ac8a5286ac9'

def build(base,out,mode='atlas'):
    base,out=Path(base).resolve(),Path(out).resolve()
    if out.exists()or mode not in('original','atlas'):raise ValueError('new output and declared mode required')
    m=json.loads((base/'build.json').read_text());parent=verified_bytes(base/m['rom']['filename'],PARENT);files=dict(m['source_files'])
    if len(files)!=165 or any(sha((ROOT/n).read_bytes())!=h for n,h in files.items()):raise ValueError('v19 source closure changed')
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.name=='geometry':continue
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():shutil.copytree(p,out/p.name)
    (out/'geometry').symlink_to((base/'geometry').resolve(),target_is_directory=True)
    if mode=='original':
        (out/'rollback.json').write_text(json.dumps(dict(complete=True,rom_sha256=PARENT,byte_identical=True),indent=2)+'\n');return m
    s=symbols(base/'presentation.sym');packets=[]
    for phase in range(16):
        at=36*16384+0x3800+phase*128;count=parent[at+115]
        if not 1<=count<=14:raise ValueError('delta8 phase0 packet differs')
        address=int.from_bytes(parent[at+117:at+119],'little');bank=parent[at+119];pointer=bank*16384+address-0x8000
        packets.append(dict(patterns=tuple(parent[at+i*8:at+(i+1)*8]for i in range(count)),names=parent[pointer:pointer+30]))
    atlas=compile_atlas(packets)
    if len(atlas['ids'])!=62 or len(atlas['patterns'])!=496:raise ValueError('certified atlas population differs')
    (out/'atlas-patterns.bin').write_bytes(atlas['patterns']);(out/'atlas-programs.bin').write_bytes(atlas['programs'])
    (out/'symbols.inc').write_text('\n'.join(f'{n} EQU ${v:04X}'for n,v in s.items()if '.'not in n)+'\n')
    source=ROOT/'src/presentation_ice_atlas.asm'
    run=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={out}',f'--raw={out/"ice-atlas.bin"}',f'--sym={out/"ice-atlas.sym"}',f'--lst={out/"ice-atlas.lst"}',str(source)],cwd=ROOT,capture_output=True,text=True)
    (out/'ice-atlas-assembler.log').write_text(run.stdout+run.stderr)
    if run.returncode:raise ValueError(run.stdout+run.stderr)
    q=symbols(out/'ice-atlas.sym');code=(out/'ice-atlas.bin').read_bytes();rom=bytearray(parent);patches=[]
    def patch(at,new,expected=None):
        old=bytes(rom[at:at+len(new)])
        if expected is not None and old!=expected:raise ValueError('guarded patch differs')
        if any(at<r['offset']+r['size']and r['offset']<at+len(new)for r in patches):raise ValueError('overlap')
        rom[at:at+len(new)]=new;patches.append(dict(offset=at,size=len(new),before_sha256=sha(old),after_sha256=sha(new)))
    ins=lambda op,v:bytes((op,v&255,v>>8))
    bridges=q['ah_bridges_padded_end']-q['ah_boot_bridge']
    if bridges!=26 or len(code)!=26+2048 or q['ah_boot_bridge']!=0xf5b8:raise ValueError('allocation differs')
    patch(147*16384+0x39b8,code[:26],bytes(26))
    patch(147*16384+0x383d,ins(0xc3,q['ah_runtime_bridge']),ins(0x3a,s['p_w_row']))
    patch(0x49d7-0x4000,ins(0xcd,q['ah_boot_bridge']),ins(0xcd,0x4a7b))
    patch(65*16384+0x3800,code[26:])
    if rom[65*16384:65*16384+0x3800]!=parent[65*16384:65*16384+0x3800]:raise ValueError('contact14 prefix changed')
    world=bytes(rom[147*16384+0x3800:147*16384+0x3800+1240]);(out/'world.bin').write_bytes(world)
    for section in('coherent_x','native_lanes'):
        for row in m[section]['auxiliary_code']:
            if row['ram_address']==0xf400:row['sha256']=sha(world)
    m['world_x']['code_sha256']=sha(world)
    for bank in{p['offset']//16384 for p in patches}:
        name=f'assets-{bank:03d}.bin';data=bytes(rom[bank*16384:(bank+1)*16384])
        for section in('template_assets','static_presentation'):
            if name in m[section]['files']:m[section]['files'][name]=sha(data);(out/'template-assets'/name).write_bytes(data)
    for row in m['contact14']['arena']:
        bank=row['bank'];row['packed_sha256']=sha(rom[bank*16384:(bank+1)*16384])
    for p in(Path(__file__),source,ROOT/'scripts/presentation_ice_atlas.py',ROOT/'scripts/presentation_ice_atlas_check.py',ROOT/'tests/test_presentation_ice_atlas.py'):
        files[str(p.resolve().relative_to(ROOT))]=sha(p.read_bytes())
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    m.update(version='ice-atlas-ah-diagnostic',source_commit=commit,source_dirty=dirty,source_files=files,complete_source=dict(commit=commit,working_tree_dirty=dirty,files=files,scope='Additive immutable white/delta8 ice only; source mechanics/input/audio unchanged.'))
    m['ice_atlas']=dict(parent_rom_sha256=PARENT,patches=patches,ids=list(atlas['ids']),patterns_sha256=sha(atlas['patterns']),programs_sha256=sha(atlas['programs']),bank=65,patterns_address=q['ah_patterns'],programs_address=q['ah_programs'],context=dict(color=15,delta=8,delta_index=1),new_ram_bytes=0,occupied_existing_vram_bytes=1984,footer_ids_preserved=[160,203])
    s.update({n:v for n,v in q.items()if n.startswith('ah_')});(out/'presentation.sym').write_text('\n'.join(f'{n}: EQU 0x{v:08X}'for n,v in s.items())+'\n')
    name='frostbite-ice-atlas-ah.rom';(out/name).write_bytes(rom);m['rom'].update(filename=name,sha256=sha(rom));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    print(dict(rom_sha256=sha(rom),sources=len(files),atlas_ids=len(atlas['ids']),banked_code_data_bytes=q['ah_end']-q['ah_boot']));return m

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--mode',choices=('original','atlas'),default='atlas');a=p.parse_args();build(a.base,a.out,a.mode)
