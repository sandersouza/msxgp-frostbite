"""Materialize native region preparation atop a reproduced, authenticated Q-E."""
import argparse
import json
from pathlib import Path
import subprocess

from environment import ROOT,verified_tool
from presentation_band_spike import apply_patch,sha,verified_bytes,COMPANIONS
from presentation_region_pipeline import igloo_records,record_address
from render_build import symbols

PARENT='2654da3abdb2fc2624f6485a9104327447e0493f64a864feb56b41212dc5ada9'


def build(base,out,*,allocation=None):
    if out.exists():raise ValueError('immutable output already exists')
    meta=json.loads((base/'build.json').read_text());parent=verified_bytes(base/meta['rom']['filename'],PARENT)
    if 'complete_source' not in meta:raise ValueError('reproduced corresponding source chain required')
    for name,value in meta['complete_source']['files'].items():
        if sha((ROOT/name).read_bytes())!=value:raise ValueError('parent corresponding source changed: '+name)
    allocation=Path(allocation) if allocation else base.parent/'i/tables.json'
    inherited=json.loads(verified_bytes(allocation,COMPANIONS['i_allocation']))
    s=symbols(base/'presentation.sym');out.mkdir(parents=True)
    def resident(bank,address,size):
        at=bank*16384+address-32768
        if not 32768<=address<address+size<=49152:raise ValueError('bank-local ROM range required')
        return parent[at:at+size]
    patterns=resident(1,s['p_bg_patterns0_data'],27*8)
    colors=resident(1,s['p_bg_colors0_data'],27*8)
    backgrounds=[patterns[i*8:i*8+8]+colors[i*8:i*8+8] for i in range(27)]
    rows=resident(1,s['p_bg_rows_data'],4*72)
    gradient=resident(1,s['p_bg_gradient_data'],meta['background']['gradient_profiles']*4)
    reachable={128}|{rows[t*72+y*3+2] for t in range(4) for y in (3,4,5)}|set(gradient[1::2])
    records,mapping=igloo_records(backgrounds,{value-128 for value in reachable})
    (out/'igloo-records.bin').write_bytes(records);(out/'igloo-map.bin').write_bytes(mapping)
    source=ROOT/'src/presentation_region_pipeline.asm'
    (out/'symbols.inc').write_text('\n'.join(f'{n} EQU ${v:04X}' for n,v in sorted(s.items()) if '.'not in n)
        +f'\nr_init_origin EQU ${s["pk_resident_end"]:04X}\nr_original_scan EQU ${s["p_player_variant_lookup.scan"]:04X}\nr_background_count EQU 27\n')
    run=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={out}',
        f'--raw={out/"patch.bin"}',f'--sym={out/"patch.sym"}',str(source)],cwd=ROOT,capture_output=True,text=True)
    (out/'assembler.log').write_text(run.stdout+run.stderr)
    if run.returncode:raise ValueError(run.stdout+run.stderr)
    q=symbols(out/'patch.sym');code=(out/'patch.bin').read_bytes()
    init=q['r_init_end']-q['r_init'];body=q['r_end']-q['r_header']
    if len(code)!=init+body or body>1792:raise ValueError('unexpected RAM/resident code extent')
    rom=bytearray(parent);patches=[]
    def patch(at,old,new):patches.append(apply_patch(rom,at,old,new))
    def ins(op,address):return bytes((op,address&255,address>>8))
    if q['r_init']!=s['pk_resident_end'] or q['r_init_end']>0x7f5f:raise ValueError('initializer left certified obsolete J range')
    at=q['r_init']-16384
    patch(at,parent[at:at+init],code[:init])
    patch(s['pk_init']-16384+3,ins(205,s['qe_init']),ins(205,q['r_init']))
    patch(s['p_fast_header_prepare.rows']-16384,ins(205,s['p_template_header_keys']),ins(195,q['r_header']))
    patch(s['p_fast_igloo_prepare']-16384,parent[s['p_fast_igloo_prepare']-16384:s['p_fast_igloo_prepare']-16384+3],ins(195,q['r_igloo']))
    at=2*16384+s['p_player_variant_lookup']-32768
    patch(at,ins(205,s['p_player_variant_default']),ins(195,q['r_player_lookup']))
    for bank in range(115,150):
        if parent[bank*16384+0x3800:(bank+1)*16384]!=b'\xff'*2048:raise ValueError('region tail is not fully reclaimed')
    at=115*16384+0x3800;patch(at,b'\xff'*body,code[init:])
    data_ranges=[]
    for index in range(len(records)//16):
        bank,address=record_address(index);at=bank*16384+address-32768
        patch(at,b'\xff'*16,records[index*16:index*16+16])
        data_ranges.append((bank,address,16))
    for bank,address,size in inherited['allocations']:
        at=bank*16384+address-32768
        if rom[at:at+size]!=parent[at:at+size]:raise ValueError('region driver changed a live I allocation')
    for name in ('geometry','template-assets'):(out/name).symlink_to((base/name).resolve(),target_is_directory=True)
    name='frostbite-native-regions-r.rom';(out/name).write_bytes(rom)
    for bank in meta['contact14']['arena']:
        b=bank['bank'];bank['packed_sha256']=sha(rom[b*16384:(b+1)*16384])
    (out/'presentation.sym').write_text((base/'presentation.sym').read_text()+'\n'+'\n'.join(f'{n}: EQU 0x{v:08X}' for n,v in q.items() if n.startswith(('r_','rh_','rp_')))+'\n')
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    files=dict(meta['complete_source']['files'])
    for p in (Path(__file__).resolve(),source,ROOT/'scripts/presentation_region_pipeline.py'):
        files[str(p.relative_to(ROOT))]=sha(p.read_bytes())
    meta.update(version='native-regions-r-internal',source_commit=commit,source_dirty=dirty,exploratory=True,source_files=files,
        complete_source=dict(commit=commit,dirty=dirty,files=files,scope='Full reproduced Q plus region builder and hand-written RAM driver.'))
    meta['rom'].update(filename=name,sha256=sha(rom))
    meta['region_pipeline']=dict(parent_rom_sha256=PARENT,patches=patches,ram_cache=[0xe880,0xe900],
        ram_code=[0xe900,0xf000],ram_code_bytes=body,ram_code_bank=115,ram_code_address=0xb800,
        ram_code_sha256=sha(code[init:]),guard=[0xf000,0xf340],reachable_igloo_backgrounds=sorted(reachable),
        inherited_allocation_sha256=COMPANIONS['i_allocation'],all_inherited_allocations_preserved=True,
        igloo_records=len(records)//16,igloo_bytes=len(records),igloo_record_sha256=sha(records),
        scope='Internal RAM-resident fixed header/igloo transactions and exact previous-way lookup; no cadence/human delivery acceptance.')
    (out/'build.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(dict(rom_sha256=sha(rom),ram_code_bytes=body,resident_init_bytes=init,igloo_records=len(records)//16))
    return meta


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-q',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--allocation',type=Path)
    args=parser.parse_args();build(args.base_q.resolve(),args.out.resolve(),allocation=args.allocation)
