"""Optional exact standing left-shore recipes from sealed v22; reversible."""
import argparse,json,shutil,subprocess
from pathlib import Path
from environment import ROOT,verified_tool
from presentation_band_spike import sha,verified_bytes
from presentation_dirty_native import checked_kernel_extension
from presentation_shore_recipes import compile_standing,verify_right_alias
from render_build import symbols
PARENT='b0a3d2befe9c370bbec9ba9096df63143a5743949b1deeeeea63879fa843c1e2'

def build(base,out,mode='native'):
    base,out=Path(base).resolve(),Path(out).resolve()
    if out.exists()or mode not in('original','native'):raise ValueError('fresh output and declared mode required')
    m=json.loads((base/'build.json').read_text());parent=verified_bytes(base/m['rom']['filename'],PARENT);files=dict(m['source_files'])
    if len(files)!=178 or any(sha((ROOT/n).read_bytes())!=h for n,h in files.items()):raise ValueError('v22 source closure changed')
    if m['grid24']['name_mode']!='prepared':raise ValueError('retired NAME tails require prepared grid mode')
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.name=='geometry':continue
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():shutil.copytree(p,out/p.name)
    (out/'geometry').symlink_to((base/'geometry').resolve(),target_is_directory=True)
    if mode=='original':
        (out/'rollback.json').write_text(json.dumps(dict(complete=True,rom_sha256=PARENT,byte_identical=True),indent=2)+'\n');return m
    s=symbols(base/'presentation.sym');palette=bytearray(parent[2*16384+(s['p_sprite_colors_data']&16383):2*16384+(s['p_sprite_colors_data']&16383)+256])
    for c,v in m['player_palette']['normal_overrides'].items():palette[int(c)]=v
    source_rom=verified_bytes(ROOT/'references/roms/frostbite.bin','cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834')
    directory,records,patterns,proof=compile_standing(source_rom,palette)
    proof['right_alias_checks']=verify_right_alias(source_rom,palette,directory,records,patterns)
    if (len(directory),len(records),len(patterns))!=(1152,2464,8128):raise ValueError('standing domain differs')
    for name,data in(('shore-directory.bin',directory),('shore-records.bin',records),('shore-patterns.bin',patterns)):(out/name).write_bytes(data)
    (out/'shore-finite-domain.json').write_text(json.dumps(dict(complete=True,**proof),indent=2)+'\n')
    defs={**s,'AK_DIRECTORY_BANK':120,'AK_RECORD_BANK':121,'AK_PATTERN_BANK':123}
    (out/'symbols.inc').write_text('\n'.join(f'{n} EQU ${v:04X}'for n,v in defs.items()if '.'not in n)+'\n')
    source=ROOT/'src/presentation_shore_recipes.asm'
    run=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={out}',f'--raw={out/"shore-recipes.bin"}',f'--sym={out/"shore-recipes.sym"}',f'--lst={out/"shore-recipes.lst"}',str(source)],cwd=ROOT,capture_output=True,text=True)
    (out/'shore-recipes-assembler.log').write_text(run.stdout+run.stderr)
    if run.returncode:raise ValueError(run.stdout+run.stderr)
    q=symbols(out/'shore-recipes.sym');code=(out/'shore-recipes.bin').read_bytes();size=q['ak_ram_end']-q['ak_entry']
    if q['ak_entry']!=0xefd1 or m['fixed_clock']['ram_code_bytes']!=1745 or len(code)!=size+q['ak_body_end']-q['ak_try']or q['ak_body_end']>0xbc53:raise ValueError('kernel/body layout differs')
    rom=bytearray(parent);patches=[];ins=lambda op,v:bytes((op,v&255,v>>8))
    def patch(at,new,old=None):
        before=bytes(rom[at:at+len(new)])
        if old is not None and before!=old:raise ValueError('guarded patch differs')
        if any(at<r['offset']+r['size']and r['offset']<at+len(new)for r in patches):raise ValueError('overlap')
        rom[at:at+len(new)]=new;patches.append(dict(offset=at,size=len(new),before_sha256=sha(before),after_sha256=sha(new)))
    def tails(first,count,data):
        if len(data)>count*2048:raise ValueError('tail capacity exceeded')
        data+=bytes([255])*(count*2048-len(data))
        for i in range(count):patch((first+i)*16384+0x3800,data[i*2048:(i+1)*2048])
    tails(120,1,directory);tails(121,2,records);tails(123,4,patterns)
    at=115*16384+0x3800+1745;patch(at,checked_kernel_extension(parent,at,code[:size],47),bytes([255])*size)
    old=2*16384+(s['p_dirty_describe']&16383)
    if parent[old:old+3]!=ins(0xc3,s['aj_entry'])or s['p_dirty_capture']!=0xbc53:raise ValueError('retired dirty body not certified')
    patch(2*16384+0x3a91,code[size:])
    patch(115*16384+0x3800+s['x_try']-0xe900,ins(0xc3,q['ak_entry']),bytes.fromhex('3a6bf0'))
    lo=s['t_initializer']-0x4000;hi=s['t_initializer_end']-0x4000;needle=ins(1,1745)
    if parent.count(needle,lo,hi)!=1:raise ValueError('kernel copy count differs')
    patch(parent.index(needle,lo,hi),ins(1,1745+size))
    for bank in range(120,127):assert rom[bank*16384:bank*16384+0x3800]==parent[bank*16384:bank*16384+0x3800]
    for bank in range(116,120):assert rom[bank*16384:(bank+1)*16384]==parent[bank*16384:(bank+1)*16384]
    for bank in{p['offset']//16384 for p in patches}:
        name=f'assets-{bank:03d}.bin';data=bytes(rom[bank*16384:(bank+1)*16384])
        for section in('template_assets','static_presentation'):
            if name in m[section]['files']:m[section]['files'][name]=sha(data);(out/'template-assets'/name).write_bytes(data)
    for row in m['contact14']['arena']:
        bank=row['bank'];row['packed_sha256']=sha(rom[bank*16384:(bank+1)*16384])
    m['fixed_clock']['ram_code_bytes']=1745+size;m['fixed_clock']['ram_code_sha256']=sha(rom[115*16384+0x3800:115*16384+0x3800+1745+size])
    for p in(Path(__file__),source,ROOT/'scripts/presentation_shore_recipes.py',ROOT/'tests/test_presentation_shore_recipes.py'):files[str(p.resolve().relative_to(ROOT))]=sha(p.read_bytes())
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    m.update(version='shore-recipes-ak-diagnostic',source_commit=commit,source_dirty=dirty,source_files=files,complete_source=dict(commit=commit,working_tree_dirty=dirty,files=files,scope='Exact standing left-shore P0 preparation only; original clock/mechanics/graphics.'))
    m['shore_recipes']=dict(parent_rom_sha256=PARENT,patches=patches,**proof,directory_bank=120,record_banks=[121,122],pattern_banks=[123,126],reserved_ram_code_bytes_added=size,new_ram_allocation_bytes=0,new_vram_bytes=0,bank2_body=[q['ak_try'],q['ak_body_end']],protected_banks=[116,117,118,119])
    s.update({n:v for n,v in q.items()if n.startswith('ak_')});(out/'presentation.sym').write_text('\n'.join(f'{n}: EQU 0x{v:08X}'for n,v in s.items())+'\n')
    name='frostbite-shore-recipes-ak.rom';(out/name).write_bytes(rom);m['rom'].update(filename=name,sha256=sha(rom));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n');print(dict(rom_sha256=sha(rom),sources=len(files),reserved_ram_code_bytes_added=size,body_bytes=len(code)-size));return m
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--mode',choices=('original','native'),default='native');a=p.parse_args();build(a.base,a.out,a.mode)
