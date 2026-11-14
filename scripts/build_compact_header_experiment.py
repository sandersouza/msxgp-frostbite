"""Integrate the qualified interior floe kernel; retain literal boundary fallback."""
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
    if not m.get('compact_retired_pools') or digest(parent)!=m['rom']['sha256']:
        raise ValueError('bound startup-grid integration required')
    if any(digest((ROOT/n).read_bytes())!=h for n,h in m['source_files'].items()):raise ValueError('source changed')
    source=ROOT/'outputs/compact/issue44-header-native-01'
    proof=json.loads((source/'component-result.json').read_bytes())
    if not proof['complete'] or proof['oracle_rom_sha256']!=CONTROL_SHA or proof['sealed_dictionary_cases']!=666:raise ValueError('qualified header constructor required')
    for n,h in proof['sources'].items():
        if digest((ROOT/n).read_bytes())!=h:raise ValueError('header component source changed')
    assets={n:(source/(n+'.bin')).read_bytes() for n in ('fragments','phases')}
    if any(digest(b)!=proof['files'][n+'.bin'] for n,b in assets.items()):raise ValueError('header data changed')
    s=symbols(base/'presentation.sym');out.mkdir(parents=True)
    for p in base.iterdir():
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
    for n,b in assets.items():(out/('cf-'+n+'.bin')).write_bytes(b)
    def assemble(name,text):
        p=out/(name+'.asm');p.write_text(text)
        r=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={ROOT/"src"}',
            f'--raw={out/(name+".bin")}',f'--sym={out/(name+".sym")}',str(p)],capture_output=True,text=True)
        (out/(name+'.log')).write_text(r.stdout+r.stderr)
        if r.returncode:raise ValueError('assembly failed: '+(r.stdout+r.stderr)[-1200:])
        return (out/(name+'.bin')).read_bytes()
    asm=[' ORG $B800','ch_fragments EQU $B900','ch_phases EQU $BE60',
         ' INCLUDE "compact_header.asm"',' ASSERT $ <= $B900']
    for n,a in (('fragments',0xB900),('phases',0xBE60)):
        asm += [f' DS ${a:04X}-$,$FF',f' INCBIN "{out/("cf-"+n+".bin")}"']
    asm += [' DS $C000-$,$FF'];code=assemble('hc-bank','\n'.join(asm)+'\n')
    asm=[f' ORG ${s["hy_lookup"]:04X}']
    for n in ('hy_half','hy_col','pt_glyphs','t_mapper'):asm.append(f'{n} EQU ${s[n]:04X}')
    asm += [' INCLUDE "compact_header_lookup.asm"',f' ASSERT $ <= ${s["hy_lookup_end"]:04X}',f' DS ${s["hy_lookup_end"]:04X}-$,0']
    gate=assemble('hc-lookup','\n'.join(asm)+'\n')
    target=bytearray(parent);patches=[]
    def patch(at,b,reason):
        target[at:at+len(b)]=b
        patches.append(dict(offset=at,size=len(b),before_sha256=digest(parent[at:at+len(b)]),after_sha256=digest(b),reason=reason))
    patch(52*16384+0x3800,code,'compact header fragments and constructor')
    owner=[r for r in m['coherent_x']['auxiliary_code'] if r['ram_address']<=s['hy_lookup']<r['ram_address']+r['size']]
    if len(owner)!=1:raise ValueError('unique copied header lookup owner required')
    row=owner[0];at=row['bank']*16384+row['rom_address']-0x8000+s['hy_lookup']-row['ram_address']
    patch(at,gate,'fragment-based header lookup with original special columns')
    for row in m['coherent_x']['auxiliary_code']:
        at=row['bank']*16384+row['rom_address']-0x8000;row['sha256']=digest(target[at:at+row['size']])
    for n in ('scripts/build_compact_header_experiment.py','src/compact_header.asm','src/compact_header_lookup.asm','scripts/compact_header_probe.py'):
        m['source_files'][n]=digest((ROOT/n).read_bytes())
    for row in m['contact14']['arena']:
        if row['bank'] in (52,146):row['packed_sha256']=digest(target[row['bank']*16384:(row['bank']+1)*16384])
    m['compact_header']=dict(parent_rom_sha256=digest(parent),patches=patches,
        immutable_ram=[],scratch_ram=[[0xC7B0,0xC7B3],[0xC480,0xC488]],
        eligibility='complete existing header upper/lower/special-column lookup',prepared_dictionary_bytes=5328,fragment_bytes=1360,phase_bytes=10,
        original_tables_retained=True,mapperless=False,human_test_candidate=False)
    filename='frostbite-compact-header-internal.rom';(out/filename).write_bytes(target)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True,cwd=ROOT).strip()
    m.update(source_commit=commit,source_dirty=True,version='compact-header-internal')
    m['complete_source']=dict(commit=commit,working_tree_dirty=True,files=m['source_files'],scope='Unqualified integration experiment.')
    m['rom'].update(filename=filename,sha256=digest(target))
    (out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    print(dict(rom_sha256=digest(target),patches=len(patches),human_test_candidate=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.base,a.out)
