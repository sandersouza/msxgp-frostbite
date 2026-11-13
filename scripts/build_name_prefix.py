"""Omit the unchanged fixed header NAME prefix in the proven warm AL domain."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
from environment import ROOT,verified_tool
from render_build import symbols
sha=lambda b:hashlib.sha256(b).hexdigest()

def build(base,out):
    base,out=Path(base).resolve(),Path(out).resolve()
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((base/'build.json').read_text());files=dict(m['source_files']);parent=(base/m['rom']['filename']).read_bytes()
    if sha(parent)!=m['rom']['sha256']or not m.get('temperature_burst')or m.get('name_prefix'):raise ValueError('verified burst parent required')
    if any(sha((ROOT/n).read_bytes())!=h for n,h in files.items()):raise ValueError('parent source closure changed')
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.name=='geometry':(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
        elif p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():shutil.copytree(p,out/p.name)
    s=symbols(base/'presentation.sym');(out/'symbols.inc').write_text('\n'.join(f'{n} EQU ${v:04X}'for n,v in s.items()if'.'not in n)+'\n');source=ROOT/'src/presentation_name_prefix.asm'
    run=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={out}',f'--raw={out/"name-prefix-code.bin"}',f'--sym={out/"name-prefix.sym"}',str(source)],cwd=ROOT,capture_output=True,text=True);(out/'name-prefix-assembler.log').write_text(run.stdout+run.stderr)
    if run.returncode:raise ValueError(run.stdout+run.stderr)
    q=symbols(out/'name-prefix.sym');code=(out/'name-prefix-code.bin').read_bytes();ram=q['prefix_ram_padded_end']-q['prefix_names'];fixed=q['prefix_fixed_end']-q['prefix_compact']
    if ram!=58 or fixed!=12 or len(code)!=ram+fixed or q['prefix_compact']!=0x6a32:raise ValueError('reserved allocation differs')
    rom=bytearray(parent);patches=[]
    def patch(at,data):
        old=bytes(rom[at:at+len(data)]);rom[at:at+len(data)]=data;patches.append(dict(offset=at,size=len(data),before_sha256=sha(old),after_sha256=sha(data)))
    patch(147*16384+0x3800+s['ac_names']-0xf400,code[:ram]);patch(q['prefix_compact']-0x4000,code[ram:])
    lo=s['p_template_upload_names_known']-0x4000
    assert rom[lo:lo+160]==parent[lo:lo+160]
    world=bytes(rom[147*16384+0x3800:147*16384+0x3800+1240]);(out/'world.bin').write_bytes(world)
    for section in('coherent_x','native_lanes'):
        for row in m[section]['auxiliary_code']:
            if row['ram_address']==0xf400:row['sha256']=sha(world)
    m['world_x']['code_sha256']=sha(world);name='assets-147.bin';blob=bytes(rom[147*16384:148*16384])
    for section in('template_assets','static_presentation'):
        if name in m[section]['files']:m[section]['files'][name]=sha(blob);(out/'template-assets'/name).write_bytes(blob)
    for row in m['contact14']['arena']:
        if row['bank']==147:row['packed_sha256']=sha(blob)
    for p in(Path(__file__),source,ROOT/'scripts/presentation_name_prefix.py',ROOT/'scripts/presentation_name_prefix_check.py',ROOT/'tests/test_presentation_name_prefix.py'):files[str(p.resolve().relative_to(ROOT))]=sha(p.read_bytes())
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    m.update(version='name-prefix-ao-internal',source_commit=commit,source_dirty=dirty,source_files=files,complete_source=dict(commit=commit,working_tree_dirty=dirty,files=files,scope='Warm fixed header NAME prefix omitted; dirty transactions, graphics and original source clocks/mechanics preserved.'))
    m['name_prefix']=dict(parent_rom_sha256=m['rom']['sha256'],patches=patches,ram_publisher_bytes=58,fixed_gap_bytes=12,predicate='hy_lo==14 and (p_fd_rows&7)==7 and p_fd_rows!=255',skip_sorted_prefix_rows=3,dirty_flags_unchanged=True,list_and_count_trimmed_only_at_final_private_publisher=True,public_name_uploader_unchanged=True,new_ram_bytes=0,new_vram_bytes=0)
    s.update({n:v for n,v in q.items()if n.startswith('prefix_')});(out/'presentation.sym').write_text('\n'.join(f'{n}: EQU 0x{v:08X}'for n,v in s.items())+'\n');name='frostbite-name-prefix-ao.rom';(out/name).write_bytes(rom);m['rom'].update(filename=name,sha256=sha(rom));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n');print(dict(rom_sha256=sha(rom),sources=len(files),ram_bytes=ram,fixed_bytes=fixed));return m

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();build(a.base,a.out)
