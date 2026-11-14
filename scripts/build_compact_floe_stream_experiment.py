"""Stream exact phase0 floe patterns directly from a deduplicated dictionary."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from build_compact_packet_experiment import digest
from compact_live_probe import CONTROL_SHA
from environment import ROOT,verified_tool
from reference_traces import private_output
from render_build import symbols


def build(base,out):
    base=base.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((base/'build.json').read_bytes());parent=(base/m['rom']['filename']).read_bytes()
    if not m.get('compact_temperature') or digest(parent)!=m['rom']['sha256']:raise ValueError('bound temperature integration required')
    if any(digest((ROOT/n).read_bytes())!=h for n,h in m['source_files'].items()):raise ValueError('parent source changed')
    proofroot=ROOT/'outputs/compact/issue44-floe-packet-native-01';proof=json.loads((proofroot/'component-result.json').read_bytes())
    if not proof['complete'] or proof['cases']!=160 or proof['oracle_rom_sha256']!=CONTROL_SHA:raise ValueError('complete packet proof required')
    for n,h in proof['sources'].items():
        if digest((ROOT/n).read_bytes())!=h:raise ValueError('component source changed')
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
    for n in ('directory','counts','indices','patterns'):
        data=(proofroot/(n+'.bin')).read_bytes()
        if digest(data)!=proof['files'][n+'.bin']:raise ValueError('component assets changed')
        (out/('cp-'+n+'.bin')).write_bytes(data)
    s=symbols(base/'presentation.sym')
    asm=[' ORG $A800']
    for n in ('pk_bank','pk_pointer','pk_pending','t_restore_interrupts'):asm.append(f'{n} EQU ${s[n]:04X}')
    asm += [' INCLUDE "compact_floe_stream.asm"',' ASSERT $ <= $A900',' DS $A900-$,$FF']
    for n in ('directory','counts','indices','patterns'):asm += [f'cp_{n}:',f' INCBIN "{out/("cp-"+n+".bin")}"']
    asm += [' ASSERT $ <= $C000',' DS $C000-$,$FF']
    (out/'cs-bank.asm').write_text('\n'.join(asm)+'\n')
    r=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={ROOT/"src"}',f'--raw={out/"cs-bank.bin"}',
        f'--sym={out/"cs-bank.sym"}',str(out/'cs-bank.asm')],capture_output=True,text=True)
    (out/'cs-bank.log').write_text(r.stdout+r.stderr)
    if r.returncode:raise ValueError('assembly failed: '+(r.stdout+r.stderr)[-1200:])
    target=bytearray(parent);patches=[]
    def patch(at,data,reason):
        patches.append(dict(offset=at,size=len(data),before_sha256=digest(parent[at:at+len(data)]),after_sha256=digest(data),reason=reason));target[at:at+len(data)]=data
    at=54*16384+0x2800
    if parent[at:at+6144]!=bytes([255])*6144:raise ValueError('erased replacement allocation required')
    patch(at,(out/'cs-bank.bin').read_bytes(),'deduplicated direct floe stream')
    # The now-native floe acquisition never reads the obsolete20 control pointers.
    gate=s['floe_control_pointers'];old=s['aa_publish']-0x4000
    if parent[old:old+3]!=bytes((0xCD,s['vdp_write']&255,s['vdp_write']>>8)):raise ValueError('unique original PGT upload required')
    patch(gate-0x4000,bytes((0x3E,54,0xCD,s['t_mapper']&255,s['t_mapper']>>8,0xC3,0,0xA8)),'resident retired control-directory bridge')
    patch(old,bytes((0xCD,gate&255,gate>>8)),'phase0 PGT uploader only')
    retired=[]
    for bank in range(35,45):
        for variant in range(16):
            address=0xB800+variant*128
            for a,n in ((address,112),(address+116,12)):
                patch(bank*16384+a-0x8000,bytes([255])*n,'obsolete phase0 pattern/padding bytes')
                retired.append(dict(bank=bank,address=a,size=n,kind='superseded phase0 PGT packet'))
    pools=m['compact_retired_pools'];row=next(r for r in pools['ranges'] if r['bank']==54)
    if row['size']!=0x3800:raise ValueError('exact erased contact prefix required')
    row['size']=0x2800;pools['retired_physical_bytes']-=4096
    graphics=m['compact_retired_graphics'];removed=[r for r in graphics['ranges'] if r['bank']==54]
    if len(removed)!=1 or removed[0]['address']!=0xB800 or removed[0]['size']!=2048:raise ValueError('exact erased NAME tail required')
    graphics['ranges']=[r for r in graphics['ranges'] if r['bank']!=54]+retired
    graphics['retired_physical_bytes']+=19840-2048
    for row in m['contact14']['arena']:
        bank=row['bank'];row['packed_sha256']=digest(target[bank*16384:(bank+1)*16384])
    for n in ('scripts/build_compact_floe_stream_experiment.py','src/compact_floe_stream.asm','scripts/compact_floe_packet_probe.py','src/compact_floe_packet.asm'):
        m['source_files'][n]=digest((ROOT/n).read_bytes())
    m['compact_floe_stream']=dict(parent_rom_sha256=digest(parent),patches=patches,compact_data_bytes=4686,
        owner_metadata_bytes_retained=640,reused_retired_collision_bytes=4096,reused_retired_name_bytes=2048,
        original_vdp_byte_spacing_retained=True,new_ram_bytes=0,mapperless=False,human_test_candidate=False)
    filename='frostbite-compact-floe-stream-internal.rom';(out/filename).write_bytes(target)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    m.update(source_commit=commit,source_dirty=True,version='compact-floe-stream-internal')
    m['complete_source']=dict(commit=commit,working_tree_dirty=True,files=m['source_files'],scope='Dictionary stream experiment; no flat runtime delivered.')
    m['rom'].update(filename=filename,sha256=digest(target));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    print(dict(rom_sha256=digest(target),data_bytes=4686,old_packet_bytes_retired=19840))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.base,a.out)
