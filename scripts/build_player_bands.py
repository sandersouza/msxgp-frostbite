"""Repack normal P0 rectangles with exact source pixels from sealed v25."""
import argparse,json,hashlib,shutil,subprocess
from pathlib import Path
from environment import ROOT,verified_tool
from presentation_player_bands import normal_assets
from render_build import symbols
PARENT='bf5c703d1e607a47bec037a1e5bac0ce32d34539f14e051f69134470d78dae41'
sha=lambda b:hashlib.sha256(b).hexdigest()

def build(base,out,mode='packed'):
    base,out=Path(base).resolve(),Path(out).resolve()
    if out.exists()or mode not in('packed','original'):raise ValueError('fresh output and declared mode required')
    m=json.loads((base/'build.json').read_text());parent=(base/m['rom']['filename']).read_bytes();files=dict(m['source_files'])
    if sha(parent)!=PARENT or len(files)!=191 or any(sha((ROOT/n).read_bytes())!=h for n,h in files.items()):raise ValueError('sealed v25 ROM/source closure differs')
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.name=='geometry':continue
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():shutil.copytree(p,out/p.name)
    (out/'geometry').symlink_to((base/'geometry').resolve(),target_is_directory=True)
    if mode=='original':
        (out/'rollback.json').write_text(json.dumps(dict(complete=True,rom_sha256=PARENT,byte_identical=True),indent=2)+'\n');return m
    a=normal_assets(base);s=symbols(base/'presentation.sym');defs={**s,'AO_CACHE_ENTRY':s['p_player_cache_lookup.entry'],'AO_CACHE_MISS':s['p_player_cache_lookup.miss'],'AO_UPPER':s['p_player_variant_lookup.replace']+3}
    at=2*16384+s['p_player_variant_lookup.replace']-0x8000
    if parent[at:at+3]!=bytes((0xc3,s['x_player_replace']&255,s['x_player_replace']>>8))or s['p_player_variant_uncached']-defs['AO_UPPER']!=23:raise ValueError('retirement-proven unconditional variant redirect differs')
    (out/'symbols.inc').write_text('\n'.join(f'{n} EQU ${v:04X}'for n,v in defs.items()if'.'not in n)+'\n');source=ROOT/'src/presentation_player_bands.asm'
    run=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={out}',f'--raw={out/"player-bands.bin"}',f'--sym={out/"player-bands.sym"}',f'--lst={out/"player-bands.lst"}',str(source)],cwd=ROOT,capture_output=True,text=True);(out/'player-bands-assembler.log').write_text(run.stdout+run.stderr)
    if run.returncode:raise ValueError(run.stdout+run.stderr)
    q=symbols(out/'player-bands.sym');code=(out/'player-bands.bin').read_bytes();tail=s['p_player_variant_default']-defs['AO_CACHE_ENTRY']
    if len(code)!=tail+23 or q['ao_cache_miss']!=defs['AO_CACHE_MISS']or q['ao_cache_store']!=s['p_player_cache_store']or q['ao_upper_end']-q['ao_upper']!=22:raise ValueError('audited cache/gap allocation differs')
    rom=bytearray(parent);patches=[]
    def patch(at,data):
        old=bytes(rom[at:at+len(data)]);rom[at:at+len(data)]=data;patches.append(dict(offset=at,size=len(data),before_sha256=sha(old),after_sha256=sha(data)))
    patch(2*16384+defs['AO_CACHE_ENTRY']-0x8000,code[:tail]);patch(2*16384+defs['AO_UPPER']-0x8000,code[tail:]);patch(146*16384+0x3900,a['descriptors'])
    patch(149*16384+0x3800,a['patterns'][:2048]);patch(148*16384+0x3a60,a['patterns'][2048:])
    for bank in(146,148,149):assert rom[bank*16384:bank*16384+0x3800]==parent[bank*16384:bank*16384+0x3800]
    # Unused old normal-pattern suffix and all adjacent live data stay exact.
    assert rom[148*16384+0x3b20:149*16384]==parent[148*16384+0x3b20:149*16384]
    for bank in(2,146,148,149):
        name=f'assets-{bank:03d}.bin';blob=bytes(rom[bank*16384:(bank+1)*16384])
        for section in('template_assets','static_presentation'):
            if name in m[section]['files']:m[section]['files'][name]=sha(blob);(out/'template-assets'/name).write_bytes(blob)
    for row in m['contact14']['arena']:
        bank=row['bank'];row['packed_sha256']=sha(rom[bank*16384:(bank+1)*16384])
    for p in(Path(__file__),source,ROOT/'scripts/presentation_player_bands.py',ROOT/'tests/test_presentation_player_bands.py'):files[str(p.resolve().relative_to(ROOT))]=sha(p.read_bytes())
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    m.update(version='player-bands-ao-internal',source_commit=commit,source_dirty=dirty,source_files=files,complete_source=dict(commit=commit,working_tree_dirty=dirty,files=files,scope='Exact normal P0 rectangle packing and uniform signed cache displacements; source mechanics/clock/palette/PSG unchanged.'))
    m['player_bands']=dict(parent_rom_sha256=PARENT,mode='packed-player-only',patches=patches,records=72,record_bytes=16,patterns=a['pattern_count'],old_pattern_capacity=137,normal_sprite_count=3,normal_maximum_scanline=2,cache_entry_format='signed startY-minus-cut, cut is maximum start',cache_helper_bank=2,cache_helper_address=q['ao_upper'],cache_helper_bytes=22,retired_gap_bytes=23,new_ram_allocation_bytes=0,new_vram_bytes=0,full_bear=False,scope='Internal phase1 correctness candidate; no full-bear path or performance claim yet.')
    s.update({n:v for n,v in q.items()if n.startswith('ao_')});(out/'presentation.sym').write_text('\n'.join(f'{n}: EQU 0x{v:08X}'for n,v in s.items())+'\n');(out/'player-band-records.bin').write_bytes(a['descriptors']);(out/'player-band-patterns.bin').write_bytes(a['patterns']);(out/'player-bands-model.json').write_text(json.dumps(a['checks'],indent=2)+'\n')
    name='frostbite-player-bands-ao.rom';(out/name).write_bytes(rom);m['rom'].update(filename=name,sha256=sha(rom));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n');print(dict(rom_sha256=sha(rom),sources=len(files),patterns=a['pattern_count'],cache_helper_bytes=22));return m

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--mode',choices=('packed','original'),default='packed');a=p.parse_args();build(a.base,a.out,a.mode)
