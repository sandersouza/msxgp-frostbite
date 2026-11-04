"""Build the original-speed source-clock diagnostic from exact reproduced Q-E."""
import argparse
import json
from pathlib import Path
import subprocess

from environment import ROOT,verified_tool
from presentation_band_spike import apply_patch,sha,verified_bytes,COMPANIONS
from presentation_clock_inventory import inventory,Q_SHA
from render_build import symbols


def build(base_f,chain,out):
    if out.exists():raise ValueError('immutable output already exists')
    base=chain/'q';meta=json.loads((base/'build.json').read_text())
    parent=verified_bytes(base/meta['rom']['filename'],Q_SHA)
    for name,value in meta['complete_source']['files'].items():
        if sha((ROOT/name).read_bytes())!=value:raise ValueError('corresponding Q source changed: '+name)
    inherited=json.loads(verified_bytes(chain/'i/tables.json',COMPANIONS['i_allocation']))
    entries=inventory(base_f,chain,parent)
    s=symbols(base/'presentation.sym');out.mkdir(parents=True)
    (out/'instruction-inventory.json').write_text(json.dumps(entries,indent=2)+'\n')
    (out/'symbols.inc').write_text('\n'.join(f'{n} EQU ${v:04X}' for n,v in sorted(s.items()) if '.'not in n)
        +f'\nt_resident_origin EQU ${s["c14_end"]:04X}\nt_initializer_origin EQU ${s["pk_resident_end"]:04X}\n')
    source=ROOT/'src/presentation_fixed_clock.asm'
    run=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={out}',
        f'--raw={out/"patch.bin"}',f'--sym={out/"patch.sym"}',f'--lst={out/"patch.lst"}',str(source)],cwd=ROOT,capture_output=True,text=True)
    (out/'assembler.log').write_text(run.stdout+run.stderr)
    if run.returncode:raise ValueError(run.stdout+run.stderr)
    q=symbols(out/'patch.sym');code=(out/'patch.bin').read_bytes()
    nr=q['t_resident_end']-q['t_mapper'];ni=q['t_initializer_end']-q['t_initializer'];nb=q['t_ram_end']-q['t_prepare_gate']
    if len(code)!=nr+ni+nb or nb>1792:raise ValueError('unexpected fixed-clock code extent')
    rom=bytearray(parent);patches=[]
    def patch(at,old,new):patches.append(apply_patch(rom,at,old,new))
    def ins(op,address):return bytes((op,address&255,address>>8))
    for record in entries:
        old=bytes.fromhex(record['before'])
        new=ins(205,q['t_mapper']) if record['kind']=='mapper' else bytes.fromhex(record['after'])
        patch(record['offset'],old,new)
    at=q['t_mapper']-16384
    patch(at,bytes(nr),code[:nr])
    if q['t_initializer']!=s['pk_resident_end'] or q['t_initializer_end']>0x7f5f:
        raise ValueError('initializer exceeds certified obsolete J range')
    at=q['t_initializer']-16384
    patch(at,parent[at:at+ni],code[nr:nr+ni])
    patch(s['pk_init']-16384+3,ins(205,s['qe_init']),ins(205,q['t_initializer']))
    at=parent.index(ins(205,s['map_page2']),s['start']-16384,s['start']-16384+20)
    patch(at,ins(205,s['map_page2']),ins(205,q['t_bootstrap']))
    patch(s['presentation_prepare']-16384,bytes([0x3e,1])+ins(205,q['t_mapper']),ins(205,q['t_prepare_gate'])+bytes(2))
    patch(s['vdp_write']-16384,bytes.fromhex('7bd399'),ins(195,q['t_vdp_write']))
    patch(s['pk_fill']-16384,bytes.fromhex('4f7bd3'),ins(195,q['t_fill']))
    patch(s['paced_frame_start']-16384,ins(205,s['diagnostic_selectors']),ins(195,q['t_main']))
    at=115*16384+0x3800
    if parent[at:at+2048]!=b'\xff'*2048:raise ValueError('kernel tail is not reclaimed')
    patch(at,b'\xff'*nb,code[nr+ni:])
    for bank,address,size in inherited['allocations']:
        at=bank*16384+address-32768
        if rom[at:at+size]!=parent[at:at+size]:raise ValueError('fixed clock changed a live I allocation')
    original_at=2*16384+s['original_data']-32768
    original_data=(base_f/'data.bin').read_bytes()
    if (parent[original_at:original_at+len(original_data)]!=original_data
            or rom[original_at:original_at+len(original_data)]!=original_data):raise ValueError('original source data changed')
    (out/'geometry').symlink_to((base/'geometry').resolve(),target_is_directory=True)
    assets=out/'template-assets';assets.mkdir()
    for bank in meta['template_assets']['physical_banks']:
        name=f'assets-{bank:03d}.bin';blob=bytes(rom[bank*16384:(bank+1)*16384])
        (assets/name).write_bytes(blob)
        meta['template_assets']['files'][name]=sha(blob);meta['static_presentation']['files'][name]=sha(blob)
    for record in meta['contact14']['arena']:
        b=record['bank'];record['packed_sha256']=sha(rom[b*16384:(b+1)*16384])
    name='frostbite-fixed-clock-t.rom';(out/name).write_bytes(rom)
    (out/'presentation.sym').write_text((base/'presentation.sym').read_text()+'\n'+'\n'.join(f'{n}: EQU 0x{v:08X}' for n,v in q.items() if n.startswith('t_'))+'\n')
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    files=dict(meta['complete_source']['files'])
    for p in (Path(__file__).resolve(),source,ROOT/'scripts/presentation_clock_inventory.py',ROOT/'scripts/presentation_fixed_clock.py'):
        files[str(p.relative_to(ROOT))]=sha(p.read_bytes())
    meta.update(version='fixed-clock-t-diagnostic',source_commit=commit,source_dirty=dirty,exploratory=True,source_files=files,
        complete_source=dict(commit=commit,working_tree_dirty=dirty,files=files,scope='Reproduced Q plus instruction-provenance relocation and fixed-clock kernel.'))
    meta['rom'].update(filename=name,sha256=sha(rom))
    meta['fixed_clock']=dict(parent_rom_sha256=Q_SHA,patches=patches,mapper_sites=sum(r['kind']=='mapper' for r in entries),
        snapshot_sites=sum(r['kind']=='snapshot' for r in entries),ram_state=[0xe880,0xe900],ram_code=[0xe900,0xf000],
        ram_code_bytes=nb,ram_code_sha256=sha(code[nr+ni:]),snapshot=[0xf000,0xf080],guard=[0xf080,0xf300],stack=[0xf300,0xf380],
        all_inherited_allocations_preserved=True,original_source_data_preserved=True,
        scope='Unqualified diagnostic: original source logic per VBlank with coherent snapshots; independent source/render clock and slot/IRQ proofs required.')
    (out/'build.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(dict(rom_sha256=sha(rom),ram_code_bytes=nb,resident_bytes=nr,initializer_bytes=ni,inventory=len(entries)))
    return meta


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-f',type=Path,required=True);parser.add_argument('--chain',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();build(args.base_f.resolve(),args.chain.resolve(),args.out.resolve())
