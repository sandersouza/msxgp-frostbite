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
    if not m.get('compact_shore_complete') or digest(parent)!=m['rom']['sha256']:
        raise ValueError('bound startup-grid integration required')
    if any(digest((ROOT/n).read_bytes())!=h for n,h in m['source_files'].items()):raise ValueError('source changed')
    source=ROOT/'outputs/compact/issue44-shore-program-native-full-01'
    proof=json.loads((source/'component-result.json').read_bytes())
    if not proof['complete'] or not proof['complete_native_horizontal_domain'] or proof['original_sha256']!=m['profile']['source_sha256']:
        raise ValueError('qualified complete shore program required')
    assets={n:(source/(n+'.bin')).read_bytes() for n in ('glyphs','samples','selectors')}
    if any(digest(b)!=proof['files'][n+'.bin'] for n,b in assets.items()):raise ValueError('shore program data changed')
    expected=(source/'expected.bin').read_bytes();native=(source/'actual.bin').read_bytes()
    if digest(expected)!=proof['files']['expected.bin'] or digest(native)!=proof['files']['actual.bin']:raise ValueError('complete native mask corpus changed')
    rejected=0
    for mode in range(6):
        for px in (*range(9),*range(153,160)):
            for bx in range(160):
                body=(bx+(6 if bx<15 else 1))%160
                dx=(px-body)%160;initial=(body-8+14-bx%15)%160
                visible=dx<16 or dx>=153
                clock=body<9 or body>=145
                first=initial<16 or initial>=145
                if not (visible or clock or first):
                    index=(mode*160+px)*160+bx
                    if expected[index*90:(index+1)*90]!=bytes(90) or native[index*92:index*92+90]!=bytes(90):
                        raise ValueError('geometric rejection is not an empty native program')
                    rejected+=1
    if rejected<=10944:raise ValueError('exact rejection domain must include the broad safe range')
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
    asm=[' ORG $B800',' DEFINE WS_INPUT_ORIGIN $3300',' DEFINE WS_OUTPUT_ORIGIN $0E10',
         ' DEFINE WS_SCRATCH_ORIGIN $0FC0',' DEFINE WS_QUERY_TAG $2990',
         ' DEFINE CE_ROW_INPUT_ORIGIN $2970',' DEFINE MP_INPUT_ORIGIN $2990',' DEFINE MP_SCRATCH_ORIGIN $2997',
         'ce_glyphs EQU $0100','ce_bases EQU $0F00',
         'ws_glyphs EQU $BD00','ws_samples EQU $BE00','ws_selectors EQU $BE20',
         ' INCLUDE "compact_shore_program.asm"',' INCLUDE "compact_floe_edge_row.asm"',
         ' INCLUDE "compact_mask_program.asm"',' ASSERT $ <= $BC00',' DS $BC00-$,$FF']
    for n in ('hazard_x','hazard_y'):asm.append(f'{n} EQU ${s[n]:04X}')
    asm += [' INCLUDE "compact_shore_exact_edge_query.asm"',' ASSERT $ <= $BD00']
    for n,a in (('glyphs',0xBD00),('samples',0xBE00),('selectors',0xBE20)):
        asm += [f' DS ${a:04X}-$,$FF',f' INCBIN "{out/("cf-"+n+".bin")}"']
    asm += [' DS $C000-$,$FF'];code=assemble('se-bank','\n'.join(asm)+'\n')
    asm=[' ORG $3690','cf_bear_contact EQU $3600']
    for i,n in enumerate(('cf_control','cf_y','cf_dx','cf_pose','cf_shift','cf_reflection','cf_absolute_x')):asm.append(f'{n} EQU ${0x3300+i:04X}')
    for n in ('t_enabled','hazard_x','hazard_y','hazard_shore_min_y','hazard_lookup'):asm.append(f'{n} EQU ${s[n]:04X}')
    asm += [f'shore_edge_gate EQU ${s["i_shift5"]:04X}',
            ' INCLUDE "compact_shore_fast_common.asm"',' ASSERT $ <= $37C0',' DS $37C0-$,$FF']
    gate=assemble('sf-common','\n'.join(asm)+'\n')
    target=bytearray(parent);patches=[]
    def patch(at,b,reason):
        target[at:at+len(b)]=b
        patches.append(dict(offset=at,size=len(b),before_sha256=digest(parent[at:at+len(b)]),after_sha256=digest(b),reason=reason))
    patch(51*16384+0x3800,code,'fast shore edge program with proven empty-domain rejection')
    patch(46*16384+0x3800+0x690,gate,'expanded visible-only common shore domain with modulo160 distance')
    for n in ('scripts/build_compact_shore_cached_experiment.py','src/compact_shore_program.asm','src/compact_floe_edge_row.asm','src/compact_mask_program.asm','src/compact_shore_edge_query.asm','src/compact_shore_exact_edge_query.asm','src/compact_shore_fast_common.asm','src/compact_shore_cached_edge_query.asm'):
        m['source_files'][n]=digest((ROOT/n).read_bytes())
    for row in m['contact14']['arena']:
        if row['bank'] in (46,51):row['packed_sha256']=digest(target[row['bank']*16384:(row['bank']+1)*16384])
    m['compact_shore_cached']=dict(parent_rom_sha256=digest(parent),patches=patches,
        immutable_ram=[],scratch_ram=[[0x3300,0x3307],[0x0FC0,0x0FE0],[0x2970,0x2999],[0x0E10,0x0E6A]],
        eligibility='common visible-only PX9..152, source-clock edge generator otherwise; cold fallback retained',zero_program_rejection_cases=rejected,repurposed_boot_padding=[[0x0E10,0x0E6A],[0x0FA0,0x0FA4]],cache_key="mode/playerX/bearX/query tag; boot FF mode is invalid",
        original_tables_retained=True,mapperless=False,human_test_candidate=False)
    filename='frostbite-compact-shore-cached-internal.rom';(out/filename).write_bytes(target)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True,cwd=ROOT).strip()
    m.update(source_commit=commit,source_dirty=True,version='compact-shore-cached-internal')
    m['complete_source']=dict(commit=commit,working_tree_dirty=True,files=m['source_files'],scope='Unqualified integration experiment.')
    m['rom'].update(filename=filename,sha256=digest(target))
    (out/'build.json').write_text(json.dumps(m,indent=2)+'\n')
    print(dict(rom_sha256=digest(target),patches=len(patches),human_test_candidate=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();build(a.base,a.out)
