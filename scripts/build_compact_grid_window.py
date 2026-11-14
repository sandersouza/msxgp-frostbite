"""Keep fast literal NAME rows while reclaiming1200 lower-RAM bytes."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from build_compact_packet_experiment import digest
from compact_grid_window_probe import assets
from compact_live_probe import CONTROL_SHA
from environment import ROOT,verified_tool
from reference_traces import private_output
from render_build import symbols


def build(base,out):
    base=base.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((base/'build.json').read_bytes());parent=(base/m['rom']['filename']).read_bytes()
    if not m.get('compact_footer_vram') or m.get('compact_grid_palette') or digest(parent)!=m['rom']['sha256']:raise ValueError('bound fast pre-palette base required')
    if any(digest((ROOT/n).read_bytes())!=h for n,h in m['source_files'].items()):raise ValueError('parent source changed')
    proofroot=ROOT/'outputs/compact/issue44-grid-window-native-01';proof=json.loads((proofroot/'component-result.json').read_bytes())
    if not proof['complete'] or proof['cases']!=1280 or proof['oracle_rom_sha256']!=CONTROL_SHA:raise ValueError('all1280 literal rows required')
    for n,h in proof['sources'].items():
        if digest((ROOT/n).read_bytes())!=h:raise ValueError('literal-row producer changed')
    data,_,_=assets(ROOT/'outputs/presentation/credit-reference-at/build-final');s=symbols(base/'presentation.sym');out.mkdir(parents=True)
    for p in base.iterdir():
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
    def assemble(name,text):
        p=out/(name+'.asm');p.write_text(text)
        r=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={ROOT/"src"}',f'--raw={out/(name+".bin")}',f'--sym={out/(name+".sym")}',str(p)],capture_output=True,text=True)
        (out/(name+'.log')).write_text(r.stdout+r.stderr)
        if r.returncode:raise ValueError('assembly failed: '+(r.stdout+r.stderr)[-1300:])
        return (out/(name+'.bin')).read_bytes()
    pointers=b''.join((0x1100+int.from_bytes(data['offsets'][i:i+2],'little')).to_bytes(2,'little') for i in range(0,352,2))
    initializers=[]
    for name,address,blob in (('directory',0x1000,data['directory']),('pool',0x1100,data['pool']),('pointers',0x2100,pointers)):
        filename='gw-'+name+'.bin';(out/filename).write_bytes(blob);initializers.append(dict(file=filename,ram_address=address,size=len(blob),sha256=digest(blob)))
    gate=[f' ORG ${s["i_shifts"]:04X}']
    for n in ('p_tl_delta_index','p_tl_root','PAGE','p_w_row','t_mapper','x_name_row','t_enabled'):gate.append(f'{n} EQU ${s[n]:04X}')
    gate+=[' PUSH DE',' LD A,(p_tl_delta_index)']+[' RLCA']*4
    gate+=[' LD B,A',' LD A,(p_tl_root)',' AND 15',' OR B',' LD ($C7F0),A',' LD A,(PAGE)',' ADD A,A',' ADD A,A',
           ' LD B,A',' LD A,(p_w_row)',' ADD A,B',' LD ($C7F1),A',' LD A,(t_enabled)',' OR A',' JR Z,gw_cold',
           ' DEFINE GW_INLINE','gw_directory EQU $1000','gw_index EQU $2100',' INCLUDE "compact_grid_window.asm"',' POP DE',' JP x_name_row',
           'gw_cold:',' LD A,45',' CALL t_mapper',' LD A,($C7F0)',' LD L,A',' LD H,$BD',' LD A,(HL)',
           ' LD ($C7F0),A',' CALL $B800',' POP DE',' LD HL,$C480',' JP x_name_row',' ASSERT $ <= $7C51']
    gate=assemble('gw-gate','\n'.join(gate)+'\n')
    reclaimed=[dict(address=0x20F0,size=16),dict(address=0x2260,size=1184)]
    loader=[' ORG $BF00']
    for row in reclaimed:
        start=row['address'];size=row['size']
        loader += [f' LD HL,${start:04X}',f' LD DE,${start+1:04X}',f' LD BC,{size-1}',' LD (HL),$A5',' LDIR']
    for source,dest,size in ((0xB980,0x1000,160),(0xA800,0x1100,4080),(0xB800,0x2100,352)):
        loader += [f' LD HL,${source:04X}',f' LD DE,${dest:04X}',f' LD BC,{size}',' LDIR']
    loader+=[' RET',' ASSERT $ <= $C000'];loader=assemble('gw-loader','\n'.join(loader)+'\n')
    target=bytearray(parent);patches=[]
    def patch(at,b,reason):
        patches.append(dict(offset=at,size=len(b),before_sha256=digest(parent[at:at+len(b)]),after_sha256=digest(b),reason=reason));target[at:at+len(b)]=b
    allocations=((0xA800,data['pool']),(0xB800,pointers),(0xB980,data['directory']),(0xBF00,loader))
    for address,blob in allocations:
        at=63*16384+address-0x8000
        if parent[at:at+len(blob)]!=bytes([255])*len(blob):raise ValueError('erased cold-grid source bank required')
        patch(at,blob,'startup-only exact literal NAME pool/directory/preloader')
    old=bytes((0x3E,45,0xCD,s['t_mapper']&255,s['t_mapper']>>8,0xCD,0,0xBF));at=0x7C51-0x4000
    if parent[at:at+len(old)]!=old:raise ValueError('exact current lower-grid bootstrap entry required')
    patch(at+1,bytes((63,)),'bootstrap selects the new literal-window source bank')
    patch(s['i_shifts']-0x4000,gate,'literal pointer lookup keeps the original row copier and cold constructor')
    pools=m['compact_retired_pools'];row=next(r for r in pools['ranges'] if r['bank']==63)
    if row['size']!=0x3800:raise ValueError('exact retired prefix required')
    row['size']=0x2800;pools['retired_physical_bytes']-=4096
    graphics=m['compact_retired_graphics'];oldrow=next(r for r in graphics['ranges'] if r['bank']==63 and r['address']==0xB800 and r['size']==2048)
    graphics['ranges'].remove(oldrow);graphics['retired_physical_bytes']-=2048
    for first,last in ((0xB7F0,0xB800),(0xB960,0xB980),(0xBA20,0xBF00),(0xBF00+len(loader),0xC000)):
        graphics['ranges'].append(dict(bank=63,address=first,size=last-first,kind='unused cold literal-grid source gaps'))
        graphics['retired_physical_bytes']+=last-first
    for row in m['contact14']['arena']:
        b=row['bank'];row['packed_sha256']=digest(target[b*16384:(b+1)*16384])
    for n in ('scripts/build_compact_grid_window.py','scripts/compact_grid_window_probe.py','src/compact_grid_window.asm'):
        m['source_files'][n]=digest((ROOT/n).read_bytes())
    m['compact_grid_window']=dict(parent_rom_sha256=digest(parent),patches=patches,initializers=initializers,reclaimed_ranges=reclaimed,
        old_expanded_rows_bytes=5632,literal_pool_bytes=4080,pointer_bytes=352,reclaimed_lower_RAM_bytes=1200,
        cold_constructor_retained=True,white_atlas_unchanged=True,phase_owner_cases=1280,legacy_row_copier_unchanged=True,
        source_pools_are_startup_only=True,mapperless=False,human_test_candidate=False)
    m['compact_grid_experiment']['representation_replaced_by']='compact_grid_window: exact4592-byte immutable phase/pointer/pool allocation; old expanded fields are ancestry only'
    filename='frostbite-compact-grid-window-internal.rom';(out/filename).write_bytes(target)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();m.update(source_commit=commit,source_dirty=True,version='compact-grid-window-internal')
    m['complete_source']=dict(commit=commit,working_tree_dirty=True,files=m['source_files'],scope='Literal overlapping prepared NAME windows, unchanged row copier; new preload/retirement and whole-frame gates required.')
    m['rom'].update(filename=filename,sha256=digest(target));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    print(dict(rom_sha256=digest(target),reclaimed_lower_RAM_bytes=1200,gate_bytes=len(gate),loader_bytes=len(loader)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.base,a.out)
