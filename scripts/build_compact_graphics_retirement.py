"""Retire superseded enemy payloads, prepared NAME rows and header dictionary."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import zlib

from build_compact_packet_experiment import digest
from environment import ROOT
from reference_traces import private_output
from render_build import symbols


def build(base,out):
    base=base.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((base/'build.json').read_bytes());parent=(base/m['rom']['filename']).read_bytes()
    if not m.get('compact_header') or not m.get('compact_retired_pools') or digest(parent)!=m['rom']['sha256']:
        raise ValueError('bound native/header integration required')
    if any(digest((ROOT/n).read_bytes())!=h for n,h in m['source_files'].items()):raise ValueError('source changed')
    control=ROOT/'outputs/presentation/credit-reference-at/build-final';cm=json.loads((control/'build.json').read_bytes());cr=(control/cm['rom']['filename']).read_bytes()
    old=(ROOT/'outputs/presentation/direct-playfield-i/build/frostbite-private-direct-playfield-i.rom').read_bytes()
    if digest(old)!=cm['inherited_j']['parent_rom_sha256']:raise ValueError('sealed original packet producer required')
    allocations=json.loads((ROOT/'outputs/presentation/direct-playfield-i/tables.json').read_bytes())['allocations']
    spans=[]
    for bank,address,size in allocations[1:]:
        at=bank*16384+address-0x8000
        if parent[at:at+size]!=old[at:at+size] or cr[at:at+size]!=old[at:at+size]:raise ValueError('old packet payload was repurposed')
        spans.append((bank,address,size,'superseded enemy payload'))
    if sum(n for b,a,n,k in spans)!=18824:raise ValueError('complete old packet payload domain required')
    for bank in range(53,65):spans.append((bank,0xB800,2048,'superseded prepared NAME rows'))
    spans.append((48,0xBA40,0x5C0,'prepared NAME bytes beyond current enemy bootstrap'))
    spans.extend(((116,0xB800,2048,'superseded header pairs'),(117,0xB800,2048,'superseded header pairs'),(118,0xB800,1232,'superseded header singles/specials')))
    for bank,address,size,kind in spans:
        at=bank*16384+address-0x8000
        if parent[at:at+size]!=cr[at:at+size]:raise ValueError('superseded graphics region was repurposed: '+kind)
    s=symbols(base/'presentation.sym');patch=m['compact_packet_experiment']['patches'][0]
    if digest(parent[patch['offset']:patch['offset']+patch['size']])!=patch['after_sha256']:
        raise ValueError('native enemy constructor gate changed')
    target=bytearray(parent);ranges=[]
    for bank,address,size,kind in spans:
        at=bank*16384+address-0x8000;target[at:at+size]=bytes([255])*size
        ranges.append(dict(bank=bank,address=address,size=size,kind=kind,before_sha256=digest(parent[at:at+size])))
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
    for row in m['contact14']['arena']:
        bank=row['bank'];row['packed_sha256']=digest(target[bank*16384:(bank+1)*16384])
    # These physical banks also held retired packet payloads in reclaimed
    # template space. Bind their new bytes without changing the raw-floe oracle.
    packed=m['template_assets']
    asset_data=b''.join(target[b*16384:(b+1)*16384] for b in packed['physical_banks'])
    section=packed['sections']['floe_patterns']
    if digest(asset_data[section['offset']:section['offset']+section['size']])!=packed['floe_patterns_sha256']:
        raise ValueError('independent raw-floe namespace changed')
    for bank in packed['physical_banks']:
        packed['files'][f'assets-{bank:03d}.bin']=digest(target[bank*16384:(bank+1)*16384])
    m['source_files']['scripts/build_compact_graphics_retirement.py']=digest(Path(__file__).read_bytes())
    m['compact_retired_graphics']=dict(parent_rom_sha256=digest(parent),ranges=ranges,
        retired_physical_bytes=sum(n for b,a,n,k in spans),requires_read_and_pixels_proof=True,mapperless=False,human_test_candidate=False)
    filename='frostbite-compact-retired-graphics-internal.rom';(out/filename).write_bytes(target)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    m.update(version='compact-retired-graphics-internal',source_commit=commit,source_dirty=True)
    m['complete_source']=dict(commit=commit,working_tree_dirty=True,files=m['source_files'],scope='Graphics retirement experiment; full physical guards required.')
    m['rom'].update(filename=filename,sha256=digest(target));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    print(dict(rom_sha256=digest(target),retired_graphics_bytes=sum(n for b,a,n,k in spans),non_ff_bytes=sum(v!=255 for v in target),host_zlib_bytes=len(zlib.compress(target,9))))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.base,a.out)
