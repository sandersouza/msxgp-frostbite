"""Skip an already-performed default selection at one native player cache caller."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
from environment import ROOT
from render_build import symbols
sha=lambda b:hashlib.sha256(b).hexdigest()
PARENT='7765bb9e1485a237c49abe0a95c621bea918b61989aae1fc4ad97b1d8b031c84'

def build(base,out,mode='single'):
    base,out=Path(base).resolve(),Path(out).resolve()
    if out.exists()or mode not in('single','original'):raise ValueError('fresh output and declared mode required')
    m=json.loads((base/'build.json').read_text());files=dict(m['source_files']);parent=(base/m['rom']['filename']).read_bytes()
    if sha(parent)!=PARENT or m['rom']['sha256']!=PARENT or len(files)!=214:raise ValueError('exact sealed v26 parent required')
    if any(sha((ROOT/n).read_bytes())!=h for n,h in files.items()):raise ValueError('v26 source closure changed')
    s=symbols(base/'presentation.sym');offset=lambda pc:2*16384+pc-0x8000;ins=lambda op,n:bytes((op,n&255,n>>8))
    entry=s['p_player_cache_lookup'];default=s['p_player_variant_default'];lookup=s['p_player_variant_lookup'];scan=s['p_player_variant_lookup.scan']
    if parent[offset(entry+3):offset(entry+6)]!=ins(0xcd,default):raise ValueError('caller must already select/validate default way')
    if scan!=lookup+4 or parent[offset(lookup):offset(scan)]!=ins(0xcd,default)+bytes((0xd8,)):raise ValueError('public lookup/default/scan layout differs')
    lo,hi=offset(entry),offset(s['p_player_cache_store']);needle=ins(0xcd,lookup)
    if parent.count(needle,lo,hi)!=1:raise ValueError('exactly one eligible native caller required')
    at=parent.index(needle,lo,hi);rom=bytearray(parent);rom[at:at+3]=ins(0xcd,scan)
    changed=[i for i,(a,b)in enumerate(zip(parent,rom))if a!=b]
    if changed!=[at+1]or parent[at+1]!=0x9c or rom[at+1]!=0xa0:raise ValueError('expected one guarded caller operand byte')
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.name=='geometry':(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
        elif p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():shutil.copytree(p,out/p.name)
    if mode=='original':
        (out/'rollback.json').write_text(json.dumps(dict(complete=True,rom_sha256=PARENT,byte_identical=True),indent=2)+'\n');return m
    for section in('template_assets','static_presentation'):
        name='assets-002.bin'
        if name in m[section]['files']:
            data=bytes(rom[2*16384:3*16384]);m[section]['files'][name]=sha(data);(out/'template-assets'/name).write_bytes(data)
    for row in m['contact14']['arena']:
        bank=row['bank'];row['packed_sha256']=sha(rom[bank*16384:(bank+1)*16384])
    files[str(Path(__file__).resolve().relative_to(ROOT))]=sha(Path(__file__).read_bytes())
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    m.update(version='single-cache-default-ap-internal',source_commit=commit,source_dirty=dirty,source_files=files,complete_source=dict(commit=commit,working_tree_dirty=dirty,files=files,scope='One caller skips a redundant default after selection/validation already completed. Public callee and original graphics/mechanics/input/PSG/clock unchanged.'))
    m['cache_default']=dict(parent_rom_sha256=PARENT,patch_offset=at+1,before='9c',after='a0',caller_bank=2,caller_address=at-2*16384+0x8000,public_lookup=lookup,selected_scan_entry=scan,first_default_retained=True,standalone_public_lookup_byte_identical=True,new_ram_bytes=0,new_vram_bytes=0)
    name='frostbite-cache-default-ap.rom';(out/name).write_bytes(rom);m['rom'].update(filename=name,sha256=sha(rom));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n');print(dict(rom_sha256=sha(rom),sources=len(files),changed_ROM_bytes=1));return m

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--mode',choices=('single','original'),default='single');a=p.parse_args();build(a.base,a.out,a.mode)
