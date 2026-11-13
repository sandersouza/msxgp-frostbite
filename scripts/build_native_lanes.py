"""Build the coherent native lane diagnostic from the immutable W control.

Original ROM inputs and compiled graphics remain local-only. Every patch checks
its prior bytes; the selected artifact can be rebuilt without research outputs
other than the declared, verified W parent.
"""
import argparse,json,subprocess
from pathlib import Path
from environment import ROOT,verified_tool
from presentation_band_spike import apply_patch,sha,verified_bytes
from render_build import symbols
from presentation_player_recipes import compile_recipes

PARENT='98904b6bb592f78964158d154545764eda0e986c9c979196d60e9a7ed03f30b4'
SELECTED='b92478f778a57c70e152497e92102637879248fefac7a9161a9f196928a2c0dc'

def build(base,out):
    if out.exists():raise ValueError('immutable output exists')
    meta=json.loads((base/'build.json').read_text())
    parent=verified_bytes(base/meta['rom']['filename'],PARENT)
    for name,value in meta['source_files'].items():
        if sha((ROOT/name).read_bytes())!=value:raise ValueError('parent source differs: '+name)
    out.mkdir(parents=True)
    s=symbols(base/'presentation.sym');rom=bytearray(parent);patches=[];sources=[]
    def ins(op,address):return bytes((op,address&255,address>>8))
    def patch(at,old,new):patches.append(apply_patch(rom,at,old,new))
    def data(bank,address,blob):patch(bank*16384+address-0x8000,b'\xff'*len(blob),blob)
    def assemble(stem,filename,defs):
        source=ROOT/'src'/filename;sources.append(source)
        (out/'symbols.inc').write_text('\n'.join(f'{n} EQU ${v:04X}' for n,v in sorted(defs.items()) if '.'not in n)+'\n')
        result=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={out}',f'--raw={out/(stem+".bin")}',f'--sym={out/(stem+".sym")}',f'--lst={out/(stem+".lst")}',str(source)],cwd=ROOT,capture_output=True,text=True)
        (out/(stem+'-assembler.log')).write_text(result.stdout+result.stderr)
        if result.returncode:raise ValueError(result.stdout+result.stderr)
        return (out/(stem+'.bin')).read_bytes(),symbols(out/(stem+'.sym'))
    code,q=assemble('world','presentation_native_lanes.asm',s)
    assert len(code)==q['x_world_end']-0xf400<=1280
    # Bank147:B800 is a preserved empty tail after contact14 packing, untouched by V/W.
    assert parent[147*16384+0x3800:148*16384]==b'\xff'*2048
    patch(147*16384+0x3800,b'\xff'*len(code),code)
    patch(s['presentation_world_prepare.template_floes']-0x4000,ins(205,s['p_fixed_floe_prepare']),ins(195,q['x_world']))
    # Each immutable ice packet already reserves11zero bytes after program116.
    # Encode the two legal page-specific NAME far pointers; no pattern/key changes.
    for index in range(1280):
     phase=index//160;lane=(0,3,3,2,2,1,1,0)[phase]
     at=(35+index//16)*16384+0x3800+index%16*128
     program=parent[at+116];payload=bytearray()
     for page in (0,1):
      owner=lane+page*4;directory=(116+owner//2)*16384+0x3800+(owner%2)*1024+program*4
      ptr=parent[directory:directory+3];assert len(ptr)==3 and ptr[2]
      payload.extend(ptr)
     patch(at+117,bytes(6),payload)
    # Preserve stable SAT actors even if NAME dirtiness is empty.
    start=s['presentation_world_prepare']-0x4000
    at=parent.index(bytes.fromhex('b0c8af32'),start,start+80)
    patch(at,bytes.fromhex('b0c8af'),ins(205,q['x_world_dirty']))
    # Suppress only the independent actor contribution, before union with floes.
    start=2*16384+(s['p_dirty_describe.object']&16383)
    end=2*16384+(s['p_dirty_describe.floe']&16383)
    at=parent.index(ins(205,s['p_template_dirty_object']),start,end)
    patch(at,ins(205,s['p_template_dirty_object']),ins(205,q['x_actor_dirty_gate']))
    # Hardware enemy prototype: resident gates plus dead-bank7 native chooser.
    (out/'world-addresses.inc').write_text('\n'.join(f'{n} EQU ${v:04X}' for n,v in q.items() if n.startswith('x_') and '.' not in n)+'\n')
    hcode,hq=assemble('hybrid','presentation_native_enemies.asm',s)
    assert len(hcode)<=0xaa68-0xa50d
    assert s['qe_end']==0xa50d
    patch(7*16384+0x250d,parent[7*16384+0x250d:7*16384+0x250d+len(hcode)],hcode)
    # Obsolete decoder pair table is unreachable after native x_floe replacement.
    pool=bytearray()
    for group in range(66):
     for parity in range(2):
      idx=(group*16+parity)*3;at=s['i_packets_bank']*16384+(s['i_packets']&16383)+idx
      pointer=int.from_bytes(parent[at:at+2],'little');bank=parent[at+2]
      at=bank*16384+((pointer&0xfffe)&16383);packet=parent[at:at+24]
      assert pointer&1 or packet[16:]==bytes(8),(group,parity,packet.hex())
      pool+=packet[:8]+bytes(8)+packet[8:16]+bytes(8)
    assert len(pool)==4224 and parent[255*16384+0x2400:255*16384+0x2480]==b'\xff'*128
    patch(255*16384+0x1400,parent[255*16384+0x1400:255*16384+0x2480],pool)
    # Patch only the producer call sites, preserving the fixed-clock snapshot call.
    start=s['presentation_prepare']-0x4000;end=s['presentation_commit']-0x4000
    for name,target in [('p_dirty_describe',q['x_prepare_sat']),('p_fast_release_dirty',q['x_force_rows']),('presentation_world_prepare',q['x_pipeline'])]:
     old=ins(205,s[name]);positions=[at for at in range(start,end) if parent[at:at+3]==old];assert len(positions)==1
     patch(positions[0],old,ins(205,target))
    for name in ['presentation_sprites_prepare']:
     old=ins(205,s[name]);positions=[at for at in range(start,end) if parent[at:at+3]==old];assert len(positions)==1
     patch(positions[0],old,b'\0'*3)
    at=2*16384+(s['p_player_variant_lookup.next']&16383)+4
    patch(at,b'\xfe\x04',b'\xfe\x03')
    at=2*16384+(s['p_player_variant_lookup.replace']&16383)
    patch(at,parent[at:at+3],ins(195,q['x_player_replace']))
    q.update({n:v for n,v in hq.items() if n.startswith('x_')})

    world_q=dict(q);world_size=len(code)
    palette_at=115*16384+0x3800+s['w_palette']-0xe900
    palette=parent[palette_at:palette_at+256]
    source_rom=verified_bytes(ROOT/'references/roms/frostbite.bin','cbfdad89480def69d922adf16a1d89d55a6cb515929edf74e5bea884c9fb7834')
    desc,patterns,proof=compile_recipes(source_rom,palette)
    (out/'player-descriptors.bin').write_bytes(desc);(out/'player-patterns.bin').write_bytes(patterns)
    (out/'player-finite-domain.json').write_text(json.dumps(proof,indent=2)+'\n')
    assert len(desc)==1152 and len(patterns)==4384
    data(146,0xb900,desc);data(149,0xb800,patterns[:2048]);data(148,0xba60,patterns[2048:3488]);data(147,0xbd00,patterns[3488:4256]);data(146,0xbd80,patterns[4256:])
    oldsize=meta['fixed_clock']['ram_code_bytes']
    player,pq=assemble('player','presentation_player_recipes.asm',{**s,'x_origin':0xe900+oldsize,'x_resume':s['p_player_prepare']+7})
    size=oldsize+len(player);assert size<=1792
    data(115,0xb800+oldsize,player)
    lo,hi=s['t_initializer']-0x4000,s['t_initializer_end']-0x4000
    needle=ins(1,oldsize)+b'\xed\xb0';assert parent.count(needle,lo,hi)==1
    patch(parent.index(needle,lo,hi),ins(1,oldsize),ins(1,size))
    patch(2*16384+s['p_player_prepare']+4-0x8000,ins(0x21,s['p_p_planes']),ins(0xc3,pq['x_try']))
    bg,bq=assemble('background','presentation_native_background.asm',{**s,'xh_collect_resume':s['p_fast_collect_rows']+3,'xh_dirty_resume':s['p_fast_row_dirty']+3,'xh_igloo_next':s['p_fast_igloo_prepare.next_row'],'xh_igloo_continue':s['p_fast_igloo_prepare.bottom']+3})
    assert len(bg)<=608;data(148,0xb800,bg)
    patch(s['p_fast_collect_rows']-0x4000,ins(0x11,s['p_fd_list']),ins(0xc3,bq['xh_collect']))
    patch(s['p_fast_row_dirty']-0x4000,bytes.fromhex('c5d5e5'),ins(0xc3,bq['xh_dirty']))
    patch(s['p_fast_background_rows']-0x4000,ins(0x3a,s['p_fd_count']),ins(0xc3,bq['xh_bg']))
    patch(s['p_fast_igloo_prepare.bottom']-0x4000,ins(0x32,s['pfh_bottom']),ins(0xc3,bq['xh_igloo_bottom']))
    at=147*16384+0x3800+world_q['x_row_dirty']-0xf400
    patch(at,rom[at:at+3],ins(0xc3,bq['xh_dirty']))
    header,hq=assemble('header','presentation_sparse_header.asm',s)
    assert len(header)<=512;data(146,0xbe00,header)
    begin=s['w_header_resume'];end=s['p_fast_header_glyph'];assert (begin,end)==(0x6693,0x66fa)
    header_loader=begin+3
    init=ins(0xcd,s['qe_init'])+bytes((0x3e,146))+ins(0xcd,s['t_mapper'])+ins(0x21,0xbe00)+ins(0x11,0xfd00)+ins(1,len(header))+bytes.fromhex('edb0c9')
    body=ins(0xc3,hq['xh_header'])+init
    patch(begin-0x4000,parent[begin-0x4000:end-0x4000],body+bytes(end-begin-len(body)))
    auxiliary=[]
    for bank,address,length in ((147,0xf400,world_size),(148,0xf900,len(bg)),(146,0xfd00,len(header))):
        origin=0xbe00 if bank==146 else 0xb800
        at=bank*16384+origin-0x8000
        auxiliary.append(dict(bank=bank,rom_address=origin,ram_address=address,size=length,sha256=sha(rom[at:at+length])))
    loader=ins(0xcd,header_loader)
    for row in auxiliary[:2]:
        loader+=bytes((0x3e,row['bank']))+ins(0xcd,s['t_mapper'])+ins(0x21,row['rom_address'])+ins(0x11,row['ram_address'])+ins(1,row['size'])+bytes.fromhex('edb0')
    loader+=b'\xc9';assert len(loader)<=66
    patch(0x3fbe,b'\xff'*len(loader),loader)
    patch(s['t_initializer']-0x4000,ins(0xcd,s['qe_init']),ins(0xcd,0x7fbe))
    code=rom[147*16384+0x3800:147*16384+0x3800+world_size]
    (out/'world.bin').write_bytes(code)
    for names in (world_q,pq,bq,hq):s.update({n:v for n,v in names.items() if n.startswith(('x_','xh_'))})
    (out/'presentation.sym').write_text('\n'.join(f'{n}: EQU 0x{v:08X}' for n,v in s.items())+'\n')
    (out/'geometry').symlink_to((base/'geometry').resolve(),target_is_directory=True)
    assets=out/'template-assets';assets.mkdir()
    for bank in meta['template_assets']['physical_banks']:
        name=f'assets-{bank:03d}.bin';blob=bytes(rom[bank*16384:(bank+1)*16384]);(assets/name).write_bytes(blob)
        meta['template_assets']['files'][name]=sha(blob)
        if name in meta['static_presentation'].get('files',{}):meta['static_presentation']['files'][name]=sha(blob)
    for row in meta['contact14']['arena']:
        bank=row['bank'];row['packed_sha256']=sha(rom[bank*16384:(bank+1)*16384])
    if sha(rom)!=SELECTED:raise ValueError('promoted source differs from selected measured candidate: '+sha(rom))
    name='frostbite-native-lanes-x.rom';(out/name).write_bytes(rom)
    sources.extend((Path(__file__).resolve(),ROOT/'scripts/presentation_player_recipes.py'))
    files=dict(meta['source_files'])
    for path in sources:files[str(path.relative_to(ROOT))]=sha(path.read_bytes())
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    meta.update(version='native-lanes-x-diagnostic',source_commit=commit,source_dirty=dirty,source_files=files,complete_source=dict(commit=commit,working_tree_dirty=dirty,files=files,scope='Immutable W plus source-built native lanes, bounded enemy sprites, player recipes, sparse header and background.'))
    meta['rom'].update(filename=name,sha256=sha(rom))
    meta['fixed_clock'].update(ram_code_bytes=size,ram_code_sha256=sha(rom[115*16384+0x3800:115*16384+0x3800+size]))
    meta['native_lanes']=dict(parent_rom_sha256=PARENT,patches=patches,auxiliary_code=auxiliary,player_recipe_proof=proof,enemy_pattern_count=132,player_ways_per_page=3,scope='Coherent source snapshots; original gameplay clock unchanged. Development diagnostic, not original-fluidity acceptance.')
    # Compatibility fields for existing passive research guards; same allocation.
    meta['coherent_x']=dict(auxiliary_code=auxiliary,mutable_dirty_row_lookup=[0xfc00,0xfc18])
    meta['world_x']=dict(code_address=0xf400,code_size=world_size,code_sha256=sha(code))
    (out/'build.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(dict(rom_sha256=sha(rom),ram_code_bytes=size,auxiliary_code=auxiliary))
    return meta

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();build(args.base.resolve(),args.out.resolve())
