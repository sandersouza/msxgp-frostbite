"""Data-only wordmark replacement on the exact sealed v29 ROM."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
from environment import ROOT
from render_build import symbols
from presentation_credit_reference import compile_tiles

sha=lambda b:hashlib.sha256(b).hexdigest()
PARENT='94e4ee71f2ef4021e9ec16c960fa258cae6d27d660c11f3005dde0d51d0473d3'
def build(base,out):
    base,out=Path(base).resolve(),Path(out).resolve()
    m=json.loads((base/'build.json').read_text());files=dict(m['source_files'])
    parent=(base/m['rom']['filename']).read_bytes()
    if sha(parent)!=PARENT or len(files)!=229 or any(sha((ROOT/n).read_bytes())!=h for n,h in files.items()):raise ValueError('Exact sealed v29 closure required')
    if out.exists():raise ValueError('Fresh output required')
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.name=='geometry':(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
        elif p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():shutil.copytree(p,out/p.name)
    s=symbols(base/'presentation.sym');rom=bytearray(parent);patches=[]
    for coarse,name in((False,'as_patterns'),(True,'as_coarse')):
        tiles,cells=compile_tiles(coarse);blob=b''.join(tiles.values())
        if len(blob)!=112 or cells!=[tuple(c)for c in m['aligned_credit']['cells']]:raise ValueError('Existing14-tile layout required')
        at=65*16384+s[name]-0x8000;old=parent[at:at+len(blob)];rom[at:at+len(blob)]=blob
        patches.append(dict(offset=at,size=len(blob),before_sha256=sha(old),after_sha256=sha(blob)))
        (out/('reference-credit-coarse.bin'if coarse else'reference-credit-patterns.bin')).write_bytes(blob)
    allowed={i for p in patches for i in range(p['offset'],p['offset']+p['size'])}
    if any(a!=b and i not in allowed for i,(a,b)in enumerate(zip(parent,rom))):raise ValueError('Non-pattern ROM byte changed')
    def refresh(node):
        if isinstance(node,dict):
            if all(k in node for k in('bank','rom_address','ram_address','size','sha256')):
                at=node['bank']*16384+node['rom_address']-0x8000;node['sha256']=sha(rom[at:at+node['size']])
            for v in node.values():refresh(v)
        elif isinstance(node,list):
            for v in node:refresh(v)
    refresh(m)
    name='assets-065.bin';blob=bytes(rom[65*16384:66*16384])
    for section in('template_assets','static_presentation'):
        if name in m[section]['files']:m[section]['files'][name]=sha(blob);(out/'template-assets'/name).write_bytes(blob)
    for row in m['contact14']['arena']:
        if row['bank']==65:row['packed_sha256']=sha(blob)
    for p in(Path(__file__),ROOT/'scripts/presentation_credit_reference.py',ROOT/'scripts/presentation_credit_reference_check.py'):files[str(p.resolve().relative_to(ROOT))]=sha(p.read_bytes())
    commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();dirty=bool(subprocess.check_output(['git','status','--porcelain'],text=True).strip())
    m.update(version='reference-credit-at-diagnostic',source_commit=commit,source_dirty=dirty,source_files=files,complete_source=dict(commit=commit,working_tree_dirty=dirty,files=files,scope='Owner-reference lowercase credit; two pattern tables only, all executable bytes unchanged.'))
    m['reference_credit']=dict(parent_rom_sha256=PARENT,patches=patches,word='retroworks',hyphen=False,year=False,right=247,top=182,bottom=188,coarse_shift=1,ids=list(tiles),cells=cells,glyph_size=[4,7],character_pitch=5,executable_bytes_unchanged=True,extra_vram_bytes=0,extra_ram_bytes=0)
    name='frostbite-reference-credit-at.rom';(out/name).write_bytes(rom);m['rom'].update(filename=name,sha256=sha(rom));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n');print(dict(rom_sha256=sha(rom),sources=len(files),patches=len(patches)));return m
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();build(a.base,a.out)
