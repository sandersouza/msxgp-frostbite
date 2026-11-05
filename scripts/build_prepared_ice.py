"""Build direct ice packets in losslessly reclaimed contact-bank tails."""
import argparse
import json
from pathlib import Path
import subprocess

from environment import ROOT,verified_tool
from presentation_band_spike import apply_patch,sha,verified_bytes,COMPANIONS
from render_build import symbols


def build(out,*,direct_enemy=False,lazy_enemy=False,base=None,allocation=None,i_symbols=None):
    if lazy_enemy and not direct_enemy:raise ValueError('lazy enemies require direct-band mode')
    if out.exists():raise ValueError('immutable output directory already exists')
    historical = base is None
    base=ROOT/'outputs/presentation/prepared-bands-p/codec-b' if historical else Path(base)
    rawmeta=verified_bytes(base/'build.json','524a84378bdff9ab69346a444b5b8ba80daefb37791bbdcda148ee167e19d0fd') if historical else (base/'build.json').read_bytes()
    rawsyms=verified_bytes(base/'presentation.sym','233a80b450b3a143ae8dfd951ee35cd31490085a952962ae2481e1f3b39a2ff2') if historical else (base/'presentation.sym').read_bytes()
    proof=ROOT/'outputs/presentation/direct-playfield-i/tables.json'
    allocation=json.loads(verified_bytes(proof,COMPANIONS['i_allocation'])) if allocation is None else json.loads(Path(allocation).read_text())
    if not any(b==7 and a<=0xA10C and z>=0xAA68 for b,a,z in allocation['regions']):
        raise ValueError('uncertified bank7 code range')
    if any(b==7 and a<0xAA68 and a+n>0xA10C for b,a,n in allocation['allocations']):
        raise ValueError('bank7 code overlaps a live allocation')
    meta=json.loads(rawmeta)
    parent=verified_bytes(base/meta['rom']['filename'],'209992bdbbf93ba30729d9cf94b7d8a0f6e1c55ac4c1f8206cecb464aa2e75d8')
    out.mkdir(parents=True)
    (out/'input-meta.json').write_bytes(rawmeta);(out/'input.sym').write_bytes(rawsyms)
    s=symbols(out/'input.sym')
    extra_sources=[]
    if direct_enemy:
        from presentation_direct_enemy import segments
        raw_i=verified_bytes(ROOT/'outputs/presentation/direct-playfield-i/patch.sym',COMPANIONS['i_symbols']) if i_symbols is None else Path(i_symbols).read_bytes()
        (out/'input-i.sym').write_bytes(raw_i)
        s.update({n:v for n,v in symbols(out/'input-i.sym').items() if n.startswith('i_')})
        roles=bytearray()
        for page in range(2):
            for lane in range(4):
                for role in segments(page,lane):
                    roles.extend(role['pgt'].to_bytes(2,'little')+role['key'].to_bytes(2,'little')+bytes([role['tile'],role['water']]))
        (out/'qe-roles.bin').write_bytes(roles)
    def logical(address,size):
        bank=address//16384;physical=bank+3 if bank<11 else bank+242
        if address%16384+size>16384:raise ValueError('cross-bank logical record')
        at=physical*16384+address%16384
        return parent[at:at+size]
    def far(address):
        bank=address//16384;physical=bank+3 if bank<11 else bank+242
        return (0x8000+address%16384).to_bytes(2,'little')+bytes([physical])
    names_pattern=bytes.fromhex('3af0c26f26002929292929')
    at=parent.index(names_pattern,s['p_template_load']-0x4000,s['p_template_load']-0x4000+230)
    names_tail=at+0x4000
    (out/'symbols.inc').write_text('\n'.join(f'{n} EQU ${v:04X}' for n,v in sorted(s.items()) if '.' not in n)
        +f'\npk_names_tail EQU ${names_tail:04X}\n')
    source=ROOT/'src/presentation_prepared_ice.asm'
    entry=source
    if direct_enemy:
        entry=out/'entry.asm'
        entry.write_text('    DEFINE WITH_DIRECT_ENEMY\n'+('    DEFINE WITH_LAZY_ENEMY\n' if lazy_enemy else '')+'    INCLUDE "presentation_prepared_ice.asm"\n')
        extra_sources=[ROOT/'src/presentation_direct_enemy_body.asm',ROOT/'src/presentation_direct_enemy_helpers.asm',ROOT/'scripts/presentation_direct_enemy.py']
    run=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={out}',f'--inc={ROOT/"src"}',
        f'--raw={out/"patch.bin"}',f'--sym={out/"patch.sym"}', f'--lst={out/"patch.lst"}',str(entry)],cwd=ROOT,capture_output=True,text=True)
    (out/'assembler.log').write_text(run.stdout+run.stderr)
    if run.returncode:raise ValueError(run.stdout+run.stderr)
    q=symbols(out/'patch.sym');code=(out/'patch.bin').read_bytes()
    resident=q['pk_resident_end']-q['pk_init'];banked=q['pk_end']-q['pk_load']
    if len(code)!=resident+banked:raise ValueError('unexpected assembler extent')
    rom=bytearray(parent);patches=[]
    def patch(at,old,new):patches.append(apply_patch(rom,at,old,new))
    def ins(op,address):return bytes((op,address&255,address>>8))
    patch(q['pk_init']-0x4000,parent[q['pk_init']-0x4000:q['pk_init']-0x4000+resident],code[:resident])
    at=7*16384+q['pk_load']-0x8000
    patch(at,parent[at:at+banked],code[resident:])
    patch(s['presentation_init']-0x4000,ins(205,0x7F5F),ins(205,q['pk_init']))
    patch(s['p_template_strip_publish.mask']-0x4000,ins(195,0x7E5D),ins(195,q['pk_publish_entry']))
    at=parent.index(ins(205,s['p_template_load']),s['p_fixed_floe_prepare']-0x4000,s['p_template_object_fuse']-0x4000)
    patch(at,ins(205,s['p_template_load']),ins(205,q['pk_load_entry']))
    at=parent.index(ins(205,s['p_fast_old_key']),s['p_template_object_fuse']-0x4000,s['p_template_object_fuse']-0x4000+20)
    patch(at,ins(205,s['p_fast_old_key']),ins(205,q['pk_old_entry']))
    if direct_enemy:
        start=s['presentation_world_prepare.object']-0x4000
        end=s['presentation_world_prepare.floes']-0x4000
        old=ins(205,s['i_primitive'])
        if parent.count(old,start,end)!=1:raise ValueError('unique original enemy hook required')
        at=parent.index(old,start,end)
        patch(at,old,ins(205,q['qe_entry']))
    packets=[]
    codec=meta['tables']['codec']
    if codec['block_bank']!=35 or codec['tree_bank']<=114:
        raise ValueError('packet tail arena differs')
    for index in range(1280):
        pointer=int.from_bytes(logical(s['p_template_template_index_offset']+index*2,2),'little')
        address=s['p_template_template_keys_offset']+pointer
        program,count=logical(address,2)
        if not 1<=count<=14:raise ValueError('invalid complete packet count')
        keys=logical(address+2,count*2)
        ids=[int.from_bytes(keys[i:i+2],'little') for i in range(0,len(keys),2)]
        if any(i>=2049 for i in ids):raise ValueError('raw floe ID outside exact namespace')
        patterns=b''.join(logical(s['p_template_floe_patterns_offset']+i*8,8) for i in ids)
        packet=patterns+bytes(112-len(patterns))+far(address+2)+bytes([count,program])+bytes(11)
        assert len(packet)==128
        bank=35+index//16;cpu=0xB800+index%16*128;at=bank*16384+cpu-0x8000
        if rom[at:at+128]!=b'\xff'*128:raise ValueError('packet target is not reclaimed padding')
        rom[at:at+128]=packet
        packets.append(dict(index=index,bank=bank,address=cpu,count=count,program=program,
                            raw_keys_sha256=sha(keys),pattern_sha256=sha(patterns),packet_sha256=sha(packet)))
    assets=out/'template-assets';assets.mkdir()
    for bank in meta['template_assets']['physical_banks']:
        name=f'assets-{bank:03d}.bin';data=bytes(rom[bank*16384:(bank+1)*16384])
        (assets/name).write_bytes(data)
        meta['template_assets']['files'][name]=sha(data);meta['static_presentation']['files'][name]=sha(data)
    for bank in meta['contact14']['arena']:
        b=bank['bank'];bank['packed_sha256']=sha(rom[b*16384:(b+1)*16384])
    for bank,address,size in allocation['allocations']:
        at=bank*16384+address-0x8000
        if rom[at:at+size]!=parent[at:at+size]:raise ValueError('prepared packets changed a live I allocation')
    (out/'geometry').symlink_to((base/'geometry').resolve(),target_is_directory=True)
    name='frostbite-direct-enemy-q.rom' if direct_enemy else 'frostbite-prepared-ice-p.rom'
    (out/name).write_bytes(rom)
    (out/'presentation.sym').write_text(rawsyms.decode()+'\n'+'\n'.join(f'{n}: EQU 0x{v:08X}' for n,v in q.items() if n.startswith(('pk_','qe_','i_')))+'\n')
    (out/'packets.json').write_text(json.dumps(packets,indent=2)+'\n')
    meta['version']='prepared-ice-p-internal';meta['rom'].update(filename=name,sha256=sha(rom))
    meta['prepared_ice']=dict(parent_rom_sha256=sha(parent),patches=patches,
        resident_bytes=resident,banked_bytes=banked,packet_count=1280,packet_bytes=163840,
        records=[0xC1D1,0xC1F1],colors=[0xC1F1,0xC1F9],scratch=[0xC1F9,0xC1FF],pending=[0xC1C1,0xC1C5],
        sources={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in (Path(__file__).resolve(),source)},
        scope='Internal prepared ice packets, lossless contact14 prerequisite, lazy physical ice keys; unqualified for human delivery.')
    if direct_enemy:
        meta['version']='direct-enemy-q-internal'
        meta['direct_enemy']=dict(ram=[0xE800,0xE880],heap_redzone=[0xE880,0xF340],
            cache=[0xE800,0xE820],banked_end=q['qe_end'],lazy_keys=lazy_enemy,
            sources={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in extra_sources},
            scope='Internal complete physical enemy bands with original geometry, copy/fusion, NAME and simulation semantics; unqualified for human delivery.')
    (out/'build.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(dict(rom_sha256=sha(rom),resident_bytes=resident,banked_bytes=banked,packet_count=1280))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--direct-enemy',action='store_true')
    parser.add_argument('--lazy-enemy',action='store_true')
    args=parser.parse_args();build(args.out.resolve(),direct_enemy=args.direct_enemy,lazy_enemy=args.lazy_enemy)
