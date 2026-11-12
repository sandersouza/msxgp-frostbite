"""Add the optional grid24 view to sealed v0.0.17; original mode is exact rollback."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from environment import ROOT,verified_tool
from presentation_band_spike import sha,verified_bytes
from presentation_grid24 import anchor,delta_table,names,span
from render_build import symbols

PARENT='c50a3131df056011af9a037b58624d9de84930b3474579b24d2137d736e9d562'

def build(base,out,layout='grid24',name_mode='prepared'):
    base,out=Path(base).resolve(),Path(out).resolve()
    if layout not in('original','grid24')or out.exists():raise ValueError('new output and declared layout required')
    if name_mode not in ('translated','prepared'):raise ValueError('declared NAME strategy required')
    m=json.loads((base/'build.json').read_text());parent=verified_bytes(base/m['rom']['filename'],PARENT)
    files=dict(m['source_files'])
    if len(files)!=154 or any(sha((ROOT/n).read_bytes())!=h for n,h in files.items()):raise ValueError('v17 parent source closure changed')
    out.mkdir(parents=True)
    if layout=='original':
        for p in base.iterdir():
            if p.name=='geometry':continue
            if p.is_file():shutil.copyfile(p,out/p.name)
            elif p.is_dir():shutil.copytree(p,out/p.name)
        (out/'geometry').symlink_to((base/'geometry').resolve(),target_is_directory=True)
        (out/'rollback.json').write_text(json.dumps(dict(complete=True,layout='original',rom_sha256=PARENT,byte_identical=True,builder_sha256=sha(Path(__file__).read_bytes())),indent=2)+'\n')
        print(dict(layout=layout,rom_sha256=PARENT,byte_identical=True));return m
    s=symbols(base/'presentation.sym');rom=bytearray(parent);patches=[]
    if(s['ad_resident_end'],s['ad_end'],s['p_template_footer_prepare'])!=(0x6235,0xbc91,0x6249):raise ValueError('free bridge/helper allocation changed')
    def ins(op,address):return bytes((op,address&255,address>>8))
    def patch(at,new):
        if any(at<r['offset']+r['size']and r['offset']<at+len(new)for r in patches):raise ValueError('overlapping patch')
        old=bytes(rom[at:at+len(new)]);rom[at:at+len(new)]=new
        patches.append(dict(offset=at,size=len(new),before_sha256=sha(old),after_sha256=sha(new)))
    def assemble(stem,filename):
        (out/'symbols.inc').write_text('\n'.join(f'{n} EQU ${v:04X}'for n,v in s.items()if '.'not in n)+f'\nGRID_PREPARED_NAMES EQU {int(name_mode=="prepared")}\n')
        source=ROOT/'src'/filename
        r=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={out}',f'--raw={out/(stem+".bin")}',f'--sym={out/(stem+".sym")}',f'--lst={out/(stem+".lst")}',str(source)],cwd=ROOT,capture_output=True,text=True)
        (out/(stem+'-assembler.log')).write_text(r.stdout+r.stderr)
        if r.returncode:raise ValueError(r.stdout+r.stderr)
        files[str(source.relative_to(ROOT))]=sha(source.read_bytes())
        return(out/(stem+'.bin')).read_bytes(),symbols(out/(stem+'.sym'))
    floe,q=assemble('grid-floe','presentation_grid_floe.asm')
    if len(floe)!=0xf5d2-0xf43d:raise ValueError('floe RAM allocation changed')
    patch(147*16384+0x383d,floe)
    (out/'grid-deltas.bin').write_bytes(delta_table())
    player,z=assemble('grid-player','presentation_grid_player.asm')
    bridge=z['ag_bridge_end']-z['ag_player_entry'];banked=z['ag_player_bank_end']-z['ag_player']
    if bridge>20 or banked!=0xc000-0xbc91 or len(player)!=bridge+banked:raise ValueError('player allocation changed')
    patch(0x6235-0x4000,player[:bridge]);patch(119*16384+0x3c91,player[bridge:])
    # Declared eight-band anchors; source shore/bear/footer coarse state stays live.
    patch(s['aa_y']-0x4000,bytes(anchor('floe',i)for i in range(4)))
    row_at=s['p_world_row_offsets']-0x4000
    if parent[row_at:row_at+4]!=bytes((0,230,204,178)):raise ValueError('source pitch differs')
    patch(row_at,bytes((0,232,208,184)))
    # Only the new complete floe NAME rows may skip the background fill.
    # The old coverage tables reserve rows at the former 26-pixel pitch.
    cover=bytearray([255]*24)
    for lane in range(4):cover[anchor('floe',lane)//8]=lane
    for name in ('p_template_cover_normal','p_template_cover_coarse'):
        patch(s[name]-0x4000,cover)
    at=s['p_world_row_y']-0x4000;end=s['p_world_nibble']-0x4000
    needle=ins(0x3a,s['p_w_coarse']);positions=[p for p in range(at,end)if parent[p:p+3]==needle]
    if len(positions)!=1:raise ValueError('row coarse load not unique')
    patch(positions[0],bytes.fromhex('af0000'))
    # Native actor and independent current-picture eligibility preflight.
    lo=147*16384+0x3800+s['x_actor']-0xf400;hi=147*16384+0x3800+s['x_row_dirty']-0xf400
    positions=[p for p in range(lo,hi)if parent[p:p+2]==b'\xc6\x99']
    if len(positions)!=1:raise ValueError('actor anchor not unique')
    patch(positions[0],b'\xc6\x98')
    positions=[p for p in range(lo,hi)if parent[p:p+3]==needle]
    if len(positions)!=1:raise ValueError('actor segment selector not unique')
    patch(positions[0],bytes.fromhex('af0000'))
    lo=7*16384+s['x_preflight']-0x8000;hi=7*16384+s['x_apply_invalid']-0x8000
    positions=[p for p in range(lo,hi)if parent[p:p+2]==b'\xc6\x99']
    if len(positions)!=1:raise ValueError('preflight anchor not unique')
    patch(positions[0],b'\xc6\x98')
    # Three live bank7 coarse uses: generic segment, cache key and lane1 copy.
    # v17's qe_generate/qe_fuse use resident prepared-packet trampolines.
    lo=7*16384+s['qe_primitive']-0x8000;hi=7*16384+s['qe_end']-0x8000
    positions=[p for p in range(lo,hi)if parent[p:p+3]==needle]
    if len(positions)!=3:raise ValueError('actor coarse uses differ')
    for at in positions:patch(at,bytes.fromhex('af0000'))
    at=7*16384+s['qe_roles_data']-0x8000
    roles=bytearray(parent[at:at+96])
    for page in range(2):
        p=(page*4+1)*12;roles[p:p+12]=roles[p+6:p+12]+roles[p:p+6]
    patch(at,roles)
    for kind,name in[('enemy','p_template_object_spans'),('floe','p_template_floe_spans')]:
        patch(s[name]-0x4000,b''.join(span(kind,i)for c in range(2)for i in range(4)))
    masks=bytearray()
    for bits in range(16):
        pair=[0,0]
        for lane in range(4):
            if bits&(1<<lane):
                flags=span('enemy',lane);pair=[a|b for a,b in zip(pair,flags[1:])]
        masks.extend(pair)
    patch(7*16384+s['x_dirty_masks']-0x8000,masks)
    lo=2*16384+s['presentation_sprites_prepare']-0x8000;hi=2*16384+s['p_s_finish']-0x8000
    needle=ins(0xcd,s['ys_static']);positions=[p for p in range(lo,hi)if parent[p:p+3]==needle]
    if len(positions)!=1:raise ValueError('pre-static hook not unique')
    patch(positions[0],ins(0xcd,z['ag_player_entry']))
    # Verify every reused phase0 NAME program independently, both page domains.
    checked=0
    programs={bank:bytearray(2048)for bank in range(45,65)}
    for i in range(160):
        at=(35+i//16)*16384+0x3800+i%16*128
        for page in range(2):
            raw=parent[at+117+page*3:at+120+page*3];address=int.from_bytes(raw[:2],'little');bank=raw[2]
            data=parent[bank*16384+address-0x8000:bank*16384+address-0x8000+30]
            for lane in range(4):
                if name_mode=='prepared':
                    # Only old nonzero-phase packet tails are retired. Contact14's
                    # speculative B800 read is masked from the decoded28-bit value.
                    bank=45+2*(i//16)+(i%16)//8
                    offset=((i%8)*8+page*4+lane)*32
                    programs[bank][offset:offset+32]=names(data,lane,page,0)+bytes(2)
                for rotation in range(0,30,3):names(data,lane,page,rotation);checked+=1
    if name_mode=='prepared':
        for bank,payload in programs.items():patch(bank*16384+0x3800,payload)
        if rom[35*16384:45*16384]!=parent[35*16384:45*16384]:
            raise ValueError('live phase0 pattern/owner packets changed')
        for bank in programs:
            lo=bank*16384
            if rom[lo:lo+0x3800]!=parent[lo:lo+0x3800]:
                raise ValueError('contact14 lower14KiB changed')
    s.update({n:v for n,v in q.items()if n.startswith('ag_')})
    s.update({n:v for n,v in z.items()if n.startswith('ag_')})
    for n in list(s):
        if n.startswith('aa_floe.'):del s[n]
    s['x_floe']=s['aa_floe']=q['ag_floe'];s['aa_floe_end']=q['ag_floe_end']
    world=bytes(rom[147*16384+0x3800:147*16384+0x3800+1240]);(out/'world.bin').write_bytes(world)
    (out/'hybrid.bin').write_bytes(bytes(rom[7*16384+s['x_hybrid']-0x8000:7*16384+s['x_hybrid_end']-0x8000]))
    (out/'geometry').symlink_to((base/'geometry').resolve(),target_is_directory=True)
    assets=out/'template-assets';assets.mkdir()
    for p in(base/'template-assets').glob('*.bin'):shutil.copyfile(p,assets/p.name)
    changed={p['offset']//16384 for p in patches}
    for bank in changed:
        name=f'assets-{bank:03d}.bin';image=bytes(rom[bank*16384:(bank+1)*16384])
        if name in m['template_assets']['files']or name in m['static_presentation']['files']:
            (assets/name).write_bytes(image)
        for section in('template_assets','static_presentation'):
            if name in m[section]['files']:m[section]['files'][name]=sha(image)
    for section in('coherent_x','native_lanes'):
        for row in m[section]['auxiliary_code']:
            if row['ram_address']==0xf400:row['sha256']=sha(world)
    m['world_x']['code_sha256']=sha(world)
    for row in m['contact14']['arena']:
        bank=row['bank'];row['packed_sha256']=sha(rom[bank*16384:(bank+1)*16384])
    for path in(Path(__file__).resolve(),ROOT/'scripts/presentation_grid24.py',
                ROOT/'scripts/presentation_grid24_check.py',ROOT/'tests/test_presentation_grid24.py'):
        files[str(path.relative_to(ROOT))]=sha(path.read_bytes())
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    m.update(version='grid24-af-diagnostic',source_commit=commit,source_dirty=dirty,source_files=files)
    m['complete_source']=dict(commit=commit,working_tree_dirty=dirty,files=files,scope='Additive optional grid24 view; original mode copies sealed v17 bytes.')
    m['grid24']=dict(view='grid24-v1',name_mode=name_mode,parent_rom_sha256=PARENT,patches=patches,new_ram_bytes=0,new_vram_bytes=0,
        enemy_y=[anchor('enemy',i)for i in range(4)],floe_y=[anchor('floe',i)for i in range(4)],phase0_name_cases=checked,
        player_delta_sha256=sha(delta_table()),rollback='--layout original; exact sealed v0.0.17 ROM',scope='Only presentation anchors/player translation changed. Source mechanics, colors, shapes and clock unchanged.')
    (out/'presentation.sym').write_text('\n'.join(f'{n}: EQU 0x{v:08X}'for n,v in s.items())+'\n')
    name='frostbite-grid24-af.rom';(out/name).write_bytes(rom);m['rom'].update(filename=name,sha256=sha(rom))
    (out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    print(dict(rom_sha256=sha(rom),source_files=len(files),name_cases=checked,patches=len(patches)))
    return m

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--layout',choices=('original','grid24'),default='grid24');p.add_argument('--name-mode',choices=('translated','prepared'),default='prepared');a=p.parse_args();build(a.base,a.out,a.layout,a.name_mode)
