"""Optional exact temperature-unit update programs from sealed v23."""
import argparse,json,shutil,subprocess
from pathlib import Path
from environment import ROOT,verified_tool
from presentation_band_spike import sha,verified_bytes
from presentation_dirty_native import checked_kernel_extension
from presentation_temperature_programs import compile_programs
from render_build import symbols
PARENT='b1a1d10077e778f833cfb4cab233740cf2d705bd5d40c397e5b9c8767f1cadd9'

def build(base,out,mode='native'):
    base,out=Path(base).resolve(),Path(out).resolve()
    if out.exists()or mode not in('original','native'):raise ValueError('fresh output and declared mode required')
    m=json.loads((base/'build.json').read_text());parent=verified_bytes(base/m['rom']['filename'],PARENT);files=dict(m['source_files'])
    if len(files)!=182 or any(sha((ROOT/n).read_bytes())!=h for n,h in files.items()):raise ValueError('v23 source closure changed')
    if m['grid24']['name_mode']!='prepared':raise ValueError('retired NAME tails require prepared mode')
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.name=='geometry':continue
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():shutil.copytree(p,out/p.name)
    (out/'geometry').symlink_to((base/'geometry').resolve(),target_is_directory=True)
    if mode=='original':
        (out/'rollback.json').write_text(json.dumps(dict(complete=True,rom_sha256=PARENT,byte_identical=True),indent=2)+'\n');return m
    s=symbols(base/'presentation.sym');dictionary=b''.join(parent[b*16384+0x3800:(b+1)*16384]for b in range(116,119))[:5328]
    original=verified_bytes(ROOT/'references/roms/frostbite.bin','cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834')
    programs,proof=compile_programs(original,dictionary)
    if len(programs)!=8192:raise ValueError('temperature program allocation differs')
    (out/'temperature-programs.bin').write_bytes(programs);(out/'temperature-finite-domain.json').write_text(json.dumps(dict(complete=True,**proof),indent=2)+'\n')
    defs={**s,'AL_RESUME':s['hy_header.no_clear']+3}
    (out/'symbols.inc').write_text('\n'.join(f'{n} EQU ${v:04X}'for n,v in defs.items()if '.'not in n)+'\n')
    source=ROOT/'src/presentation_temperature_programs.asm'
    run=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={out}',f'--raw={out/"temperature-programs-code.bin"}',f'--sym={out/"temperature-programs.sym"}',f'--lst={out/"temperature-programs.lst"}',str(source)],cwd=ROOT,capture_output=True,text=True)
    (out/'temperature-programs-assembler.log').write_text(run.stdout+run.stderr)
    if run.returncode:raise ValueError(run.stdout+run.stderr)
    q=symbols(out/'temperature-programs.sym');code=(out/'temperature-programs-code.bin').read_bytes();size=q['al_ram_end']-q['al_copy'];gate=q['al_gate_end']-q['al_gate'];body=q['al_body_end']-q['al_body']
    if q['al_copy']!=0xefe3 or m['fixed_clock']['ram_code_bytes']!=1763 or q['al_gate']!=0x69fc or gate>74 or len(code)!=size+gate+body:raise ValueError('kernel/gate layout differs')
    rom=bytearray(parent);patches=[];ins=lambda op,v:bytes((op,v&255,v>>8))
    def patch(at,new,old=None):
        before=bytes(rom[at:at+len(new)])
        if old is not None and before!=old:raise ValueError('guarded patch differs')
        if any(at<r['offset']+r['size']and r['offset']<at+len(new)for r in patches):raise ValueError('overlap')
        rom[at:at+len(new)]=new;patches.append(dict(offset=at,size=len(new),before_sha256=sha(before),after_sha256=sha(new)))
    for i in range(4):patch((127+i)*16384+0x3800,programs[i*2048:(i+1)*2048])
    patch(131*16384+0x3800,code[size+gate:])
    at=115*16384+0x3800+1763;patch(at,checked_kernel_extension(parent,at,code[:size],29),bytes([255])*size)
    patch(0x69fc-0x4000,code[size:size+gate])
    patch(s['hy_header.no_clear']-0x4000,ins(0xc3,q['al_gate']),ins(0x3a,s['hy_color']))
    lo=s['t_initializer']-0x4000;hi=s['t_initializer_end']-0x4000;needle=ins(1,1763)
    if parent.count(needle,lo,hi)!=1:raise ValueError('kernel copy count differs')
    patch(parent.index(needle,lo,hi),ins(1,1763+size))
    assert rom[0x20b6:0x2200]==parent[0x20b6:0x2200]
    assert rom[s['p_fast_upload_dirty']-0x4000:s['p_fast_upload_dirty']-0x4000+20]==parent[s['p_fast_upload_dirty']-0x4000:s['p_fast_upload_dirty']-0x4000+20]
    for bank in range(116,127):assert rom[bank*16384:(bank+1)*16384]==parent[bank*16384:(bank+1)*16384]
    for bank in range(127,132):assert rom[bank*16384:bank*16384+0x3800]==parent[bank*16384:bank*16384+0x3800]
    for bank in{p['offset']//16384 for p in patches}:
        name=f'assets-{bank:03d}.bin';data=bytes(rom[bank*16384:(bank+1)*16384])
        for section in('template_assets','static_presentation'):
            if name in m[section]['files']:m[section]['files'][name]=sha(data);(out/'template-assets'/name).write_bytes(data)
    for row in m['contact14']['arena']:
        bank=row['bank'];row['packed_sha256']=sha(rom[bank*16384:(bank+1)*16384])
    m['fixed_clock']['ram_code_bytes']=1763+size;m['fixed_clock']['ram_code_sha256']=sha(rom[115*16384+0x3800:115*16384+0x3800+1763+size])
    for p in(Path(__file__),source,ROOT/'scripts/presentation_temperature_programs.py',ROOT/'tests/test_presentation_temperature_programs.py'):files[str(p.resolve().relative_to(ROOT))]=sha(p.read_bytes())
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    m.update(version='temperature-programs-al-diagnostic',source_commit=commit,source_dirty=dirty,source_files=files,complete_source=dict(commit=commit,working_tree_dirty=dirty,files=files,scope='Exact prepared temperature-unit PGT/key updates only. Same graphics/mechanics/clock.'))
    m['temperature_programs']=dict(parent_rom_sha256=PARENT,patches=patches,**proof,program_banks=[127,130],body_bank=131,reserved_ram_code_bytes_added=size,new_ram_allocation_bytes=0,new_vram_bytes=0,fixed_gate=[q['al_gate'],q['al_gate_end']],protected=['aa_publish','world_palette_6100','p_fast_upload_dirty','banks116..126'])
    s.update({n:v for n,v in q.items()if n.startswith('al_')});(out/'presentation.sym').write_text('\n'.join(f'{n}: EQU 0x{v:08X}'for n,v in s.items())+'\n')
    name='frostbite-temperature-programs-al.rom';(out/name).write_bytes(rom);m['rom'].update(filename=name,sha256=sha(rom));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n');print(dict(rom_sha256=sha(rom),sources=len(files),reserved_ram_code_bytes_added=size,fixed_gate_bytes=gate,body_bytes=body));return m
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--mode',choices=('original','native'),default='native');a=p.parse_args();build(a.base,a.out,a.mode)
