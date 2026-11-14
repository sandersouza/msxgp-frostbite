"""Integrate exact source-mask grammars before the final native RAM takeover."""
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


def build(base,p0proof,floeproof,out):
    base=base.resolve();out=private_output(out)
    if out.exists():raise ValueError('fresh output required')
    m=json.loads((base/'build.json').read_bytes());parent=(base/m['rom']['filename']).read_bytes()
    if digest(parent)!=m['rom']['sha256'] or not m.get('native_name_palette_trial') or not m.get('native_p0_shore_trial'):
        raise ValueError('bound combined size parent required')
    for directory,kind,cases in ((p0proof,'p0',70),(floeproof,'floe-stream',160)):
        p=json.loads((directory/'component-result.json').read_bytes())
        if not p['complete'] or p['kind']!=kind or p['cases']!=cases or p['input_rom_sha256']!=m['rom']['sha256']:
            raise ValueError('all native source-mask cases required')
        if any(digest((ROOT/n).read_bytes())!=h for n,h in p['sources'].items()):raise ValueError('proved native source changed')
    for mode in ('ntsc','pal','bear-ntsc','bear-pal','matrix'):
        p=json.loads((base.parent/mode/'native-bear-renderer-check.json').read_bytes())
        if not p['complete'] or p['rom_sha256']!=m['rom']['sha256']:raise ValueError('all five parent source/whole-game checks required')
    out.mkdir(parents=True)
    for p in base.iterdir():
        if p.is_file():shutil.copyfile(p,out/p.name)
        elif p.is_dir():(out/p.name).symlink_to(p.resolve(),target_is_directory=True)
    s=symbols(base/'presentation.sym');target=bytearray(parent)
    def assemble(name,text):
        (out/(name+'.asm')).write_text(text)
        r=subprocess.run([str(verified_tool('sjasmplus')),'--nologo',f'--inc={ROOT/"src"}',f'--raw={out/(name+".bin")}',
                          f'--sym={out/(name+".sym")}',str(out/(name+'.asm'))],capture_output=True,text=True)
        (out/(name+'.log')).write_text(r.stdout+r.stderr)
        if r.returncode:raise ValueError('native grammar assembly failed: '+(r.stdout+r.stderr)[-1600:])
        return (out/(name+'.bin')).read_bytes(),symbols(out/(name+'.sym'))
    pc=' ORG $A800\nnp0_directory EQU $AB00\nnp0_rows EQU $A900\nnp0_expansion EQU $B300\n INCLUDE "native_p0_pattern.asm"\n ASSERT $ <= $A900\n'
    pcode,pq=assemble('ng-p0',pc)
    expansion=parent[2*16384+0x3300:2*16384+0x3700]
    placements=[(58,0xA800,pcode),(58,0xA900,(p0proof/'rows.bin').read_bytes()),
                (58,0xAB00,(p0proof/'directory.bin').read_bytes()),(58,0xB300,expansion)]
    code=' ORG $A800\n'+''.join(f'{n} EQU ${s[n]:04X}\n' for n in ('pk_pointer','pk_bank','pk_pending','t_restore_interrupts'))
    code+='nf_directory EQU $A900\nnf_indices EQU $AA40\nnf_basis EQU $B1A8\n INCLUDE "native_floe_union_stream.asm"\n ASSERT $ <= $A900\n'
    fcode,fq=assemble('ng-floe',code)
    placements += [(54,0xA800,fcode),(54,0xA900,(floeproof/'directory.bin').read_bytes()),
                   (54,0xAA40,(floeproof/'indices.bin').read_bytes()),(54,0xB1A8,(floeproof/'basis.bin').read_bytes())]
    for bank,address,data in placements:
        at=bank*16384+address-0x8000;target[at:at+len(data)]=data
        m['compact_retired_graphics']['ranges']=remove_interval(m['compact_retired_graphics']['ranges'],bank,address,address+len(data))
    def ram_at(address):return 115*16384+0x3800+address-0xE900
    if parent[ram_at(s['x_try']):ram_at(s['x_try'])+3]!=bytes((0xC3,0xD1,0xEF)):
        raise ValueError('standing-shore entry redirection required')
    target[ram_at(s['x_try']):ram_at(s['x_try'])+3]=bytes((0x3A,0x6B,0xF0))
    start,end=s['x_entry'],s['x_entry.upload']
    region=parent[ram_at(start):ram_at(end)]
    needle=bytes((0x3A,s['p_p_segment']&255,s['p_p_segment']>>8,0x06,149))
    if region.count(needle)!=1:raise ValueError('unique ordinary P0 pool selection required')
    first=start+region.index(needle)
    replacement=needle[:3]+bytes((0xCD,0xD1,0xEF,0xC3,end&255,end>>8))
    target[ram_at(first):ram_at(end)]=replacement+bytes([255])*(end-first-len(replacement))
    gate=' ORG $EFD1\n'+f't_mapper EQU ${s["t_mapper"]:04X}\n'+''' PUSH AF
 LD A,58
 CALL t_mapper
 POP AF
 CALL $A800
 LD A,2
 CALL t_mapper
 RET
 ASSERT $ <= $EFE3
'''
    bridge,_=assemble('ng-p0-gate',gate)
    target[ram_at(0xEFD1):ram_at(0xEFE3)]=bridge+bytes([255])*(18-len(bridge))
    # Old immutable P0 SGTs are now host-only oracle bytes. Keep them for exact
    # independent historical reconstruction, with cold CPU read guards.
    old_sgt=[(149,0xB800,2048),(148,0xBA60,192)]
    for bank,address,size in old_sgt:
        m['compact_retired_graphics']['ranges'].append(dict(bank=bank,address=address,size=size,kind='host-only original P0 SGT grammar oracle; no CPU reader'))
    m['compact_retired_graphics']['retired_physical_bytes']=sum(r['size'] for r in m['compact_retired_graphics']['ranges'])
    fixed=m['fixed_clock'];at=115*16384+0x3800
    fixed['ram_code_sha256']=digest(target[at:at+fixed['ram_code_bytes']])
    for row in m['contact14']['arena']:
        bank=row['bank'];row['packed_sha256']=digest(target[bank*16384:(bank+1)*16384])
    files=('scripts/build_native_graphic_grammar.py','scripts/native_graphic_grammar.py','scripts/native_graphic_grammar_probe.py',
           'src/native_p0_pattern.asm','src/native_floe_union_stream.asm')
    for n in files:m['source_files'][n]=digest((ROOT/n).read_bytes())
    m['native_graphic_grammar']=dict(parent_rom_sha256=digest(parent),native_P0_patterns=70,native_floe_packets=160,
        P0_grammar_bytes=638,floe_basis_bytes=440,original_P0_literal_bytes=2240,original_floe_literal_bytes=2312,
        P0_constructor_bytes=len(pcode),floe_stream_bytes=len(fcode),prototype_only_expansion_ROM_duplicate_bytes=1024,
        no_additional_RAM_or_VRAM=True,old_SGT_host_oracle_CPU_guarded=True,mapperless=False,human_test_candidate=False)
    for n,v in pq.items():
        if n.startswith('np0_'):s[n]=v
    for n,v in fq.items():
        if n.startswith('nf_'):s[n]=v
    filename='frostbite-native-graphic-grammar-internal.rom'
    (out/filename).write_bytes(target);m['rom'].update(filename=filename,sha256=digest(target))
    (out/'presentation.sym').write_text('\n'.join(f'{n}: EQU 0x{v:08X}' for n,v in s.items())+'\n')
    (out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    print(dict(rom_sha256=digest(target),P0_constructor_bytes=len(pcode),floe_stream_bytes=len(fcode),source_representation_bytes_saved=3474))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('base','p0-proof','floe-proof','out'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();build(a.base,a.p0_proof,a.floe_proof,a.out)
