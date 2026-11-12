"""Add certified igloo color-only publication to the exact v0.0.16 control."""
import argparse
import json
from pathlib import Path
import subprocess

from environment import ROOT,verified_tool
from presentation_band_spike import sha,verified_bytes
from presentation_igloo_colors import compile_colors
from render_build import symbols

PARENT='9d2ee2926bc8de7fd0d22b05e7ad334e76078141bfde997720adfb62414cc77b'
PARENT_SOURCES='6fb6921a503780d869cc670580fe86eb06cdf1f04f2a388550d4e96b58dba581'
BANK=119


def build(base,out):
    base,out=Path(base).resolve(),Path(out).resolve()
    if out.exists():raise ValueError('immutable output exists')
    meta=json.loads((base/'build.json').read_text())
    parent=verified_bytes(base/meta['rom']['filename'],PARENT)
    files=dict(meta['source_files'])
    if len(files)!=151 or sha(json.dumps(files,sort_keys=True,separators=(',',':')).encode())!=PARENT_SOURCES:
        raise ValueError('v0.0.16 source closure differs')
    if any(sha((ROOT/n).read_bytes())!=h for n,h in files.items()):
        raise ValueError('parent source changed')
    s=symbols(base/'presentation.sym')
    if s['aa_resident_end']!=0x6212 or s['p_template_footer_prepare']!=0x6249:
        raise ValueError('retired typed-header bridge extent changed')
    # Z's dictionary consumes only116..118. X embedded all live NAME pointers
    # in the immutable packets;119:B800..BFFF is retired directory storage.
    dictionary_end=max(x['offset']+x['size'] for x in meta['core_cadence']['dictionary_sections'])
    if dictionary_end>3*2048:raise ValueError('header dictionary reaches bank119')
    pointers=[]
    for index in range(1280):
        at=(35+index//16)*16384+0x3800+index%16*128
        for page in (0,1):
            raw=parent[at+117+page*3:at+120+page*3]
            address=int.from_bytes(raw[:2],'little');bank=raw[2]
            if not 0x8000<=address<0xc000 or not 120<=bank<=145:
                raise ValueError('native NAME program leaves certified allocation')
            pointers.append((bank,address))
    patterns_at=16384+s['p_bg_patterns0_data']-0x8000
    colors_at=16384+s['p_bg_colors0_data']-0x8000
    if meta['background']['tiles_per_bank'][0]!=27:raise ValueError('background domain changed')
    backgrounds={128+i:parent[patterns_at+i*8:patterns_at+(i+1)*8]+parent[colors_at+i*8:colors_at+(i+1)*8] for i in range(27)}
    flags,colors=compile_colors(backgrounds)
    out.mkdir(parents=True)
    (out/'igloo-flags.bin').write_bytes(flags)
    (out/'igloo-colors.bin').write_bytes(colors)
    (out/'symbols.inc').write_text('\n'.join(f'{n} EQU ${v:04X}' for n,v in sorted(s.items()) if '.'not in n)
        +f'\nad_original_publish EQU ${s["p_fixed_put.publish"]:04X}\n')
    source=ROOT/'src/presentation_igloo_colors.asm'
    run=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={out}',
        f'--raw={out/"igloo.bin"}',f'--sym={out/"igloo.sym"}',f'--lst={out/"igloo.lst"}',str(source)],
        cwd=ROOT,capture_output=True,text=True)
    (out/'assembler.log').write_text(run.stdout+run.stderr)
    if run.returncode:raise ValueError(run.stdout+run.stderr)
    q=symbols(out/'igloo.sym');code=(out/'igloo.bin').read_bytes()
    resident=q['ad_resident_end']-q['ad_entry'];banked=q['ad_end']-q['ad_main']
    if q['ad_entry']!=0x6212 or resident>0x6249-0x6212 or q['ad_main']!=0xb800 or banked>2048 or len(code)!=resident+banked:
        raise ValueError('igloo allocation changed')
    def ins(op,address):return bytes((op,address&255,address>>8))
    lo=s['p_fast_igloo_prepare']-0x4000;hi=s['p_fast_igloo_prepare.next_row']-0x4000
    old_call=ins(0xcd,s['p_fast_put'])
    if parent.count(old_call,lo,hi)!=1:raise ValueError('igloo-specific publisher call not unique')
    call_at=parent.index(old_call,lo,hi)
    rom=bytearray(parent);patches=[]
    for at,new in ((q['ad_entry']-0x4000,code[:resident]),(BANK*16384+0x3800,code[resident:]),(call_at,ins(0xcd,q['ad_entry']))):
        old=parent[at:at+len(new)];rom[at:at+len(new)]=new
        patches.append(dict(offset=at,size=len(new),before_sha256=sha(old),after_sha256=sha(new)))
    if rom[s['p_template_footer_prepare']-0x4000:s['p_template_footer_prepare']-0x4000+32]!=parent[s['p_template_footer_prepare']-0x4000:s['p_template_footer_prepare']-0x4000+32]:
        raise ValueError('live footer changed')
    s.update({n:v for n,v in q.items() if n.startswith('ad_')})
    (out/'presentation.sym').write_text('\n'.join(f'{n}: EQU 0x{v:08X}' for n,v in s.items())+'\n')
    for name in ('world.bin','hybrid.bin'):(out/name).write_bytes((base/name).read_bytes())
    (out/'geometry').symlink_to((base/'geometry').resolve(),target_is_directory=True)
    assets=out/'template-assets';assets.mkdir()
    for p in sorted((base/'template-assets').glob('*.bin')):
        (assets/p.name).write_bytes(p.read_bytes())
    bank_image=bytes(rom[BANK*16384:(BANK+1)*16384])
    (assets/f'assets-{BANK:03d}.bin').write_bytes(bank_image)
    for section in ('template_assets','static_presentation'):
        name=f'assets-{BANK:03d}.bin'
        if name in meta[section]['files']:meta[section]['files'][name]=sha(bank_image)
    for row in meta['contact14']['arena']:
        bank=row['bank'];row['packed_sha256']=sha(rom[bank*16384:(bank+1)*16384])
    additions=(source,Path(__file__).resolve(),ROOT/'scripts/presentation_igloo_colors.py')
    for p in additions:files[str(p.relative_to(ROOT))]=sha(p.read_bytes())
    if len(files)!=154:raise ValueError('154 additive sources expected')
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    scope='Verified v0.0.16 plus scoped igloo exact-hit/color-only publication; unchanged full fallback, original clock/input/audio and coherent snapshots.'
    meta.update(version='igloo-colors-ad-diagnostic',source_commit=commit,source_dirty=dirty,
        source_files=files,complete_source=dict(commit=commit,working_tree_dirty=dirty,files=files,scope=scope))
    meta['igloo_colors']=dict(parent_rom_sha256=PARENT,patches=patches,
        resident_half_open=[q['ad_entry'],q['ad_resident_end']],bank=BANK,
        banked_half_open=[q['ad_main'],q['ad_end']],code_bytes=q['ad_code_end']-q['ad_main'],
        colors_sha256=sha(colors),flags_sha256=sha(flags),certified_backgrounds=[128+i for i in range(27) if flags[i]],
        native_name_far_pointers_verified=len(pointers),header_dictionary_bytes=dictionary_end,
        exact_igloo_callsite=call_at+0x4000,new_ram_bytes=0,new_vram_bytes=0,
        exported_bank_image_sha256=sha(bank_image),scope=scope)
    name='frostbite-igloo-colors-ad.rom';(out/name).write_bytes(rom)
    meta['rom'].update(filename=name,sha256=sha(rom))
    (out/'build.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(dict(rom_sha256=sha(rom),source_files=len(files),resident_bytes=resident,
        banked_bytes=banked,source_commit=commit,source_dirty=dirty))
    return meta

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();build(args.base,args.out)
