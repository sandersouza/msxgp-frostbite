"""Remove obsolete generic actor atlas while retaining current bank7 code."""
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
    if not m.get('compact_floe_stream') or digest(parent)!=m['rom']['sha256']:raise ValueError('bound compact floe stream required')
    if any(digest((ROOT/n).read_bytes())!=h for n,h in m['source_files'].items()):raise ValueError('parent source changed')
    control=ROOT/'outputs/presentation/credit-reference-at/build-final';cm=json.loads((control/'build.json').read_bytes())
    if digest((control/cm['rom']['filename']).read_bytes())!=CONTROL_SHA:raise ValueError('sealed geometry oracle required')
    spans=[]
    for bank in range(3,13):
        if bank==7:spans.extend(((bank,0x8000,0x2000),(bank,0xB800,0x800)))
        elif bank==12:spans.append((bank,0x8000,0x3880))
        else:spans.append((bank,0x8000,16384))
    target=bytearray(parent);retired=[]
    for bank,a,n in spans:
        at=bank*16384+a-0x8000;target[at:at+n]=bytes([255])*n
        retired.append(dict(bank=bank,address=a,size=n,kind='retired generic actor pattern/geometry atlas',before_sha256=digest(parent[at:at+n])))
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
    for row in m['contact14']['arena']:
        b=row['bank'];row['packed_sha256']=digest(target[b*16384:(b+1)*16384])
    packed=m['template_assets'];data=b''.join(target[b*16384:(b+1)*16384] for b in packed['physical_banks']);section=packed['sections']['floe_patterns']
    if digest(data[section['offset']:section['offset']+section['size']])!=packed['floe_patterns_sha256']:raise ValueError('raw-floe namespace changed')
    for b in packed['physical_banks']:packed['files'][f'assets-{b:03d}.bin']=digest(target[b*16384:(b+1)*16384])
    graphics=m['compact_retired_graphics'];graphics['ranges']+=retired
    # Overlapping earlier packet retirements are accounted as a physical union.
    physical=set()
    for row in graphics['ranges']:physical.update(range(row['bank']*16384+row['address']-0x8000,row['bank']*16384+row['address']-0x8000+row['size']))
    graphics['retired_physical_bytes']=len(physical)
    m['compact_retired_templates']=dict(parent_rom_sha256=digest(parent),ranges=retired,
        protected_bank7=[0xA000,0xB800],validation_geometry_oracle_sha256=CONTROL_SHA,
        requires_forbidden_generic_entry_and_physical_read_guards=True,mapperless=False,human_test_candidate=False)
    for n in ('scripts/build_compact_template_retirement.py',):m['source_files'][n]=digest((ROOT/n).read_bytes())
    filename='frostbite-compact-retired-templates-internal.rom';(out/filename).write_bytes(target)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    m.update(source_commit=commit,source_dirty=True,version='compact-retired-templates-internal')
    m['complete_source']=dict(commit=commit,working_tree_dirty=True,files=m['source_files'],scope='Generic atlas retirement with separate immutable expected-geometry oracle.')
    m['rom'].update(filename=filename,sha256=digest(target));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    print(dict(rom_sha256=digest(target),retired_ranges=len(retired),non_ff_bytes=sum(v!=255 for v in target)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.base,a.out)
