"""Share exact16-byte halves of239 left-shore P0 patterns."""
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
    if not m.get('compact_bear_strip') or digest(parent)!=m['rom']['sha256']:raise ValueError('bound compact bear-strip integration required')
    if any(digest((ROOT/n).read_bytes())!=h for n,h in m['source_files'].items()):raise ValueError('parent source changed')
    proofroot=ROOT/'outputs/compact/issue44-shore-pattern-native-01';proof=json.loads((proofroot/'component-result.json').read_bytes())
    if not proof['complete'] or proof['cases']!=239 or proof['oracle_rom_sha256']!=CONTROL_SHA:raise ValueError('complete shore pattern proof required')
    for n,h in proof['sources'].items():
        if digest((ROOT/n).read_bytes())!=h:raise ValueError('component source changed')
    data={n:(proofroot/(n+'.bin')).read_bytes() for n in ('directory','halves')}
    if any(digest(b)!=proof['files'][n+'.bin'] for n,b in data.items()):raise ValueError('component data changed')
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
    for n,b in data.items():(out/('sp-'+n+'.bin')).write_bytes(b)
    def assemble(name,text):
        p=out/(name+'.asm');p.write_text(text)
        r=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={ROOT/"src"}',f'--raw={out/(name+".bin")}',
            f'--sym={out/(name+".sym")}',str(p)],capture_output=True,text=True)
        (out/(name+'.log')).write_text(r.stdout+r.stderr)
        if r.returncode:raise ValueError('assembly failed: '+(r.stdout+r.stderr)[-1200:])
        return (out/(name+'.bin')).read_bytes()
    asm=[' ORG $A800','sp_directory EQU $A900','sp_halves EQU $AD00',' INCLUDE "compact_shore_pattern.asm"',
         ' ASSERT $ <= $A900',' DS $A900-$,$FF',f' INCBIN "{out/"sp-directory.bin"}"',
         ' DS $AD00-$,$FF',f' INCBIN "{out/"sp-halves.bin"}"',' ASSERT $ <= $C000',' DS $C000-$,$FF']
    code=assemble('sp-bank','\n'.join(asm)+'\n');s=symbols(base/'presentation.sym');gate=s['p_template_strip_publish']
    asm=[f' ORG ${gate:04X}',f't_mapper EQU ${s["t_mapper"]:04X}',
         ' PUSH AF',' LD A,58',' CALL t_mapper',' POP AF',' CALL $A800',' LD A,2',' JP t_mapper',f' ASSERT $ <= ${s["p_template_load"]:04X}']
    bridge=assemble('sp-bridge','\n'.join(asm)+'\n');target=bytearray(parent);patches=[]
    def patch(at,b,reason):
        patches.append(dict(offset=at,size=len(b),before_sha256=digest(parent[at:at+len(b)]),after_sha256=digest(b),reason=reason));target[at:at+len(b)]=b
    at=58*16384+0x2800
    if parent[at:at+6144]!=bytes([255])*6144:raise ValueError('erased replacement allocation required')
    patch(at,code,'P0 shore pattern half dictionary and exact32-byte constructor')
    patch(gate-0x4000,bridge,'pattern bridge in retired raw-floe strip publisher')
    at=2*16384+s['ak_try.entry']-0x8000;end=2*16384+s['ak_fallback']-0x8000;region=parent[at:end]
    needle=bytes((0x22,s['p_p_planeaddr']&255,s['p_p_planeaddr']>>8))
    if region.count(needle)!=1:raise ValueError('unique live shore pattern index publication required')
    start=at+region.index(needle)+3
    call=bytes((0xCD,s['ak_copy']&255,s['ak_copy']>>8));tail=parent[start:end]
    if tail[0]!=0x47 or tail.count(call)!=1:raise ValueError('exact original shore pattern copy required')
    size=tail.index(call)+3;resume=0x8000+start%16384+size
    replacement=bytes((0xCD,gate&255,gate>>8,0xC3,resume&255,resume>>8))
    patch(start,replacement+bytes([255])*(size-len(replacement)),'reconstruct current pattern ID; original sprite emit/cache path unchanged')
    remaining=7648
    for b in range(123,127):
        n=min(2048,remaining);patch(b*16384+0x3800,bytes([255])*n,'retired full32-byte P0 shore patterns')
        m['compact_retired_graphics']['ranges'].append(dict(bank=b,address=0xB800,size=n,kind='retired P0 shore full patterns'));remaining-=n
    if remaining:raise ValueError('complete239 pattern retirement required')
    pools=m['compact_retired_pools'];row=next(r for r in pools['ranges'] if r['bank']==58)
    if row['size']!=0x3800:raise ValueError('exact retired prefix required')
    row['size']=0x2800;pools['retired_physical_bytes']-=4096
    graphics=m['compact_retired_graphics'];old=[r for r in graphics['ranges'] if r['bank']==58]
    if len(old)!=1 or old[0]['address']!=0xB800 or old[0]['size']!=2048:raise ValueError('exact retired NAME tail required')
    graphics['ranges']=[r for r in graphics['ranges'] if r['bank']!=58];graphics['retired_physical_bytes']+=7648-2048
    for row in m['contact14']['arena']:
        b=row['bank'];row['packed_sha256']=digest(target[b*16384:(b+1)*16384])
    for n in ('scripts/build_compact_shore_pattern.py','scripts/compact_shore_pattern_probe.py','src/compact_shore_pattern.asm'):
        m['source_files'][n]=digest((ROOT/n).read_bytes())
    m['compact_shore_pattern']=dict(parent_rom_sha256=digest(parent),patches=patches,old_pattern_bytes=7648,
        half_bytes=3712,directory_bytes=956,exact_pattern_cases=239,existing_C500_buffer_only=True,mapperless=False,human_test_candidate=False)
    filename='frostbite-compact-shore-pattern-internal.rom';(out/filename).write_bytes(target)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    m.update(source_commit=commit,source_dirty=True,version='compact-shore-pattern-internal')
    m['complete_source']=dict(commit=commit,working_tree_dirty=True,files=m['source_files'],scope='Exact P0 shore half patterns; full game and cadence proof required.')
    m['rom'].update(filename=filename,sha256=digest(target));(out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    print(dict(rom_sha256=digest(target),data_bytes=4668,retired_pattern_bytes=7648,non_ff_bytes=sum(v!=255 for v in target)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.base,a.out)
