"""Add one black sea-edge NAME cell to the existing reserved publisher."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
from environment import ROOT,verified_tool
from render_build import symbols
sha=lambda b:hashlib.sha256(b).hexdigest()

def build(base,out):
    base,out=Path(base).resolve(),Path(out).resolve()
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((base/'build.json').read_text());files=dict(m['source_files']);rom=bytearray((base/m['rom']['filename']).read_bytes())
    if sha(rom)!=m['rom']['sha256']or m['border_clip']['black_rows']!=[8,21]or m.get('border_closure'):raise ValueError('unclosed verified parent required')
    if any(sha((ROOT/n).read_bytes())!=h for n,h in files.items()):raise ValueError('parent source closure changed')
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.name=='geometry':(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
        elif p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():shutil.copytree(p,out/p.name)
    s=symbols(base/'presentation.sym');(out/'symbols.inc').write_text('\n'.join(f'{n} EQU ${v:04X}'for n,v in s.items()if'.'not in n)+'\n');source=ROOT/'src/presentation_border_closure.asm'
    run=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={out}',f'--raw={out/"border-closure.bin"}',f'--sym={out/"border-closure.sym"}',str(source)],cwd=ROOT,capture_output=True,text=True);(out/'border-closure-assembler.log').write_text(run.stdout+run.stderr)
    if run.returncode:raise ValueError(run.stdout+run.stderr)
    code=(out/'border-closure.bin').read_bytes();at=147*16384+0x3800+s['ac_names']-0xf400
    if s['ac_names']!=0xf57e or s['ac_names_code_end']!=0xf5b8 or len(code)!=s['ac_names_code_end']-s['ac_names']:raise ValueError('resident allocation changed')
    old=bytes(rom[at:at+len(code)]);expected=bytes.fromhex('368019')*13+bytes.fromhex('3680c3')
    if old.count(expected)!=1:raise ValueError('original14-row publisher differs')
    rom[at:at+len(code)]=code;world=bytes(rom[147*16384+0x3800:147*16384+0x3800+1240]);(out/'world.bin').write_bytes(world)
    for section in('coherent_x','native_lanes'):
        for row in m[section]['auxiliary_code']:
            if row['ram_address']==0xf400:row['sha256']=sha(world)
    m['world_x']['code_sha256']=sha(world);name='assets-147.bin';blob=bytes(rom[147*16384:148*16384])
    for section in('template_assets','static_presentation'):
        if name in m[section]['files']:m[section]['files'][name]=sha(blob);(out/'template-assets'/name).write_bytes(blob)
    for row in m['contact14']['arena']:
        if row['bank']==147:row['packed_sha256']=sha(blob)
    for p in(Path(__file__),source,ROOT/'scripts/presentation_border_closure.py',ROOT/'scripts/presentation_border_closure_check.py',ROOT/'tests/test_presentation_border_closure.py'):files[str(p.resolve().relative_to(ROOT))]=sha(p.read_bytes())
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    m.update(version='border-closure-ao-internal',source_commit=commit,source_dirty=dirty,source_files=files,complete_source=dict(commit=commit,working_tree_dirty=dirty,files=files,scope='Additive lower sea-edge closure; original mechanics and P0 priority unchanged.'))
    m['border_closure']=dict(parent_rom_sha256=m['rom']['sha256'],black_rows=[8,22],added_rectangle=[16,176,24,184],new_sprites=0,new_ram_bytes=0,new_vram_bytes=0,patch=dict(offset=at,size=len(code),before_sha256=sha(old),after_sha256=sha(code)))
    name='frostbite-border-closure-ao.rom';(out/name).write_bytes(rom);m['rom'].update(filename=name,sha256=sha(rom));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n');print(dict(rom_sha256=sha(rom),sources=len(files),new_sprites=0));return m

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();build(a.base,a.out)
