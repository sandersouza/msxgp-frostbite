"""Build W player palette/selective header diagnostic on immutable V."""
import argparse,json,subprocess
from pathlib import Path
from environment import ROOT,verified_tool
from presentation_band_spike import apply_patch,sha,verified_bytes
from render_build import symbols

PARENT='fbf81a5eafa536f95497be22c787812046cf59a38eb962ee28230b3fc8f9ec99'

def build(base,out):
    if out.exists():raise ValueError('immutable output exists')
    meta=json.loads((base/'build.json').read_text())
    parent=verified_bytes(base/meta['rom']['filename'],PARENT)
    for name,value in meta['source_files'].items():
        if sha((ROOT/name).read_bytes())!=value:raise ValueError('parent source differs: '+name)
    s=symbols(base/'presentation.sym');out.mkdir(parents=True)
    palette=bytearray(parent[2*16384+s['p_sprite_colors_data']-0x8000:2*16384+s['p_sprite_colors_data']-0x8000+256])
    for code,color in ((0x16,11),(0x24,10),(0x36,11)):
        palette[code]=palette[code+1]=color
    (out/'normal-palette.bin').write_bytes(palette)
    def ins(op,address):return bytes((op,address&255,address>>8))
    def unique(needle,start,end):
        lo,hi=start-0x4000,end-0x4000
        if parent.count(needle,lo,hi)!=1:raise ValueError('nonunique header hook')
        return parent.index(needle,lo,hi)+0x4000
    pack=s['p_template_header_keys.column'];tile=s['p_fast_header_prepare.column']
    pack_advance=unique(bytes.fromhex('110300dd19'),pack,s['p_template_header_key'])
    tile_advance=unique(ins(0xcd,s['p_fixed_put_header'])+ins(0xda,s['p_world_fail']),tile,s['p_fast_header_glyph'])+6
    defs=dict(w_origin=0xe900+meta['fixed_clock']['ram_code_bytes'],
        w_header_resume=s['p_fast_header_prepare.rows']+3,w_pack_resume=pack+3,
        w_pack_advance=pack_advance,w_tile_resume=tile+3,w_tile_advance=tile_advance)
    (out/'symbols.inc').write_text('\n'.join(f'{n} EQU ${v:04X}' for n,v in sorted({**s,**defs}.items()) if '.'not in n)+'\n')
    source=ROOT/'src/presentation_header_reuse.asm'
    run=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={out}',f'--raw={out/"patch.bin"}',f'--sym={out/"patch.sym"}',f'--lst={out/"patch.lst"}',str(source)],cwd=ROOT,capture_output=True,text=True)
    (out/'assembler.log').write_text(run.stdout+run.stderr)
    if run.returncode:raise ValueError(run.stdout+run.stderr)
    q=symbols(out/'patch.sym');code=(out/'patch.bin').read_bytes();rom=bytearray(parent);patches=[]
    def patch(at,old,new):patches.append(apply_patch(rom,at,old,new))
    oldsize=meta['fixed_clock']['ram_code_bytes'];size=oldsize+len(code)
    if size>1792:raise ValueError('RAM code exceeds guard')
    patch(115*16384+0x3800+oldsize,b'\xff'*len(code),code)
    at=unique(ins(1,oldsize)+b'\xed\xb0',s['t_initializer'],s['t_initializer_end'])-0x4000
    patch(at,ins(1,oldsize),ins(1,size))
    patch(s['p_fast_header_prepare.rows']-0x4000,ins(0xcd,s['p_template_header_keys']),ins(0xc3,q['w_header']))
    patch(pack-0x4000,bytes.fromhex('dd7e00'),ins(0xc3,q['w_pack_gate']))
    patch(tile-0x4000,ins(0xcd,s['p_template_header_key']),ins(0xc3,q['w_tile_gate']))
    patch(s['p_fast_header_glyph']-0x4000-3,ins(0xc3,s['p_fast_igloo_prepare']),ins(0xc3,q['w_save']))
    for addr in (0xad75,0xafe4):
        patch(2*16384+addr-0x8000,bytes.fromhex('26b77e'),ins(0xcd,q['w_player_color']))
    patch(2*16384+s['p_player_prepare']-0x8000,ins(0xcd,s['p_player_cache_lookup']),ins(0xcd,q['w_player_setup']))
    for name in ('geometry','template-assets'):(out/name).symlink_to((base/name).resolve(),target_is_directory=True)
    name='frostbite-header-palette-w.rom';(out/name).write_bytes(rom)
    (out/'presentation.sym').write_text((base/'presentation.sym').read_text()+'\n'+'\n'.join(f'{n}: EQU 0x{v:08X}' for n,v in q.items() if n.startswith('w_'))+'\n')
    files=dict(meta['source_files'])
    for p in (Path(__file__).resolve(),source,ROOT/'scripts/presentation_player_palette.py'):files[str(p.relative_to(ROOT))]=sha(p.read_bytes())
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    meta.update(version='header-palette-w-diagnostic',source_commit=commit,source_dirty=dirty,source_files=files,
        complete_source=dict(commit=commit,working_tree_dirty=dirty,files=files,scope='Exact V plus player-only palette and selective header columns.'))
    meta['rom'].update(filename=name,sha256=sha(rom))
    meta['fixed_clock'].update(ram_code_bytes=size,ram_code_sha256=sha(rom[115*16384+0x3800:115*16384+0x3800+size]))
    for record in meta['contact14']['arena']:
        bank=record['bank'];record['packed_sha256']=sha(rom[bank*16384:(bank+1)*16384])
    meta['header_reuse']=dict(parent_rom_sha256=PARENT,patches=patches,cache=[0xe840,0xe867],validity=90,
        identity='12 raw glyphs + 3 mapped colors + level>=20; independent physical pages')
    meta['player_palette']=dict(normal_overrides={'22':11,'36':10,'54':11},condition='EB==0 and F0==0',scope='Player only, including shore path; terminal colors unchanged.')
    (out/'build.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(dict(rom_sha256=sha(rom),ram_code_bytes=size))
    return meta

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.base.resolve(),a.out.resolve())
