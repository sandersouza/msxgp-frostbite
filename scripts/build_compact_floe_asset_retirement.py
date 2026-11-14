"""Relocate live owner keys; retire superseded mask/template/NAME tables."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from build_compact_packet_experiment import digest
from compact_live_probe import CONTROL_SHA
from environment import ROOT
from reference_traces import private_output


def build(base,out):
    base=base.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((base/'build.json').read_bytes());parent=(base/m['rom']['filename']).read_bytes()
    if not m.get('compact_retired_templates') or digest(parent)!=m['rom']['sha256']:raise ValueError('bound generic-atlas retirement required')
    if any(digest((ROOT/n).read_bytes())!=h for n,h in m['source_files'].items()):raise ValueError('parent source changed')
    target=bytearray(parent);keys=bytearray();owners=[]
    for bank in range(35,45):
        for variant in range(16):
            at=bank*16384+0x3800+variant*128+112;lo,hi,b,count=parent[at:at+4]
            source=b*16384+lo+256*hi-0x8000
            if not 1<=count<=8 or not 0x8000<=lo+256*hi<lo+256*hi+count*2<=0xC000:raise ValueError('bounded live owner keys required')
            dest=0xB800+len(keys);keys.extend(parent[source:source+count*2])
            target[at:at+4]=dest.to_bytes(2,'little')+bytes((55,count));owners.append(dict(offset=at,count=count))
    if len(keys)!=1894:raise ValueError('complete947-key domain required')
    key_at=55*16384+0x3800
    if parent[key_at:key_at+2048]!=bytes([255])*2048:raise ValueError('erased replacement key tail required')
    target[key_at:key_at+2048]=keys+bytes([255])*(2048-len(keys))
    # The generic templates and their decoded programs are no longer read.
    # Keep both the logical raw-ID domain and its exact sealed host oracle.
    # The original fixed decoder still reads the name-pair table at logical
    # 218112 (255:9400); the rejected first retirement proved it is live.
    start,end=167552,218112;packed=m['template_assets'];retired=[];pos=start
    while pos<end:
        logical,offset=divmod(pos,16384);bank=packed['physical_banks'][logical];size=min(end-pos,16384-offset)
        at=bank*16384+offset;target[at:at+size]=bytes([255])*size
        retired.append(dict(bank=bank,address=0x8000+offset,size=size,kind='superseded floe masks/template keys/NAME programs',before_sha256=digest(parent[at:at+size])));pos+=size
    graphics=m['compact_retired_graphics'];removed=[r for r in graphics['ranges'] if r['bank']==55]
    if len(removed)!=1 or removed[0]['address']!=0xB800 or removed[0]['size']!=2048:raise ValueError('exact old NAME tail required')
    graphics['ranges']=[r for r in graphics['ranges'] if r['bank']!=55]+retired
    physical=set()
    for row in graphics['ranges']:physical.update(range(row['bank']*16384+row['address']-0x8000,row['bank']*16384+row['address']-0x8000+row['size']))
    graphics['retired_physical_bytes']=len(physical)
    old_floe_sha=packed['floe_patterns_sha256'];data=b''.join(target[b*16384:(b+1)*16384] for b in packed['physical_banks']);section=packed['sections']['floe_patterns']
    packed['floe_patterns_sha256']=digest(data[section['offset']:section['offset']+section['size']])
    for b in packed['physical_banks']:packed['files'][f'assets-{b:03d}.bin']=digest(target[b*16384:(b+1)*16384])
    for row in m['contact14']['arena']:
        b=row['bank'];row['packed_sha256']=digest(target[b*16384:(b+1)*16384])
    m['compact_retired_floe_assets']=dict(parent_rom_sha256=digest(parent),ranges=retired,
        original_floe_patterns_sha256=old_floe_sha,validation_raw_floe_oracle_sha256=CONTROL_SHA,
        relocated_key_bytes=len(keys),relocated_key_sha256=digest(keys),owner_pointer_records=owners,
        logical_raw_id_domain_unchanged=True,mapperless=False,human_test_candidate=False)
    m['source_files']['scripts/build_compact_floe_asset_retirement.py']=digest(Path(__file__).read_bytes())
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
    filename='frostbite-compact-retired-floe-assets-internal.rom';(out/filename).write_bytes(target)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    m.update(source_commit=commit,source_dirty=True,version='compact-retired-floe-assets-internal')
    m['complete_source']=dict(commit=commit,working_tree_dirty=True,files=m['source_files'],scope='Owner-key relocation and prepared-table retirement; explicit sealed host oracles.')
    m['rom'].update(filename=filename,sha256=digest(target));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    print(dict(rom_sha256=digest(target),key_bytes=len(keys),removed_asset_bytes=end-start,non_ff_bytes=sum(v!=255 for v in target)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.base,a.out)
