"""Replace all256 temperature programs with two exact glyph bit planes."""
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
    if not m.get('compact_retired_graphics') or digest(parent)!=m['rom']['sha256']:raise ValueError('bound graphics-retirement integration required')
    if any(digest((ROOT/n).read_bytes())!=h for n,h in m['source_files'].items()):raise ValueError('parent source changed')
    proofroot=ROOT/'outputs/compact/issue44-temperature-native-03';proof=json.loads((proofroot/'component-result.json').read_bytes())
    if not proof['complete'] or proof['cases']!=256 or proof['oracle_rom_sha256']!=CONTROL_SHA:raise ValueError('complete temperature proof required')
    for n,h in proof['sources'].items():
        if digest((ROOT/n).read_bytes())!=h:raise ValueError('component source changed')
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
    for n in ('tens','units'):
        data=(proofroot/(n+'.bin')).read_bytes()
        if digest(data)!=proof['files'][n+'.bin']:raise ValueError('component planes changed')
        (out/('ct-'+n+'.bin')).write_bytes(data)
    s=symbols(base/'presentation.sym')
    (out/'symbols.inc').write_text('\n'.join(f'{n} EQU ${v:04X}' for n,v in s.items() if '.' not in n and not n.startswith('burst_'))+'\n')
    source=(ROOT/'src/presentation_temperature_burst.asm').read_text()
    start=source.index('    LD B,A\n    DUP 6\n');end=source.index('    LD HL,hy_tile\n',start)
    source=source[:start]+'    CALL ct_build\n'+source[end:]
    # 131:B800 owns this entire allocation; no added foreign bank calls.
    source+='\nct_tens EQU $BD00\nct_units EQU $BE00\n INCLUDE "compact_temperature.asm"\n ASSERT $ <= $BD00\n DS $BD00-$,$FF\n'
    source+=f' INCBIN "{out/"ct-tens.bin"}"\n INCBIN "{out/"ct-units.bin"}"\n ASSERT $ = $C000\n'
    (out/'ct-body.asm').write_text(source)
    r=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={out}',f'--inc={ROOT/"src"}',
        f'--raw={out/"ct-body.bin"}',f'--sym={out/"ct-body.sym"}',str(out/'ct-body.asm')],capture_output=True,text=True)
    (out/'ct-body.log').write_text(r.stdout+r.stderr)
    if r.returncode:raise ValueError('assembly failed: '+(r.stdout+r.stderr)[-1200:])
    code=(out/'ct-body.bin').read_bytes()
    if len(code)!=2048:raise ValueError('temperature body bank tail required')
    target=bytearray(parent);patches=[]
    for bank,data in [(131,code)]+[(b,bytes([255])*2048) for b in range(127,131)]:
        at=bank*16384+0x3800;target[at:at+2048]=data
        patches.append(dict(offset=at,size=2048,before_sha256=digest(parent[at:at+2048]),after_sha256=digest(data)))
    for bank in range(127,131):m['compact_retired_graphics']['ranges'].append(dict(bank=bank,address=0xB800,size=2048,kind='superseded temperature bursts'))
    m['compact_retired_graphics']['retired_physical_bytes']+=8192
    for row in m['contact14']['arena']:
        bank=row['bank'];row['packed_sha256']=digest(target[bank*16384:(bank+1)*16384])
    for n in ('scripts/build_compact_temperature_experiment.py','src/compact_temperature.asm','scripts/compact_temperature_probe.py'):
        m['source_files'][n]=digest((ROOT/n).read_bytes())
    m['compact_temperature']=dict(parent_rom_sha256=digest(parent),patches=patches,prepared_bytes=8192,plane_bytes=768,
        runtime_record_bytes=32,mapperless=False,human_test_candidate=False)
    filename='frostbite-compact-temperature-internal.rom';(out/filename).write_bytes(target)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    m.update(source_commit=commit,source_dirty=True,version='compact-temperature-internal')
    m['complete_source']=dict(commit=commit,working_tree_dirty=True,files=m['source_files'],scope='Temperature glyph-plane integration; no final flat runtime.')
    m['rom'].update(filename=filename,sha256=digest(target));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    print(dict(rom_sha256=digest(target),prepared_bytes=8192,plane_bytes=768))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.base,a.out)
