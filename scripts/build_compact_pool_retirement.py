"""Erase only declared collision pools after all native query replacements exist."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import zlib

from build_compact_packet_experiment import digest
from environment import ROOT
from reference_traces import private_output


def build(base,out):
    base=base.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((base/'build.json').read_bytes());parent=(base/m['rom']['filename']).read_bytes()
    if not m.get('compact_shore_cached') or digest(parent)!=m['rom']['sha256']:raise ValueError('complete bound native query integration required')
    if any(digest((ROOT/n).read_bytes())!=h for n,h in m['source_files'].items()):raise ValueError('source changed')
    codec=m['tables']['codec'];records=codec['record_count'];blocks=codec['block_count']
    record_banks=(records+511)//512;block_banks=(blocks+511)//512
    if codec['record_bank']+record_banks!=codec['block_bank'] or codec['block_bank']+block_banks!=codec['tree_bank']:
        raise ValueError('contiguous original pool layout required')
    spans=[]
    for i in range(record_banks):spans.append((codec['record_bank']+i,0x8000,min(512,records-i*512)*32,'record slots'))
    for i in range(block_banks):spans.append((codec['block_bank']+i,0x8000,min(512,blocks-i*512)*28,'packed uint14 blocks'))
    tree_bytes=m['tables']['used_bytes']-(record_banks+block_banks)*16384
    if not 0<tree_bytes<=(256-codec['tree_bank'])*16384:raise ValueError('bounded original tree required')
    for i in range((tree_bytes+16383)//16384):spans.append((codec['tree_bank']+i,0x8000,min(16384,tree_bytes-i*16384),'pointer tree'))
    allocations=json.loads((ROOT/'outputs/presentation/direct-playfield-i/tables.json').read_bytes())['allocations']
    for bank,address,size in allocations:
        if any(bank==b and address<a+n and a<address+size for b,a,n,kind in spans):raise ValueError('pool retirement intersects inherited noncontact allocation')
    target=bytearray(parent);ranges=[]
    for bank,address,size,kind in spans:
        at=bank*16384+address-0x8000
        if at+size>len(target):raise ValueError('pool exceeds ROM')
        target[at:at+size]=bytes([255])*size
        ranges.append(dict(bank=bank,address=address,size=size,kind=kind,before_sha256=digest(parent[at:at+size])))
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
    for row in m['contact14']['arena']:
        bank=row['bank'];row['packed_sha256']=digest(target[bank*16384:(bank+1)*16384])
    m['source_files']['scripts/build_compact_pool_retirement.py']=digest(Path(__file__).read_bytes())
    m['compact_retired_pools']=dict(parent_rom_sha256=digest(parent),ranges=ranges,
        retired_physical_bytes=sum(n for b,a,n,kind in spans),inherited_allocations_checked=len(allocations),
        original_cold_guards_retained=True,requires_no_decoder_or_retired_read_proof=True,
        mapperless=False,human_test_candidate=False)
    filename='frostbite-compact-retired-pools-internal.rom';(out/filename).write_bytes(target)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    m.update(version='compact-retired-pools-internal',source_commit=commit,source_dirty=True)
    m['complete_source']=dict(commit=commit,working_tree_dirty=True,files=m['source_files'],scope='Pool retirement experiment; cold/read/runtime checks required.')
    m['rom'].update(filename=filename,sha256=digest(target));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    print(dict(rom_sha256=digest(target),retired_physical_bytes=sum(n for b,a,n,kind in spans),
        non_ff_bytes=sum(v!=255 for v in target),host_zlib_bytes=len(zlib.compress(target,9))))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.base,a.out)
