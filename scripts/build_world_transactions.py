"""Compile direct world transactions on the immutable fixed-clock diagnostic."""
import argparse
import json
from pathlib import Path
import subprocess

from environment import ROOT,verified_tool
from presentation_band_spike import apply_patch,sha,verified_bytes,COMPANIONS
from presentation_world_packets import decoded_names,legal_programs,occupancy
from render_build import symbols

T_SHA='29b4588b62d4b44a88401c691512d415b26bdaf559198d889730ee2b49763b1e'


def build(base,chain,out):
    if out.exists():raise ValueError('immutable output already exists')
    meta=json.loads((base/'build.json').read_text())
    parent=verified_bytes(base/meta['rom']['filename'],T_SHA)
    for name,value in meta['source_files'].items():
        if sha((ROOT/name).read_bytes())!=value:raise ValueError('T source changed: '+name)
    out.mkdir(parents=True);rom=bytearray(parent);s=symbols(base/'presentation.sym');patches=[]
    k_input=chain/'k/patch.sym'
    k_raw=verified_bytes(k_input,'18c805cde084eedb30e85b7027cd4a27a2421f1b16733e866a8f25007c5b1fc0')
    (out/'input-k.sym').write_bytes(k_raw)
    s.update({n:v for n,v in symbols(out/'input-k.sym').items() if n.startswith('k_')})
    def patch(at,old,new):patches.append(apply_patch(rom,at,old,new))
    def logical(address,size):
        bank=address//16384;physical=bank+3 if bank<11 else bank+242
        at=physical*16384+address%16384
        if address%16384+size>16384:raise ValueError('cross-bank logical record')
        return parent[at:at+size]
    def empty(bank,address,data):
        at=bank*16384+address-0x8000
        if address<0xb800 or address+len(data)>0xc000:raise ValueError('outside certified empty tail')
        patch(at,b'\xff'*len(data),data)
    programs=[]
    for i in range(1280):
        pointer=int.from_bytes(logical(s['p_template_template_index_offset']+i*2,2),'little')
        programs.append(logical(s['p_template_template_keys_offset']+pointer,1)[0])
    directory=bytearray(8192);records=[];slot=0
    for owner in range(8):
        lane=owner%4;page=owner//4;first=(25,9,35,19)[lane]+page*64;water=129 if lane<2 else 130
        for program in sorted(legal_programs(programs,lane)):
            packed=logical(s['p_template_template_names_offset']+program*32,30)
            data=decoded_names(packed,first,water)
            bank=120+slot//32;address=0xb800+(slot%32)*64;slot+=1
            if bank>=150:raise ValueError('NAME packets exceed available tails')
            empty(bank,address,data)
            at=owner*1024+program*4
            directory[at:at+4]=address.to_bytes(2,'little')+bytes([bank,0])
            records.append(dict(owner=owner,program=program,bank=bank,address=address,sha256=sha(data)))
    for i in range(4):empty(116+i,0xb800,directory[i*2048:(i+1)*2048])
    from presentation_direct_enemy import resident_geometry
    geometry=resident_geometry(parent,s);codes=bytearray()
    for group in range(66):
        lo,hi,bank=geometry['roots']['row'][group]
        at=bank*16384+lo+hi*256-0x8000
        for variant in range(128):
            descriptor=int.from_bytes(parent[at+variant*2:at+variant*2+2],'little')
            cls=geometry['classes'][descriptor>>12];index=descriptor&4095
            if index>=cls['count']:raise ValueError('enemy descriptor outside finite class')
            address=cls['offset']+index*cls['stride']
            data=b''
            for i in range(cls['stride']):data+=logical(address+i,1)
            ids=[int.from_bytes(data[i:i+2],'little') for i in range(0,len(data),2)]
            codes.append(occupancy(ids,cls['columns'],cls['rows']))
    for i in range(0,len(codes),2048):empty(142+i//2048,0xb800,codes[i:i+2048])
    origin=0xe900+meta['fixed_clock']['ram_code_bytes']
    (out/'symbols.inc').write_text('\n'.join(f'{n} EQU ${v:04X}' for n,v in sorted(s.items()) if '.'not in n)+f'\nv_origin EQU ${origin:04X}\nqe_nextrow EQU ${s["qe_body.nextrow"]:04X}\n')
    source=ROOT/'src/presentation_world_transactions.asm'
    run=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={out}',f'--raw={out/"patch.bin"}',f'--sym={out/"patch.sym"}',f'--lst={out/"patch.lst"}',str(source)],cwd=ROOT,capture_output=True,text=True)
    (out/'assembler.log').write_text(run.stdout+run.stderr)
    if run.returncode:raise ValueError(run.stdout+run.stderr)
    q=symbols(out/'patch.sym');code=(out/'patch.bin').read_bytes();oldsize=meta['fixed_clock']['ram_code_bytes'];size=oldsize+len(code)
    if size>1792:raise ValueError('extended fixed-clock code exceeds RAM guard')
    patch(115*16384+0x3800+oldsize,b'\xff'*len(code),code)
    start=s['t_initializer']-0x4000;end=s['t_initializer_end']-0x4000
    old=b'\x01'+oldsize.to_bytes(2,'little')+b'\xed\xb0'
    if parent.count(old,start,end)!=1:raise ValueError('unique kernel-copy bound required')
    at=parent.index(old,start,end);patch(at,old,b'\x01'+size.to_bytes(2,'little')+b'\xed\xb0')
    old=b'\xcd'+s['p_template_decode_names'].to_bytes(2,'little')
    at=parent.index(old,s['k_decode']-0x4000,s['k_name_address']-0x4000)
    patch(at,old,b'\xcd'+q['v_decode'].to_bytes(2,'little'))
    old=b'\xcd'+s['qe_geometry'].to_bytes(2,'little')
    start=7*16384+s['qe_body']-0x8000;end=7*16384+s['qe_body.row']-0x8000
    at=parent.index(old,start,end);patch(at,old,b'\xcd'+q['v_geometry'].to_bytes(2,'little'))
    at=7*16384+s['qe_body.cell']-0x8000
    patch(at,parent[at:at+3],b'\xc3'+q['v_cells'].to_bytes(2,'little'))
    # The private direct decoder consumes the immutable final packet instead
    # of the old packed scratch. Program/count/owner metadata remain unchanged.
    at=s['pk_names']-0x4000
    patch(at,b'\xcd'+s['pk_names_tail'].to_bytes(2,'little'),b'\xc9\x00\x00')
    allocation=json.loads(verified_bytes(chain/'i/tables.json',COMPANIONS['i_allocation']))
    for bank,address,n in allocation['allocations']:
        at=bank*16384+address-0x8000
        if rom[at:at+n]!=parent[at:at+n]:raise ValueError('live inherited allocation changed')
    for kind in ('geometry',): (out/kind).symlink_to((base/kind).resolve(),target_is_directory=True)
    assets=out/'template-assets';assets.mkdir()
    for bank in meta['template_assets']['physical_banks']:
        name=f'assets-{bank:03d}.bin';data=bytes(rom[bank*16384:(bank+1)*16384]);(assets/name).write_bytes(data)
        meta['template_assets']['files'][name]=sha(data);meta['static_presentation']['files'][name]=sha(data)
    for record in meta['contact14']['arena']:
        b=record['bank'];record['packed_sha256']=sha(rom[b*16384:(b+1)*16384])
    name='frostbite-world-v.rom';(out/name).write_bytes(rom)
    (out/'presentation.sym').write_text((base/'presentation.sym').read_text()+'\n'+'\n'.join(f'{n}: EQU 0x{v:08X}' for n,v in q.items() if n.startswith('v_'))+'\n')
    files=dict(meta['source_files'])
    for p in (Path(__file__).resolve(),source,ROOT/'scripts/presentation_world_packets.py'):files[str(p.relative_to(ROOT))]=sha(p.read_bytes())
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    meta.update(version='world-transactions-v-diagnostic',source_commit=commit,source_dirty=dirty,source_files=files,
        complete_source=dict(commit=commit,working_tree_dirty=dirty,files=files,scope='Exact T plus compiled final world NAME transactions.'))
    meta['rom'].update(filename=name,sha256=sha(rom))
    meta['fixed_clock'].update(ram_code_bytes=size,ram_code_sha256=sha(rom[115*16384+0x3800:115*16384+0x3800+size]))
    meta['world_transactions']=dict(parent_rom_sha256=T_SHA,patches=patches,ready_name_packets=records,occupancy_bytes=len(codes),occupancy_sha256=sha(codes),k_symbols_sha256=sha(k_raw),ram_code=[origin,origin+len(code)],all_inherited_allocations_preserved=True)
    (out/'build.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(dict(rom_sha256=sha(rom),ram_code_bytes=size,name_packets=len(records)))
    return meta

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--chain',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.base.resolve(),a.chain.resolve(),a.out.resolve())
