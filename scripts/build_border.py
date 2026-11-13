"""Optional border24 view from the exact sealed v0.0.18 control."""
import argparse,json,shutil,subprocess
from pathlib import Path
from environment import ROOT,verified_tool
from presentation_band_spike import sha,verified_bytes
from presentation_border import left_mask
from render_build import symbols

PARENT='6677bb8ccc9caaf440b24df6a69fe9ecd7d206743645d738623e6cfedc8a219a'

def build(base,out,mode='border'):
    base,out=Path(base).resolve(),Path(out).resolve()
    if mode not in('original','border','mask-only')or out.exists():raise ValueError('new output/declared mode required')
    m=json.loads((base/'build.json').read_text());parent=verified_bytes(base/m['rom']['filename'],PARENT)
    files=dict(m['source_files'])
    if len(files)!=160 or any(sha((ROOT/n).read_bytes())!=h for n,h in files.items()):raise ValueError('v18 source closure changed')
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.name=='geometry':continue
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():shutil.copytree(p,out/p.name)
    (out/'geometry').symlink_to((base/'geometry').resolve(),target_is_directory=True)
    if mode=='original':
        (out/'rollback.json').write_text(json.dumps(dict(complete=True,rom_sha256=PARENT,byte_identical=True),indent=2)+'\n')
        print(dict(mode=mode,rom_sha256=PARENT));return m
    s=symbols(base/'presentation.sym');rom=bytearray(parent);patches=[]
    def ins(op,v):return bytes((op,v&255,v>>8))
    def patch(at,new):
        if any(at<r['offset']+r['size']and r['offset']<at+len(new)for r in patches):raise ValueError('patch overlap')
        old=bytes(rom[at:at+len(new)]);rom[at:at+len(new)]=new
        patches.append(dict(offset=at,size=len(new),before_sha256=sha(old),after_sha256=sha(new)))
    # Both cached and cold paths append the seven original mask records.
    needle=ins(0x21,s['ys_mask'])+bytes.fromhex('011c00edb0')
    lo=s['ys_static']-0x4000;hi=s['ys_mask']-0x4000
    if parent.count(needle,lo,hi)!=1:raise ValueError('cached mask copy differs')
    patch(parent.index(needle,lo,hi),bytes(len(needle)))
    lo=2*16384+s['presentation_sprites_prepare']-0x8000
    black=2*16384+s['presentation_sprites_prepare.black']-0x8000
    start=black-7
    expected=ins(0x2a,s['p_s_sat'])+bytes((0x16,63,0x06,7))
    if parent[start:black]!=expected:raise ValueError('cold mask entry differs')
    end=parent.index(ins(0x22,s['p_s_sat'])+bytes.fromhex('3a4df0'),black,black+80)+3
    patch(start,ins(0xc3,end-2*16384+0x8000))
    q={}
    if mode=='border':
        (out/'symbols.inc').write_text('\n'.join(f'{n} EQU ${v:04X}'for n,v in s.items()if '.'not in n)+'\n')
        (out/'left-masks.bin').write_bytes(b''.join(left_mask(x).to_bytes(2,'big')for x in range(11)))
        source=ROOT/'src/presentation_border.asm'
        run=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={out}',f'--raw={out/"border.bin"}',f'--sym={out/"border.sym"}',f'--lst={out/"border.lst"}',str(source)],cwd=ROOT,capture_output=True,text=True)
        (out/'border-assembler.log').write_text(run.stdout+run.stderr)
        if run.returncode:raise ValueError(run.stdout+run.stderr)
        q=symbols(out/'border.sym');code=(out/'border.bin').read_bytes();cursor=0
        sections=[('ac_names','ac_names_end',147*16384+0x3800+q['ac_names']-0xf400),
            ('ac_eligible','ac_eligible_end',7*16384+s['x_eligible']-0x8000),
            ('ac_clip','ac_clip_end',7*16384+s['x_clip_pattern']-0x8000),
            ('ac_left_masks','ac_left_masks_end',s['ys_mask']-0x4000)]
        for first,last,at in sections:
            count=q[last]-q[first];patch(at,code[cursor:cursor+count]);cursor+=count
        if cursor!=len(code):raise ValueError('unbound code section')
        if q['ac_names']!=0xf57e or q['ac_names_end']!=0xf5d2 or s['x_right_masks']!=0xa70b:raise ValueError('allocation differs')
        at=s['p_fast_upload_dirty']-0x4000
        if parent[at:at+3]!=ins(0xc3,s['p_template_upload_names_known']):raise ValueError('NAME publisher differs')
        patch(at,ins(0xc3,q['ac_names']))
        lo=7*16384+s['ab_certified_setup']-0x8000;hi=7*16384+s['ab_certified_setup_end']-0x8000
        if parent.count(bytes.fromhex('fe08'),lo,hi)!=1:raise ValueError('certified threshold not unique')
        patch(parent.index(bytes.fromhex('fe08'),lo,hi),bytes.fromhex('fe0b'))
        files[str(source.relative_to(ROOT))]=sha(source.read_bytes())
    else:
        # Private unqualified upper-bound test: deliberately no border/edge fixes.
        lo=7*16384+s['x_eligible']-0x8000;hi=7*16384+s['x_accepted']-0x8000
        needle=ins(0x3a,s['x_n'])+bytes.fromhex('3c4f')
        if parent.count(needle,lo,hi)!=1:raise ValueError('obsolete mask rectangle differs')
        patch(parent.index(needle,lo,hi)+3,b'\0')
    world=bytes(rom[147*16384+0x3800:147*16384+0x3800+1240]);(out/'world.bin').write_bytes(world)
    (out/'hybrid.bin').write_bytes(rom[7*16384+s['x_hybrid']-0x8000:7*16384+s['x_hybrid_end']-0x8000])
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
    for p in(Path(__file__),ROOT/'scripts/presentation_border.py',ROOT/'scripts/presentation_border_check.py',ROOT/'tests/test_presentation_border.py'):
        files[str(p.resolve().relative_to(ROOT))]=sha(p.read_bytes())
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    m.update(version='border-ag-diagnostic',source_commit=commit,source_dirty=dirty,source_files=files,
        complete_source=dict(commit=commit,working_tree_dirty=dirty,files=files,scope='Additive item3 mask/border/eligibility only. Source mechanics unchanged.'))
    m['border_clip']=dict(view='border24-v1'if mode=='border'else'mask-only-unqualified',mode=mode,parent_rom_sha256=PARENT,patches=patches,
        black_name_column=2,black_rows=[8,21],left_target_x=24,left_source_x=11,mask_sat_removed=7,new_ram_bytes=0,new_vram_bytes=0,
        scope='Four extra target pixels cropped in former mask region only; original foreground P0 priority retained. No clock, input, audio or mechanics changes.')
    s.update({n:v for n,v in q.items()if n.startswith('ac_')})
    (out/'presentation.sym').write_text('\n'.join(f'{n}: EQU 0x{v:08X}'for n,v in s.items())+'\n')
    name='frostbite-border-ag.rom';(out/name).write_bytes(rom);m['rom'].update(filename=name,sha256=sha(rom))
    (out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    print(dict(mode=mode,rom_sha256=sha(rom),sources=len(files),patches=len(patches)));return m

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--mode',choices=('original','border','mask-only'),default='border');a=p.parse_args();build(a.base,a.out,a.mode)
