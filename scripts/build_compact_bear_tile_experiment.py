"""Replace prepared bear final tiles with literal masks and exact row merge."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from build_compact_packet_experiment import digest
from compact_bear_tile_probe import assets
from compact_live_probe import CONTROL_SHA
from environment import ROOT,verified_tool
from reference_traces import private_output
from render_build import symbols


def build(base,out):
    base=base.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((base/'build.json').read_bytes());parent=(base/m['rom']['filename']).read_bytes()
    if not m.get('compact_retired_floe_assets') or digest(parent)!=m['rom']['sha256']:raise ValueError('bound compact floe-asset integration required')
    if any(digest((ROOT/n).read_bytes())!=h for n,h in m['source_files'].items()):raise ValueError('parent source changed')
    proofroot=ROOT/'outputs/compact/issue44-bear-tile-native-02';proof=json.loads((proofroot/'component-result.json').read_bytes())
    if not proof['complete'] or proof['cases']!=4230 or proof['oracle_rom_sha256']!=CONTROL_SHA:raise ValueError('complete bear context proof required')
    for n,h in proof['sources'].items():
        if digest((ROOT/n).read_bytes())!=h:raise ValueError('component source changed')
    control=ROOT/'outputs/presentation/credit-reference-at/build-final';data,_,_,codes=assets(control)
    for n,b in data.items():
        if digest(b)!=proof['files'][n+'.bin']:raise ValueError('component data changed')
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
    for n,b in data.items():(out/('cb-'+n+'.bin')).write_bytes(b)
    s=symbols(base/'presentation.sym')
    asm=[' ORG $A800',' INCLUDE "compact_bear_tile.asm"',' ASSERT $ <= $A900',' DS $A900-$,$FF','cb_patterns:',
         f' INCBIN "{out/"cb-patterns.bin"}"','cb_contexts:',f' INCBIN "{out/"cb-contexts.bin"}"',' ASSERT $ <= $C000',' DS $C000-$,$FF']
    (out/'cb-bank.asm').write_text('\n'.join(asm)+'\n')
    r=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={ROOT/"src"}',f'--raw={out/"cb-bank.bin"}',
        f'--sym={out/"cb-bank.sym"}',str(out/'cb-bank.asm')],capture_output=True,text=True)
    (out/'cb-bank.log').write_text(r.stdout+r.stderr)
    if r.returncode:raise ValueError('assembly failed: '+(r.stdout+r.stderr)[-1200:])
    target=bytearray(parent);patches=[]
    def patch(at,b,reason):
        patches.append(dict(offset=at,size=len(b),before_sha256=digest(parent[at:at+len(b)]),after_sha256=digest(b),reason=reason));target[at:at+len(b)]=b
    at=56*16384+0x2800
    if parent[at:at+6144]!=bytes([255])*6144:raise ValueError('erased replacement bank tail required')
    patch(at,(out/'cb-bank.bin').read_bytes(),'literal bear masks and nine certified contexts')
    gate=s['p_template_half'];bridge=bytes((0x3E,56,0xCD,s['t_mapper']&255,s['t_mapper']>>8,0xCD,0,0xA8,0x3E,102,0xC3,s['t_mapper']&255,s['t_mapper']>>8))
    if gate+len(bridge)>s['p_template_address']:raise ValueError('retired generic-half entry too small')
    patch(gate-0x4000,bridge,'resident bridge in retired generic-half decoder')
    first=102*16384+s['ai_tile.miss']-0x8000;region=parent[first:first+80]
    needle=bytes((0xCD,s['ai_copy']&255,s['ai_copy']>>8));calls=region.count(needle)
    if calls!=1 or region[0]!=0xD1:raise ValueError('exact prepared native bear tile-copy call required')
    size=region.index(needle)+3;resume=s['ai_tile.miss']+size
    jump=bytes((0xD1,0xCD,gate&255,gate>>8,0xC3,resume&255,resume>>8))
    patch(first,jump+bytes([255])*(size-len(jump)),'construct exact native bear tile, then original upload/cache publication')
    changed_cells=0
    for i in range(m['bear_native']['records']):
        bank=67+i//8;at=bank*16384+0x3800+(i%8)*256;record=bytearray(parent[at:at+256])
        for cell in range(record[240]*record[241]):
            n=int.from_bytes(record[cell*20:cell*20+2],'little')
            for context in range(9):
                p=cell*20+2+context*2;old=int.from_bytes(record[p:p+2],'little')
                record[p:p+2]=(codes[(n,context)]|(old&0x8000)).to_bytes(2,'little')
            changed_cells+=1
        patch(at,record,'native bear records retain logical IDs and clip skips; context words now select literal masks')
    retired=[]
    for bank in range(79,102):
        patch(bank*16384+0x3800,bytes([255])*2048,'retired prepared bear final-tile pool')
        retired.append(dict(bank=bank,address=0xB800,size=2048,kind='retired bear final tiles'))
    pools=m['compact_retired_pools'];row=next(r for r in pools['ranges'] if r['bank']==56)
    if row['size']!=0x3800:raise ValueError('exact erased prefix required')
    row['size']=0x2800;pools['retired_physical_bytes']-=4096
    graphics=m['compact_retired_graphics'];old=[r for r in graphics['ranges'] if r['bank']==56]
    if len(old)!=1 or old[0]['address']!=0xB800 or old[0]['size']!=2048:raise ValueError('exact retired NAME allocation required')
    graphics['ranges']=[r for r in graphics['ranges'] if r['bank']!=56]+retired
    physical=set()
    for row in graphics['ranges']:physical.update(range(row['bank']*16384+row['address']-0x8000,row['bank']*16384+row['address']-0x8000+row['size']))
    graphics['retired_physical_bytes']=len(physical)
    for row in m['contact14']['arena']:
        b=row['bank'];row['packed_sha256']=digest(target[b*16384:(b+1)*16384])
    for n in ('scripts/build_compact_bear_tile_experiment.py','scripts/compact_bear_tile_probe.py','src/compact_bear_tile.asm'):
        m['source_files'][n]=digest((ROOT/n).read_bytes())
    m['compact_bear_tile']=dict(parent_rom_sha256=digest(parent),patches=patches,mask_bytes=3760,context_bytes=288,
        replaced_final_tile_bytes=45760,records=m['bear_native']['records'],changed_cells=changed_cells,
        source_keys_and_clip_skips_retained=True,new_ram_bytes=0,mapperless=False,human_test_candidate=False)
    filename='frostbite-compact-bear-tile-internal.rom';(out/filename).write_bytes(target)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    m.update(source_commit=commit,source_dirty=True,version='compact-bear-tile-internal')
    m['complete_source']=dict(commit=commit,working_tree_dirty=True,files=m['source_files'],scope='Literal-mask native bear tile integration; full game/cadence proof required.')
    m['rom'].update(filename=filename,sha256=digest(target));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    print(dict(rom_sha256=digest(target),data_bytes=4048,changed_cells=changed_cells,non_ff_bytes=sum(v!=255 for v in target)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.base,a.out)
