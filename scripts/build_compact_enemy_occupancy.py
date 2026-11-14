"""Replace the full enemy occupancy matrix with an exact two-level dictionary."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from build_compact_packet_experiment import digest
from compact_enemy_occupancy_probe import assets
from compact_live_probe import CONTROL_SHA
from environment import ROOT,verified_tool
from reference_traces import private_output
from render_build import symbols


def build(base,out):
    base=base.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((base/'build.json').read_bytes());parent=(base/m['rom']['filename']).read_bytes()
    if not m.get('compact_bear_fast') or digest(parent)!=m['rom']['sha256']:raise ValueError('bound specialized bear stage required')
    if any(digest((ROOT/n).read_bytes())!=h for n,h in m['source_files'].items()):raise ValueError('parent source changed')
    proofroot=ROOT/'outputs/compact/issue44-occupancy-native-01';proof=json.loads((proofroot/'component-result.json').read_bytes())
    if not proof['complete'] or proof['cases']!=8448 or proof['oracle_rom_sha256']!=CONTROL_SHA:raise ValueError('complete8448-case occupancy proof required')
    for n,h in proof['sources'].items():
        if digest((ROOT/n).read_bytes())!=h:raise ValueError('occupancy source changed')
    data,expected=assets(ROOT/'outputs/presentation/credit-reference-at/build-final')
    current=b''.join(parent[b*16384+0x3800:(b+1)*16384] for b in range(142,147))[:8448]
    if current!=expected:raise ValueError('current occupancy table changed')
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
    s=symbols(base/'presentation.sym')
    def assemble(name,text):
        p=out/(name+'.asm');p.write_text(text)
        r=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={ROOT/"src"}',f'--raw={out/(name+".bin")}',str(p)],capture_output=True,text=True)
        (out/(name+'.log')).write_text(r.stdout+r.stderr)
        if r.returncode:raise ValueError('assembly failed: '+(r.stdout+r.stderr)[-1200:])
        return (out/(name+'.bin')).read_bytes()
    for n,b in data.items():(out/('co-'+n+'.bin')).write_bytes(b)
    payload=assemble('co-bank',' ORG $B800\n INCLUDE "compact_enemy_occupancy.asm"\n ASSERT $ <= $B900\n DS $B900-$,$FF\nco_directory:\n'+f' INCBIN "{out/"co-directory.bin"}"\nco_rows:\n INCBIN "{out/"co-rows.bin"}"\n ASSERT $ <= $C000\n')
    rom_at=115*16384+0x3800+s['v_geometry']-0xE900;old=parent[rom_at:rom_at+s['v_geometry_end']-s['v_geometry']]
    tail=bytes((0x78,0xE6,63,0x32,s['v_mask']&255,s['v_mask']>>8))
    if old.count(tail)!=1:raise ValueError('unique original descriptor consumer required')
    stop=old.index(tail)
    gate=assemble('co-gate',f' ORG ${s["v_geometry"]:04X}\n LD A,C\n LD (${s["pfw_geo_variant"]:04X}),A\n LD A,61\n CALL ${s["t_mapper"]:04X}\n CALL $B800\n ASSERT $ <= ${s["v_geometry"]+stop:04X}\n DS ${s["v_geometry"]+stop:04X}-$,0\n')
    target=bytearray(parent);patches=[]
    def patch(at,b,reason):
        patches.append(dict(offset=at,size=len(b),before_sha256=digest(parent[at:at+len(b)]),after_sha256=digest(b),reason=reason));target[at:at+len(b)]=b
    at=61*16384+0x3800
    if parent[at:at+len(payload)]!=bytes([255])*len(payload):raise ValueError('erased prepared NAME tail required')
    patch(at,payload,'52 exact phase rows plus66x8 byte directory; all original coordinates represented')
    patch(rom_at,gate,'unchanged RAM entry/descriptor consumer, compact two-level occupancy lookup')
    graphics=m['compact_retired_graphics'];row=next(r for r in graphics['ranges'] if r['bank']==61 and r['address']==0xB800 and r['size']==2048)
    row['address']+=len(payload);row['size']-=len(payload);graphics['retired_physical_bytes']-=len(payload)
    remaining=8448
    for bank in range(142,147):
        size=min(remaining,2048);remaining-=size
        patch(bank*16384+0x3800,bytes([255])*size,'retired complete original occupancy matrix')
        graphics['ranges'].append(dict(bank=bank,address=0xB800,size=size,kind='retired original occupancy matrix'))
    graphics['retired_physical_bytes']+=8448
    fixed=m['fixed_clock'];at=115*16384+0x3800;fixed['ram_code_sha256']=digest(target[at:at+fixed['ram_code_bytes']])
    for row in m['contact14']['arena']:
        b=row['bank'];row['packed_sha256']=digest(target[b*16384:(b+1)*16384])
    for n in ('scripts/build_compact_enemy_occupancy.py','scripts/compact_enemy_occupancy.py','scripts/compact_enemy_occupancy_probe.py','src/compact_enemy_occupancy.asm','tests/test_compact_enemy_occupancy.py'):
        m['source_files'][n]=digest((ROOT/n).read_bytes())
    m['compact_enemy_occupancy']=dict(parent_rom_sha256=digest(parent),patches=patches,old_matrix_bytes=8448,directory_bytes=528,phase_row_bytes=832,all_group_phase_cases=8448,
        original_geometry_entry_and_consumers_retained=True,scope='All original x/y phases; no reachability restriction or grid24-only shortcut.',mapperless=False,human_test_candidate=False)
    filename='frostbite-compact-enemy-occupancy-internal.rom';(out/filename).write_bytes(target)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();m.update(source_commit=commit,source_dirty=True,version='compact-enemy-occupancy-internal')
    m['complete_source']=dict(commit=commit,working_tree_dirty=True,files=m['source_files'],scope='All-state compact enemy occupancy; whole-frame qualification required.')
    m['rom'].update(filename=filename,sha256=digest(target));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    print(dict(rom_sha256=digest(target),new_dictionary_bytes=1360,payload_bytes=len(payload),old_matrix_bytes=8448))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.base,a.out)
