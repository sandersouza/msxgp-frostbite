"""Retire every superseded expanded native-bear representation after replacement."""
import argparse
import json
from pathlib import Path
import shutil

from build_compact_packet_experiment import digest
from render_build import symbols
from reference_traces import private_output
from environment import ROOT


def build(base,out):
    base=base.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((base/'build.json').read_bytes());parent=(base/m['rom']['filename']).read_bytes()
    if not m.get('native_bear_renderer') or digest(parent)!=m['rom']['sha256']:
        raise ValueError('bound native bear replacement required')
    for mode in ('ntsc','pal','bear-ntsc','bear-pal','matrix'):
        p=json.loads((base.parent/mode/'native-bear-renderer-check.json').read_bytes())
        if not p['complete'] or p['rom_sha256']!=m['rom']['sha256']:
            raise ValueError('all five original output proofs required')
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
    target=bytearray(parent);s=symbols(base/'presentation.sym')
    rows=[(56,0xA800,0xC000),(57,0xA800,0xB800),(66,0xB800,0xC000)]
    rows += [(bank,0xB800,0xC000) for bank in (67,68,69)]
    previous=set()
    for row in m['compact_retired_graphics']['ranges']:
        previous.update((row['bank'],a) for a in range(row['address'],row['address']+row['size']))
    newly=set()
    for bank,first,end in rows:
        at=bank*16384+first-0x8000
        target[at:at+end-first]=bytes([255])*(end-first)
        m['compact_retired_graphics']['ranges'].append(dict(bank=bank,address=first,size=end-first,
            kind='superseded native bear directory, records, mask/context dictionary or strip recipes'))
        newly.update((bank,a) for a in range(first,end) if (bank,a) not in previous)
    m['compact_retired_graphics']['retired_physical_bytes']+=len(newly)
    # The new source renderer does not call the old masked-tile/strip bridges.
    resident=[(0x4FE3,0x4FF0),(0x5033,0x5042)]
    for first,end in resident:
        target[first-0x4000:end-0x4000]=bytes([255])*(end-first)
        m['compact_retired_resident']['ranges'].append(dict(address=first,size=end-first,kind='superseded native bear foreign-data bridge'))
    first,end=s['ai_call'],s['ai_ram_end']
    at=115*16384+0x3800+first-0xE900
    target[at:at+end-first]=bytes([255])*(end-first)
    m['native_bear_renderer'].update(expanded_assets_retired=True,retired_upper_helper_address=first,
        retired_upper_helper_bytes=end-first,newly_retired_foreign_allocation_bytes=len(newly),
        retired_resident_bridge_bytes=sum(b-a for a,b in resident))
    fixed=m['fixed_clock'];at=115*16384+0x3800
    fixed['ram_code_sha256']=digest(target[at:at+fixed['ram_code_bytes']])
    for row in m['contact14']['arena']:
        bank=row['bank'];row['packed_sha256']=digest(target[bank*16384:(bank+1)*16384])
    for name in ('scripts/build_native_bear_retirement.py','scripts/native_bear_renderer_check.py'):
        m['source_files'][name]=digest((ROOT/name).read_bytes())
    m['native_bear_retirement']=dict(parent_rom_sha256=digest(parent),newly_retired_foreign_allocation_bytes=len(newly),
        upper_RAM_helpers= dict(address=first,size=end-first),require_cold_CPU_read_guards=True,mapperless=False,human_test_candidate=False)
    filename='frostbite-native-bear-retirement-internal.rom'
    (out/filename).write_bytes(target);m['rom'].update(filename=filename,sha256=digest(target))
    (out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    print(dict(rom_sha256=digest(target),newly_retired_foreign_allocation_bytes=len(newly),retired_upper_helper_bytes=end-first))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.base,a.out)
