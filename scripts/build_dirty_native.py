"""Optional specialized dirty traversal; original mode preserves exact v21."""
import argparse,json,shutil,subprocess
from pathlib import Path
from environment import ROOT,verified_tool
from presentation_band_spike import sha,verified_bytes
from presentation_dirty_native import checked_kernel_extension,fixed_floe_spans
from render_build import symbols
PARENT='635876dcf352bfc2eafee908757045c7387a11653c21f4dce266fd765dd5ad15'

def build(base,out,mode='native'):
    base,out=Path(base).resolve(),Path(out).resolve()
    if out.exists()or mode not in('original','native'):raise ValueError('fresh output and declared mode required')
    m=json.loads((base/'build.json').read_text());parent=verified_bytes(base/m['rom']['filename'],PARENT);files=dict(m['source_files'])
    if len(files)!=174 or any(sha((ROOT/n).read_bytes())!=h for n,h in files.items()):raise ValueError('v21 source closure changed')
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.name=='geometry':continue
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():shutil.copytree(p,out/p.name)
    (out/'geometry').symlink_to((base/'geometry').resolve(),target_is_directory=True)
    if mode=='original':
        (out/'rollback.json').write_text(json.dumps(dict(complete=True,rom_sha256=PARENT,byte_identical=True),indent=2)+'\n');return m
    s=symbols(base/'presentation.sym');(out/'symbols.inc').write_text('\n'.join(f'{n} EQU ${v:04X}'for n,v in s.items()if '.'not in n)+'\n')
    at=s['p_template_floe_spans']-0x4000
    spans=fixed_floe_spans(parent[at:at+24])
    (out/'floe-spans.inc').write_text('\n'.join(f'aj_floe_offset{i} EQU {offset}\naj_floe_mask{i} EQU {mask}'for i,(offset,mask)in enumerate(spans))+'\n')
    source=ROOT/'src/presentation_dirty_native.asm'
    run=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={out}',f'--raw={out/"dirty-native.bin"}',f'--sym={out/"dirty-native.sym"}',f'--lst={out/"dirty-native.lst"}',str(source)],cwd=ROOT,capture_output=True,text=True)
    (out/'dirty-native-assembler.log').write_text(run.stdout+run.stderr)
    if run.returncode:raise ValueError(run.stdout+run.stderr)
    q=symbols(out/'dirty-native.sym');code=(out/'dirty-native.bin').read_bytes();size=q['aj_ram_end']-q['aj_entry']
    if q['aj_entry']!=0xefc1 or m['fixed_clock']['ram_code_bytes']!=1729 or len(code)!=size+q['aj_body_end']-q['aj_body']:raise ValueError('kernel layout differs')
    rom=bytearray(parent);patches=[]
    ins=lambda op,v:bytes((op,v&255,v>>8))
    def patch(at,new,old=None):
        before=bytes(rom[at:at+len(new)])
        if old is not None and before!=old:raise ValueError('guarded patch differs')
        if any(at<r['offset']+r['size']and r['offset']<at+len(new)for r in patches):raise ValueError('overlap')
        rom[at:at+len(new)]=new;patches.append(dict(offset=at,size=len(new),before_sha256=sha(before),after_sha256=sha(new)))
    at=115*16384+0x3800+1729
    patch(at,checked_kernel_extension(parent,at,code[:size],63),bytes([255])*size)
    lo=s['t_initializer']-0x4000;hi=s['t_initializer_end']-0x4000;needle=ins(1,1729)
    if parent.count(needle,lo,hi)!=1:raise ValueError('kernel copy count differs')
    patch(parent.index(needle,lo,hi),ins(1,1729+size))
    patch(113*16384+0x3800,code[size:])
    patch(2*16384+(s['p_dirty_describe']&16383),ins(0xc3,q['aj_entry']),ins(0xcd,s['p_dirty_capture']))
    assert rom[113*16384:113*16384+0x3800]==parent[113*16384:113*16384+0x3800]
    for bank in{p['offset']//16384 for p in patches}:
        name=f'assets-{bank:03d}.bin';data=bytes(rom[bank*16384:(bank+1)*16384])
        for section in('template_assets','static_presentation'):
            if name in m[section]['files']:m[section]['files'][name]=sha(data);(out/'template-assets'/name).write_bytes(data)
    for row in m['contact14']['arena']:
        bank=row['bank'];row['packed_sha256']=sha(rom[bank*16384:(bank+1)*16384])
    m['fixed_clock']['ram_code_bytes']=1729+size;m['fixed_clock']['ram_code_sha256']=sha(rom[115*16384+0x3800:115*16384+0x3800+1729+size])
    for p in(Path(__file__),source,ROOT/'scripts/presentation_dirty_native.py',ROOT/'tests/test_presentation_dirty_specialized.py'):files[str(p.resolve().relative_to(ROOT))]=sha(p.read_bytes())
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    m.update(version='dirty-native-aj-diagnostic',source_commit=commit,source_dirty=dirty,source_files=files,complete_source=dict(commit=commit,working_tree_dirty=dirty,files=files,scope='Specialized dirty traversal only; original capture/history/union retained.'))
    m['dirty_native']=dict(parent_rom_sha256=PARENT,patches=patches,body_bank=113,reserved_ram_code_bytes_added=size,new_ram_allocation_bytes=0,new_vram_bytes=0,banked_code_bytes=len(code)-size,scope='Specialized comparisons, unrolled four-lane traversal and exact history copy. Same graphics/mechanics/clock.')
    s.update({n:v for n,v in q.items()if n.startswith('aj_')});(out/'presentation.sym').write_text('\n'.join(f'{n}: EQU 0x{v:08X}'for n,v in s.items())+'\n')
    name='frostbite-dirty-native-aj.rom';(out/name).write_bytes(rom);m['rom'].update(filename=name,sha256=sha(rom));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n');print(dict(rom_sha256=sha(rom),sources=len(files),reserved_ram_code_bytes_added=size,body_bytes=len(code)-size));return m
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--mode',choices=('original','native'),default='native');a=p.parse_args();build(a.base,a.out,a.mode)
