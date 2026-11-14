"""Reclaim the obsolete generic NAME decoder, retaining the live publisher."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from build_compact_packet_experiment import digest
from environment import ROOT
from reference_traces import private_output
from render_build import symbols


def build(base,out):
    base=base.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((base/'build.json').read_bytes());parent=(base/m['rom']['filename']).read_bytes()
    if not m.get('compact_dirty_resident') or digest(parent)!=m['rom']['sha256']:raise ValueError('bound resident dirty traversal required')
    if any(digest((ROOT/n).read_bytes())!=h for n,h in m['source_files'].items()):raise ValueError('parent source changed')
    s=symbols(base/'presentation.sym');first,end=s['p_template_decode_names'],s['p_td_roles']
    if (first,end)!=(0x538A,0x5790):raise ValueError('exact retired generic decoder region required')
    target=bytearray(parent);old=parent[first-0x4000:end-0x4000];target[first-0x4000:end-0x4000]=bytes([255])*(end-first)
    node=m['compact_retired_resident'];node['ranges'].append(dict(address=first,size=end-first,before_sha256=digest(old)));node['reclaimed_bytes']+=end-first
    m['compact_retired_names']=dict(parent_rom_sha256=digest(parent),address=first,size=end-first,
        live_NAME_publisher_preserved=[s['p_template_upload_names'],first],requires_physical_read_guard=True,mapperless=False,human_test_candidate=False)
    m['source_files']['scripts/build_compact_name_retirement.py']=digest(Path(__file__).read_bytes())
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
    filename='frostbite-compact-retired-name-decoder-internal.rom';(out/filename).write_bytes(target)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    m.update(source_commit=commit,source_dirty=True,version='compact-retired-name-decoder-internal')
    m['complete_source']=dict(commit=commit,working_tree_dirty=True,files=m['source_files'],scope='Reclaim obsolete generic NAME decoder before native code residency.')
    m['rom'].update(filename=filename,sha256=digest(target));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    print(dict(rom_sha256=digest(target),reclaimed_decoder_bytes=end-first))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.base,a.out)
