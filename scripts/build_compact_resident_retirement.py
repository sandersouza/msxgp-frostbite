"""Reclaim superseded primitive tables and resident contact-pointer arrays."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from build_compact_packet_experiment import digest
from environment import ROOT
from reference_traces import private_output


def build(base,out):
    base=base.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((base/'build.json').read_bytes());parent=(base/m['rom']['filename']).read_bytes()
    if not m.get('compact_shore_pattern') or digest(parent)!=m['rom']['sha256']:raise ValueError('bound compact shore patterns required')
    if any(digest((ROOT/n).read_bytes())!=h for n,h in m['source_files'].items()):raise ValueError('parent source changed')
    target=bytearray(parent)
    # B000..B3FF is the literal original FC00..FFFF page, including the live
    # HUD color selectors at B3F9. Keep it; retire only generic expansion tools.
    retired_bank1=0
    for address,size in ((0x8000,12288),(0xB400,416)):
        at=16384+address-0x8000;old=parent[at:at+size];target[at:at+size]=bytes([255])*size
        m['compact_retired_graphics']['ranges'].append(dict(bank=1,address=address,size=size,kind='retired generic primitive expansion/reverse/clip tables',before_sha256=digest(old)))
        retired_bank1+=size
    m['compact_retired_graphics']['retired_physical_bytes']+=retired_bank1
    first,end=0x7408,0x7900;old=parent[first-0x4000:end-0x4000];target[first-0x4000:end-0x4000]=bytes([255])*(end-first)
    m['compact_retired_resident']=dict(parent_rom_sha256=digest(parent),ranges=[dict(address=first,size=end-first,before_sha256=digest(old))],
        reclaimed_bytes=end-first,preserved_current_floe_stream_bridge=[0x7400,0x7408],preserved_control_map=[0x7300,0x7400],
        preserved_shape_and_bear_maps=[0x7900,0x7A08],requires_cold_physical_read_guard=True,mapperless=False,human_test_candidate=False)
    m['source_files']['scripts/build_compact_resident_retirement.py']=digest(Path(__file__).read_bytes())
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
    (out/'boot.bin').write_bytes(target[16384:32768]);m['background']['boot_sha256']=digest(target[16384:32768])
    filename='frostbite-compact-resident-retirement-internal.rom';(out/filename).write_bytes(target)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    m.update(source_commit=commit,source_dirty=True,version='compact-resident-retirement-internal')
    m['complete_source']=dict(commit=commit,working_tree_dirty=True,files=m['source_files'],scope='Retire superseded primitive prefix and contact-pointer arrays before resident relinking.')
    m['rom'].update(filename=filename,sha256=digest(target));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    print(dict(rom_sha256=digest(target),reclaimed_resident_bytes=end-first,retired_bank1_bytes=retired_bank1,non_ff_bytes=sum(v!=255 for v in target)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.base,a.out)
