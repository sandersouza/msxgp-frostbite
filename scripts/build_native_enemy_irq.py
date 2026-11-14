"""Protect native SGT address latching against the independently proved IRQ race."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from build_compact_packet_experiment import digest
from build_native_bear_renderer import remove_interval
from environment import ROOT,verified_tool
from reference_traces import private_output
from render_build import symbols


def build(base,proof,out):
    base=base.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((base/'build.json').read_bytes());parent=(base/m['rom']['filename']).read_bytes()
    if not m.get('native_graphic_grammar') or digest(parent)!=m['rom']['sha256']:
        raise ValueError('exact diagnosed graphics integration required')
    p=json.loads((proof/'component-result.json').read_bytes())
    if not p['complete'] or p['cases']!=264 or p['input_rom_sha256']!=m['rom']['sha256']:
        raise ValueError('all source-policy/latch-injection cases required')
    if any(digest((ROOT/n).read_bytes())!=h for n,h in p['sources'].items()):raise ValueError('IRQ-safe source changed')
    out.mkdir(parents=True)
    for f in base.iterdir():
        if f.is_file():shutil.copyfile(f,out/f.name)
        elif f.is_dir():(out/f.name).symlink_to(f.resolve(),target_is_directory=True)
    s=symbols(base/'presentation.sym')
    def assemble(name,text):
        (out/(name+'.asm')).write_text(text)
        r=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={ROOT/"src"}',f'--raw={out/(name+".bin")}',
                          f'--sym={out/(name+".sym")}',str(out/(name+'.asm'))],capture_output=True,text=True)
        (out/(name+'.log')).write_text(r.stdout+r.stderr)
        if r.returncode:raise ValueError('native IRQ-safe assembly failed: '+(r.stdout+r.stderr)[-1200:])
        return (out/(name+'.bin')).read_bytes(),symbols(out/(name+'.sym'))
    source=(base/'sr-code.asm').read_text()
    if source.count('compact_enemy_windows.asm')!=1:raise ValueError('exact original source module required')
    source=source.replace('compact_enemy_windows.asm','native_enemy_windows.asm')
    source=f't_restore_interrupts EQU ${s["t_restore_interrupts"]:04X}\n'+source
    code,q=assemble('ni-code',source)
    if len(code)!=116 or q['sw_upload']!=0xE340 or q['sw_read']!=0xE31B:raise ValueError('four-byte growth and original public entries required')
    loader_source=(base/'sr-loader.asm').read_text()
    if loader_source.count(' LD BC,112\n')!=1:raise ValueError('exact old initializer extent required')
    loader,_=assemble('ni-loader',loader_source.replace(' LD BC,112\n',' LD BC,116\n'))
    target=bytearray(parent)
    if target[64*16384+0x2DF0:64*16384+0x2DF4]!=bytes([255])*4:raise ValueError('unallocated source suffix required')
    target[64*16384+0x2D80:64*16384+0x2D80+len(code)]=code
    target[64*16384+0x3F00:64*16384+0x3F00+len(loader)]=loader
    graph=m['compact_retired_graphics']
    graph['ranges']=remove_interval(graph['ranges'],64,0xADF0,0xADF4)
    graph['retired_physical_bytes']=sum(row['size'] for row in graph['ranges'])
    (out/'sr-code.bin').write_bytes(code)
    for row in m['compact_enemy_ram']['initializers']:
        if row['ram_address']==0xE300:row.update(size=len(code),sha256=digest(code))
    m['native_enemy_irq_fix']=dict(parent_rom_sha256=digest(parent),code_bytes=116,protected_address_latch=True,
       source_policy_restore_after_both_bytes=True,finite_injected_cases=264,source_public_entries_unchanged=True,
       former_unallocated_suffix_bytes_claimed=4,mapperless=False,human_test_candidate=False)
    for row in m['contact14']['arena']:
        bank=row['bank'];row['packed_sha256']=digest(target[bank*16384:(bank+1)*16384])
    for name in ('scripts/build_native_enemy_irq.py','scripts/native_enemy_irq_probe.py','src/native_enemy_windows.asm','scripts/compact_enemy_ram_check.py'):
        m['source_files'][name]=digest((ROOT/name).read_bytes())
    filename='frostbite-native-enemy-irq-internal.rom'
    (out/filename).write_bytes(target);m['rom'].update(filename=filename,sha256=digest(target))
    (out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    print(dict(rom_sha256=digest(target),native_RAM_code_bytes=len(code),public_entrypoints_preserved=True))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('base','proof','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();build(a.base,a.proof,a.out)
